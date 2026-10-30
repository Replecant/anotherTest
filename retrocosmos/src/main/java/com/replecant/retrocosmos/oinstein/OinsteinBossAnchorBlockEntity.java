package com.replecant.retrocosmos.oinstein;

import com.replecant.retrocosmos.tribe.ModTribes;
import com.replecant.retrocosmos.tribe.boss.OinsteinBoss;
import com.replecant.retrocosmos.tribe.boss.OinsteinStrider;
import java.util.UUID;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.core.UUIDUtil;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.Difficulty;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;

/**
 * State of an Oinstein boss arena. NBT: {@code Defeated} (boolean; once true the boss never comes back) and
 * {@code Boss} (UUID of whichever phase is alive now). Once a second it checks: not defeated, no boss alive, a
 * survival/adventure player within {@link #TRIGGER_RANGE} - then the Atomic Strider steps out at the anchor at full
 * health. A boss whose UUID is stored but who cannot be found for 10 s (unloaded, /kill-ed, despawned) is forgotten.
 */
public class OinsteinBossAnchorBlockEntity extends BlockEntity {
    public static final double TRIGGER_RANGE = 20.0;
    private static final int MISSING_LIMIT = 200;

    private boolean defeated;
    @Nullable
    private UUID boss;
    private int missing;

    public OinsteinBossAnchorBlockEntity(BlockPos pos, BlockState state) {
        super(ModTribes.OINSTEIN_BOSS_ANCHOR_BE.get(), pos, state);
    }

    /** Has Dr. Oinstein been beaten here? */
    public boolean isDefeated() {
        return defeated;
    }

    @Nullable
    public UUID bossId() {
        return boss;
    }

    /** The phase now alive (set on spawn and on each phase change). */
    public void setBoss(@Nullable UUID id) {
        boss = id;
        missing = 0;
        setChanged();
    }

    /** Homo Novus is dead: this arena is done for good. */
    public void markDefeated() {
        defeated = true;
        boss = null;
        setChanged();
    }

    /** The encounter reset (everyone left): forget the boss; the strider comes back when a player does. */
    public void reset() {
        boss = null;
        missing = 0;
        setChanged();
    }

    /** Clears the defeated flag too (for commands/tests): the arena is fresh. */
    public void rearm() {
        defeated = false;
        reset();
    }

    public void serverTick(Level level) {
        if (defeated || !(level instanceof ServerLevel server) || (level.getGameTime() + worldPosition.asLong()) % 20 != 0) {
            return;
        }
        if (boss != null) {
            if (findBoss(server) != null) {
                missing = 0;
                return;
            }
            missing += 20;
            if (missing < MISSING_LIMIT) {
                return;
            }
            boss = null;
            missing = 0;
            setChanged();
        }
        if (level.getDifficulty() == Difficulty.PEACEFUL || !playerNear(server)) {
            return;
        }
        trySpawn(server);
    }

    /** Brings phase one out now, if this arena is armed and no boss is about. The ticker calls it when a player is near. */
    @Nullable
    public OinsteinStrider trySpawn(ServerLevel level) {
        if (defeated || boss != null) {
            return null;
        }
        OinsteinStrider strider = OinsteinStrider.spawnAt(level, worldPosition);
        if (strider != null) {
            setBoss(strider.getUUID());
        }
        return strider;
    }

    private boolean playerNear(ServerLevel level) {
        double cx = worldPosition.getX() + 0.5, cy = worldPosition.getY() + 0.5, cz = worldPosition.getZ() + 0.5;
        for (ServerPlayer p : level.players()) {
            if (p.isAlive() && !p.isSpectator() && !p.isCreative() && p.distanceToSqr(cx, cy, cz) < TRIGGER_RANGE * TRIGGER_RANGE) {
                return true;
            }
        }
        return false;
    }

    @Nullable
    public OinsteinBoss findBoss(ServerLevel level) {
        if (boss == null) {
            return null;
        }
        UUID id = boss;
        var found = level.getEntitiesOfClass(OinsteinBoss.class, new AABB(worldPosition).inflate(OinsteinBoss.LEASH_HARD + 24.0),
                b -> b.getUUID().equals(id) && !b.isRemoved());
        return found.isEmpty() ? null : found.get(0);
    }

    @Override
    protected void loadAdditional(ValueInput input) {
        super.loadAdditional(input);
        defeated = input.getBooleanOr("Defeated", false);
        boss = input.read("Boss", UUIDUtil.CODEC).orElse(null);
    }

    @Override
    protected void saveAdditional(ValueOutput output) {
        super.saveAdditional(output);
        output.putBoolean("Defeated", defeated);
        if (boss != null) {
            output.store("Boss", UUIDUtil.CODEC, boss);
        }
    }
}
