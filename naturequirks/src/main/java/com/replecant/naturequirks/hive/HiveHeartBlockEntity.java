package com.replecant.naturequirks.hive;

import com.replecant.naturequirks.NatureQuirks;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;

/**
 * The Hive Heart's block entity. Loaded hearts are indexed per dimension, so {@link #alarm} finds the hearts near a
 * disturbance cheaply. A heart answers at most once per {@link #COOLDOWN} ticks with up to {@link #WAVE} guardian
 * bees ({@code naturequirks:guardian_bee}, looked up in the entity registry at runtime) and never keeps more than
 * {@link #MAX_GUARDS} of them alive within {@link #GUARD_RADIUS} blocks. A guardian is made with the entity class's
 * static {@code spawn(ServerLevel, BlockPos)} when it has one, else spawned like a summoned mob; either way it is set
 * on the intruder.
 */
public class HiveHeartBlockEntity extends BlockEntity {
    public static final Identifier GUARDIAN = Identifier.fromNamespaceAndPath(NatureQuirks.MODID, "guardian_bee");
    /** How close to a heart a broken hive block or a struck bee must be to raise the alarm. */
    public static final int RADIUS = 16;
    public static final int MAX_GUARDS = 6, WAVE = 2, COOLDOWN = 40, GUARD_RADIUS = 32;
    private static final Map<ResourceKey<Level>, Set<BlockPos>> LOADED = new ConcurrentHashMap<>();
    /** Alarms answered and guardians spawned since the game started (diagnostics). */
    public static int alarms, spawned;

    private long nextWave;

    public HiveHeartBlockEntity(BlockPos pos, BlockState state) {
        super(ModHive.HIVE_HEART_BE.get(), pos, state);
    }

    @Override
    public void onLoad() {
        super.onLoad();
        if (level != null && !level.isClientSide()) {
            LOADED.computeIfAbsent(level.dimension(), k -> ConcurrentHashMap.newKeySet()).add(worldPosition.immutable());
        }
    }

    @Override
    public void setRemoved() {
        super.setRemoved();
        if (level != null && !level.isClientSide()) {
            Set<BlockPos> set = LOADED.get(level.dimension());
            if (set != null) {
                set.remove(worldPosition);
            }
        }
    }

    /** The loaded hearts within {@code radius} blocks of {@code pos}, nearest first. */
    public static List<BlockPos> heartsNear(ServerLevel level, BlockPos pos, int radius) {
        List<BlockPos> out = new ArrayList<>();
        for (BlockPos p : LOADED.getOrDefault(level.dimension(), Set.of())) {
            if (p.distSqr(pos) <= (double) radius * radius) {
                out.add(p);
            }
        }
        out.sort((a, b) -> Double.compare(a.distSqr(pos), b.distSqr(pos)));
        return out;
    }

    /**
     * Something disturbed the hive at {@code pos} (a hive block broken, a bee struck): every heart within
     * {@link #RADIUS} sends guardians at {@code intruder}. Returns the number of guardian bees spawned.
     */
    public static int alarm(ServerLevel level, BlockPos pos, @Nullable LivingEntity intruder) {
        int n = 0;
        for (BlockPos heart : heartsNear(level, pos, RADIUS)) {
            if (level.getBlockEntity(heart) instanceof HiveHeartBlockEntity be) {
                n += be.summon(level, intruder);
            }
        }
        return n;
    }

    /** Sends a wave of guardians from this heart (cooldown and cap permitting); returns how many came out. */
    public int summon(ServerLevel level, @Nullable LivingEntity intruder) {
        long now = level.getGameTime();
        if (now < nextWave) {
            return 0;
        }
        nextWave = now + COOLDOWN;
        alarms++;
        level.playSound(null, worldPosition, SoundEvents.BEEHIVE_WORK, SoundSource.BLOCKS, 1.0F, 0.6F);
        level.sendParticles(ParticleTypes.WAX_OFF, worldPosition.getX() + 0.5, worldPosition.getY() + 0.5, worldPosition.getZ() + 0.5,
                12, 0.6, 0.6, 0.6, 0.05);
        Optional<EntityType<?>> type = BuiltInRegistries.ENTITY_TYPE.getOptional(GUARDIAN);
        if (type.isEmpty()) {
            NatureQuirks.LOGGER.debug("Hive Heart at {}: no {} registered, no guardians", worldPosition, GUARDIAN);
            return 0;
        }
        EntityType<?> guardian = type.get();
        int alive = level.getEntitiesOfClass(Entity.class, new AABB(worldPosition).inflate(GUARD_RADIUS),
                e -> e.getType() == guardian && e.isAlive()).size();
        int n = Math.min(WAVE, MAX_GUARDS - alive);
        int made = 0;
        for (int i = 0; i < n; i++) {
            BlockPos at = freeSpot(level);
            Entity e = spawnGuardian(level, guardian, at);
            if (e != null) {
                made++;
                if (intruder != null && e instanceof Mob mob) {
                    mob.setTarget(intruder);
                }
            }
        }
        spawned += made;
        return made;
    }

    private BlockPos freeSpot(ServerLevel level) {
        for (int i = 0; i < 12; i++) {
            BlockPos p = worldPosition.offset(level.getRandom().nextInt(5) - 2, level.getRandom().nextInt(3),
                    level.getRandom().nextInt(5) - 2);
            if (level.getBlockState(p).isAir() && level.getBlockState(p.above()).isAir()) {
                return p;
            }
        }
        return worldPosition.above();
    }

    @Nullable
    private static Entity spawnGuardian(ServerLevel level, EntityType<?> type, BlockPos at) {
        Entity sample = type.create(level, EntitySpawnReason.MOB_SUMMONED);
        if (sample == null) {
            return null;
        }
        try {
            Method spawn = sample.getClass().getMethod("spawn", ServerLevel.class, BlockPos.class);
            if (Modifier.isStatic(spawn.getModifiers())) {
                Object made = spawn.invoke(null, level, at);
                sample.discard();
                if (made instanceof Entity e) {
                    return e;
                }
                List<Entity> near = level.getEntitiesOfClass(Entity.class, new AABB(at).inflate(2), e -> e.getType() == type);
                return near.isEmpty() ? null : near.get(0);
            }
        } catch (NoSuchMethodException ignored) {
            // no factory: spawn the plain entity below
        } catch (ReflectiveOperationException | RuntimeException e) {
            NatureQuirks.LOGGER.warn("Hive Heart: {}.spawn failed", type, e);
        }
        sample.snapTo(at.getX() + 0.5, at.getY(), at.getZ() + 0.5, level.getRandom().nextFloat() * 360.0F, 0.0F);
        if (sample instanceof Mob mob) {
            mob.finalizeSpawn(level, level.getCurrentDifficultyAt(at), EntitySpawnReason.MOB_SUMMONED, null);
        }
        return level.addFreshEntity(sample) ? sample : null;
    }
}
