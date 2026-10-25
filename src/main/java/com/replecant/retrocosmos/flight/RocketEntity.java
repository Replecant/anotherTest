package com.replecant.retrocosmos.flight;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.block.RocketBlock;
import com.replecant.retrocosmos.block.RocketPart;
import com.replecant.retrocosmos.launch.LaunchSite;
import com.replecant.retrocosmos.registry.ModAttachments;
import com.replecant.retrocosmos.registry.ModBlocks;
import com.replecant.retrocosmos.registry.ModEntities;
import com.replecant.retrocosmos.registry.ModItems;
import com.replecant.retrocosmos.station.FreedomStation;
import java.util.List;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityDimensions;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.portal.TeleportTransition;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;

/**
 * The Liberty I in flight. While the rocket stands on the pad it is made of blocks; on launch the blocks are
 * swapped for this entity, which carries the crew up to orbit, waits there while they look at the system map,
 * and brings them back down onto the same pad.
 */
public class RocketEntity extends Entity {
    /** Crew aboard on the pad, T-minus countdown running. */
    public static final int PHASE_PAD = 0;
    public static final int PHASE_ASCENT = 1;
    public static final int PHASE_ORBIT = 2;
    public static final int PHASE_DESCENT = 3;
    /** Touched down; the crew climbs out on the next tick (once clients know the phase) and the rocket turns back into blocks. */
    public static final int PHASE_LANDED = 4;
    /** Leaving orbit for another destination: the crew is moved to the target dimension on the next tick. */
    public static final int PHASE_TRANSFER = 5;

    public static final String HOMESTEAD = "homestead";
    public static final String FREEDOM_STATION = "freedom_station";

    public static final int PAD_COUNTDOWN = 10 * 20;
    /** Height above the world's build limit at which the rocket is considered to be in orbit. */
    public static final int ORBIT_ABOVE_MAX = 120;
    public static final double MAX_ASCENT_SPEED = 2.0;
    /** Cabin height (blocks above the engine block) where the crew sits. */
    private static final double CABIN_Y = 5.15;

    private static final EntityDataAccessor<Integer> PHASE = SynchedEntityData.defineId(RocketEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> PHASE_TICKS = SynchedEntityData.defineId(RocketEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> PAD_Y = SynchedEntityData.defineId(RocketEntity.class, EntityDataSerializers.INT);

    private BlockPos padBase = BlockPos.ZERO;
    private String destination = "";

    public RocketEntity(EntityType<? extends RocketEntity> type, Level level) {
        super(type, level);
        this.noPhysics = true;
        setNoGravity(true);
    }

    /**
     * Swaps the rocket blocks standing at {@code base} for a flying rocket and boards the given crew.
     *
     * @param countdown true to start on the pad with a T-10 countdown, false to lift off immediately
     */
    public static RocketEntity launchFrom(ServerLevel level, BlockPos base, List<? extends Player> crew, boolean countdown) {
        for (int i = RocketPart.HEIGHT - 1; i >= 0; i--) {
            level.setBlock(base.above(i), Blocks.AIR.defaultBlockState(), Block.UPDATE_ALL | Block.UPDATE_SUPPRESS_DROPS);
        }
        RocketEntity rocket = new RocketEntity(ModEntities.ROCKET.get(), level);
        rocket.padBase = base.immutable();
        rocket.entityData.set(PAD_Y, base.getY());
        rocket.setPos(base.getX() + 0.5, base.getY(), base.getZ() + 0.5);
        rocket.setPhase(countdown ? PHASE_PAD : PHASE_ASCENT);
        level.addFreshEntity(rocket);
        for (Player player : crew) {
            player.startRiding(rocket, true, true);
            if (level.dimension() == Level.OVERWORLD) {
                player.setData(ModAttachments.HOME_PAD, new HomePad(base.immutable(), true));
            }
        }
        if (!countdown) {
            rocket.onLiftoff(level);
        }
        return rocket;
    }

    // ------------------------------------------------------------------ data

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        builder.define(PHASE, PHASE_PAD);
        builder.define(PHASE_TICKS, 0);
        builder.define(PAD_Y, 0);
    }

    public int phase() {
        return entityData.get(PHASE);
    }

    public int phaseTicks() {
        return entityData.get(PHASE_TICKS);
    }

    public int padY() {
        return entityData.get(PAD_Y);
    }

    private void setPhase(int phase) {
        entityData.set(PHASE, phase);
        entityData.set(PHASE_TICKS, 0);
    }

    /** Fraction of propellant left, for the flight HUD: the ascent burns 80 %, the landing burn the rest. */
    public float propellant() {
        int maxY = level().getMaxY() + ORBIT_ABOVE_MAX;
        double alt = Math.max(0, getY() - padY());
        double span = Math.max(1, maxY - padY());
        return switch (phase()) {
            case PHASE_PAD -> 1.0F;
            case PHASE_ASCENT -> (float) (1.0 - 0.8 * Math.min(1, alt / span));
            case PHASE_ORBIT -> 0.2F;
            case PHASE_LANDED -> 0.0F;
            case PHASE_TRANSFER -> 0.2F;
            default -> (float) (0.2 * Math.min(1, alt / span));
        };
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        entityData.set(PHASE, input.getIntOr("phase", PHASE_DESCENT));
        entityData.set(PHASE_TICKS, input.getIntOr("phase_ticks", 0));
        destination = input.getStringOr("destination", "");
        padBase = new BlockPos(input.getIntOr("pad_x", (int) Math.floor(getX())), input.getIntOr("pad_y", 64),
                input.getIntOr("pad_z", (int) Math.floor(getZ())));
        entityData.set(PAD_Y, padBase.getY());
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        output.putInt("phase", phase());
        output.putInt("phase_ticks", phaseTicks());
        output.putString("destination", destination);
        output.putInt("pad_x", padBase.getX());
        output.putInt("pad_y", padBase.getY());
        output.putInt("pad_z", padBase.getZ());
    }

    // ------------------------------------------------------------------ behaviour

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        return false;
    }

    @Override
    public boolean isPickable() {
        return false;
    }

    @Override
    public boolean isPushable() {
        return false;
    }

    @Override
    protected boolean canAddPassenger(Entity passenger) {
        return getPassengers().size() < 2;
    }

    @Override
    protected Vec3 getPassengerAttachmentPoint(Entity passenger, EntityDimensions dimensions, float scale) {
        int index = getPassengers().indexOf(passenger);
        return new Vec3(index == 1 ? 0.3 : 0.0, CABIN_Y, 0.0);
    }

    @Override
    public Vec3 getDismountLocationForPassenger(LivingEntity passenger) {
        // step off onto the pad, next to the rocket
        return new Vec3(padBase.getX() + 0.5 + 1.6, padBase.getY(), padBase.getZ() + 0.5);
    }

    /** Whether the crew may leave right now (only while still on the pad). */
    public boolean canDisembark() {
        return phase() == PHASE_PAD || phase() == PHASE_LANDED || phase() == PHASE_TRANSFER;
    }

    @Override
    protected void removePassenger(Entity passenger) {
        super.removePassenger(passenger);
        if (!level().isClientSide() && phase() == PHASE_PAD && getPassengers().isEmpty() && !isRemoved()) {
            // crew climbed out during the countdown: scrub and put the rocket back on the pad
            if (level() instanceof ServerLevel level) {
                restoreOnPad(level, RocketBlock.MAX_FUEL, RocketBlock.MAX_FUEL);
                broadcast(level, Component.translatable("message.retrocosmos.flight.scrubbed").withStyle(ChatFormatting.RED));
            }
        }
    }

    @Override
    public void tick() {
        super.tick();
        int ticks = phaseTicks() + 1;
        entityData.set(PHASE_TICKS, ticks);
        if (!(level() instanceof ServerLevel level)) {
            return;
        }
        switch (phase()) {
            case PHASE_PAD -> tickPad(level, ticks);
            case PHASE_ASCENT -> tickAscent(level, ticks);
            case PHASE_ORBIT -> tickOrbit(level, ticks);
            case PHASE_DESCENT -> tickDescent(level, ticks);
            case PHASE_LANDED -> land(level);
            case PHASE_TRANSFER -> transfer(level);
            default -> setPhase(PHASE_DESCENT);
        }
    }

    private void tickPad(ServerLevel level, int ticks) {
        int left = PAD_COUNTDOWN - ticks;
        if (left % 20 == 0) {
            int seconds = left / 20;
            if (seconds > 0) {
                broadcast(level, Component.translatable("message.retrocosmos.console.t_minus", seconds).withStyle(ChatFormatting.YELLOW));
                level.playSound(null, blockPosition(), SoundEvents.NOTE_BLOCK_PLING.value(), SoundSource.BLOCKS, 1.0F, seconds <= 3 ? 1.8F : 1.2F);
            } else {
                setPhase(PHASE_ASCENT);
                onLiftoff(level);
                return;
            }
        }
        if (left <= 60) {
            level.sendParticles(ParticleTypes.FLAME, getX(), getY() + 0.1, getZ(), 6, 0.25, 0.05, 0.25, 0.03);
            level.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), getY() + 0.1, getZ(), 8, 1.0, 0.1, 1.0, 0.02);
        }
    }

    private void onLiftoff(ServerLevel level) {
        broadcast(level, Component.translatable("message.retrocosmos.console.liftoff").withStyle(ChatFormatting.GREEN, ChatFormatting.BOLD));
        level.playSound(null, blockPosition(), SoundEvents.FIREWORK_ROCKET_LAUNCH, SoundSource.BLOCKS, 3.0F, 0.5F);
        level.playSound(null, blockPosition(), SoundEvents.GENERIC_EXPLODE.value(), SoundSource.BLOCKS, 2.0F, 0.6F);
        level.sendParticles(ParticleTypes.CAMPFIRE_SIGNAL_SMOKE, getX(), getY() + 0.3, getZ(), 80, 1.8, 0.3, 1.8, 0.03);
        level.sendParticles(ParticleTypes.FLAME, getX(), getY(), getZ(), 120, 0.6, 0.2, 0.6, 0.15);
        for (Entity passenger : getPassengers()) {
            if (passenger instanceof ServerPlayer player) {
                LaunchSite.award(player, "stage1/countdown", "liftoff");
                LaunchSite.award(player, "stage2/root", "liftoff");
            }
        }
    }

    private void tickAscent(ServerLevel level, int ticks) {
        double speed = Math.min(MAX_ASCENT_SPEED, 0.04 + ticks * ticks * 0.00004);
        move(speed);
        exhaust(level, speed, ticks);
        if (getY() >= level.getMaxY() + ORBIT_ABOVE_MAX) {
            setPhase(PHASE_ORBIT);
            setDeltaMovement(Vec3.ZERO);
            for (Entity passenger : getPassengers()) {
                if (passenger instanceof ServerPlayer player) {
                    player.displayClientMessage(Component.translatable("message.retrocosmos.flight.orbit").withStyle(ChatFormatting.AQUA, ChatFormatting.BOLD), false);
                    LaunchSite.award(player, "stage2/orbit", "orbit");
                }
            }
        }
    }

    private void tickOrbit(ServerLevel level, int ticks) {
        setDeltaMovement(Vec3.ZERO);
        // an uncrewed rocket comes straight back
        if (getPassengers().isEmpty() && ticks > 60) {
            beginDescent();
        }
    }

    /** The body this rocket is currently orbiting. */
    public String currentBody() {
        if (FreedomStation.isStation(level())) {
            return FREEDOM_STATION;
        }
        return level().dimension() == Level.OVERWORLD ? HOMESTEAD : "";
    }

    /** Called when the crew picks a destination on the system map. */
    public void travelTo(String target) {
        if (phase() != PHASE_ORBIT || !(target.equals(HOMESTEAD) || target.equals(FREEDOM_STATION))) {
            return;
        }
        if (target.equals(currentBody())) {
            beginDescent();
        } else {
            destination = target;
            setPhase(PHASE_TRANSFER);
        }
    }

    private void transfer(ServerLevel level) {
        if (phaseTicks() < 2) {
            return; // let clients learn about the phase first, so they accept the dismount
        }
        MinecraftServer server = level.getServer();
        List<ServerPlayer> crew = getPassengers().stream().filter(e -> e instanceof ServerPlayer).map(e -> (ServerPlayer) e).toList();
        ServerLevel target;
        BlockPos pad;
        if (destination.equals(FREEDOM_STATION)) {
            target = FreedomStation.level(server);
            FreedomStation.Layout layout = target == null ? null : FreedomStation.ensureBuilt(target);
            pad = layout == null ? null : layout.padBase();
        } else {
            target = server.overworld();
            HomePad home = crew.isEmpty() ? HomePad.UNKNOWN : crew.get(0).getData(ModAttachments.HOME_PAD);
            pad = home.known() ? home.pos() : target.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, BlockPos.ZERO);
        }
        if (target == null || pad == null) {
            RetroCosmos.LOGGER.error("Retro Cosmos: destination {} unavailable", destination);
            broadcast(level, Component.translatable("message.retrocosmos.flight.no_trajectory").withStyle(ChatFormatting.RED));
            setPhase(PHASE_ORBIT);
            return;
        }
        RocketEntity rocket = new RocketEntity(ModEntities.ROCKET.get(), target);
        rocket.padBase = pad.immutable();
        rocket.entityData.set(PAD_Y, pad.getY());
        rocket.setPos(pad.getX() + 0.5, target.getMaxY() + ORBIT_ABOVE_MAX, pad.getZ() + 0.5);
        rocket.setPhase(PHASE_DESCENT);

        ejectPassengers();
        for (ServerPlayer player : crew) {
            player.teleport(new TeleportTransition(target, new Vec3(rocket.getX(), rocket.getY() + CABIN_Y, rocket.getZ()), Vec3.ZERO,
                    player.getYRot(), player.getXRot(), TeleportTransition.DO_NOTHING));
        }
        target.addFreshEntity(rocket);
        for (ServerPlayer player : crew) {
            player.startRiding(rocket, true, true);
            player.displayClientMessage(Component.translatable(destination.equals(FREEDOM_STATION)
                    ? "message.retrocosmos.flight.approach_station" : "message.retrocosmos.flight.deorbit").withStyle(ChatFormatting.GOLD), false);
        }
        discard();
    }

    /** Called when the crew picks "Return home" on the system map. */
    public void beginDescent() {
        if (phase() == PHASE_ORBIT) {
            setPhase(PHASE_DESCENT);
            broadcast(level(), Component.translatable("message.retrocosmos.flight.deorbit").withStyle(ChatFormatting.GOLD));
        }
    }

    private void tickDescent(ServerLevel level, int ticks) {
        double height = getY() - padBase.getY();
        double speed = Math.max(0.12, Math.min(MAX_ASCENT_SPEED, height * 0.025));
        if (height <= speed) {
            setPos(getX(), padBase.getY(), getZ());
            setDeltaMovement(Vec3.ZERO);
            setPhase(PHASE_LANDED);
            return;
        }
        move(-speed);
        if (height < 48) {
            exhaust(level, speed * 0.5, ticks);
        }
    }

    private void move(double dy) {
        setDeltaMovement(0, dy, 0);
        setPos(getX(), getY() + dy, getZ());
    }

    private void exhaust(ServerLevel level, double speed, int ticks) {
        double y = getY() - 0.2;
        level.sendParticles(ParticleTypes.FLAME, getX(), y, getZ(), 6, 0.2, 0.3, 0.2, 0.04);
        level.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), y - 0.5, getZ(), 4, 0.4, 0.6, 0.4, 0.02);
        if (getY() - padY() < 12) {
            level.sendParticles(ParticleTypes.CAMPFIRE_COSY_SMOKE, getX(), padY() + 0.2, getZ(), 6, 1.5, 0.1, 1.5, 0.03);
        }
        if (ticks % 12 == 0) {
            level.playSound(null, getX(), getY(), getZ(), SoundEvents.FIRECHARGE_USE, SoundSource.BLOCKS, 2.5F, 0.4F + (float) speed * 0.1F);
        }
    }

    private void land(ServerLevel level) {
        level.playSound(null, padBase, SoundEvents.ANVIL_LAND, SoundSource.BLOCKS, 0.6F, 0.6F);
        level.sendParticles(ParticleTypes.CAMPFIRE_COSY_SMOKE, getX(), padBase.getY() + 0.2, getZ(), 40, 1.5, 0.1, 1.5, 0.03);
        List<Entity> crew = List.copyOf(getPassengers());
        for (Entity passenger : crew) {
            if (passenger instanceof ServerPlayer player) {
                player.displayClientMessage(Component.translatable("message.retrocosmos.flight.landed").withStyle(ChatFormatting.GREEN, ChatFormatting.BOLD), false);
                LaunchSite.award(player, "stage2/splashdown", "landed");
                if (FreedomStation.isStation(level)) {
                    player.displayClientMessage(Component.translatable("message.retrocosmos.flight.docked").withStyle(ChatFormatting.AQUA), false);
                    LaunchSite.award(player, "stage2/freedom_station", "docked");
                }
            }
        }
        restoreOnPad(level, 0, 0);
    }

    /** Puts the rocket back as blocks on its pad (or drops it as an item if the pad is obstructed) and removes the entity. */
    private void restoreOnPad(ServerLevel level, int fuel, int oxidizer) {
        ejectPassengers();
        boolean free = true;
        for (int i = 0; i < RocketPart.HEIGHT; i++) {
            if (!level.getBlockState(padBase.above(i)).canBeReplaced()) {
                free = false;
                break;
            }
        }
        if (free) {
            BlockState state = ModBlocks.ROCKET.get().defaultBlockState().setValue(RocketBlock.FUEL, fuel).setValue(RocketBlock.OXIDIZER, oxidizer);
            for (int i = 0; i < RocketPart.HEIGHT; i++) {
                level.setBlock(padBase.above(i), state.setValue(RocketBlock.PART, RocketPart.byOffset(i)), Block.UPDATE_ALL);
            }
        } else {
            RetroCosmos.LOGGER.info("Retro Cosmos: landing site at {} obstructed, dropping the rocket as an item", padBase);
            spawnAtLocation(level, new ItemStack(ModItems.ROCKET.get()));
        }
        discard();
    }

    private void broadcast(Level level, Component message) {
        for (Player player : level.players()) {
            if (player.distanceToSqr(this) < 64 * 64 || player.getVehicle() == this) {
                player.displayClientMessage(message, false);
            }
        }
    }
}
