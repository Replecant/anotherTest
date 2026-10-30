package com.replecant.retrocosmos.dinosaur;

import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ambient.AmbientCreature;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;

/**
 * Small ambient fliers of Venus (meganeura, spore moth): harmless background life that flies bat-style, steering
 * toward a wandering waypoint the subclass picks. Never lands, never takes fall damage, can't be pushed.
 */
public abstract class VenusFlier extends AmbientCreature implements DinosaurAnimated {
    @Nullable
    protected BlockPos waypoint;

    protected VenusFlier(EntityType<? extends VenusFlier> type, Level level) {
        super(type, level);
        setNoGravity(true);
    }

    /** Next place to fly to, or null to keep the current one. */
    @Nullable
    protected abstract BlockPos nextWaypoint();

    /** How strongly it steers (higher = darting) and its top speed. */
    protected abstract double agility();

    protected abstract double topSpeed();

    /** Ground (top of solid ground, leaves ignored) under a column. */
    protected int groundAt(int x, int z) {
        return level().getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z);
    }

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (waypoint != null && (!level.isEmptyBlock(waypoint) || waypoint.getY() <= level.getMinY())) {
            waypoint = null;
        }
        if (waypoint == null || waypoint.closerToCenterThan(position(), 1.5)) {
            waypoint = nextWaypoint();
        }
        if (waypoint == null) {
            setDeltaMovement(getDeltaMovement().scale(0.8));
            return;
        }
        double dx = waypoint.getX() + 0.5 - getX();
        double dy = waypoint.getY() + 0.5 - getY();
        double dz = waypoint.getZ() + 0.5 - getZ();
        double len = Math.max(0.01, Math.sqrt(dx * dx + dy * dy + dz * dz));
        double k = agility();
        double top = topSpeed();
        Vec3 v = getDeltaMovement();
        setDeltaMovement(v.add((dx / len * top - v.x) * k, (dy / len * top - v.y) * k, (dz / len * top - v.z) * k));
        float yaw = (float) (Mth.atan2(getDeltaMovement().z, getDeltaMovement().x) * Mth.RAD_TO_DEG) - 90.0F;
        setYRot(getYRot() + Mth.wrapDegrees(yaw - getYRot()) * 0.6F);
        yBodyRot = getYRot();
        zza = 0.5F;
    }

    @Override
    public boolean isPushable() {
        return false;
    }

    @Override
    protected void doPush(Entity entity) {
    }

    @Override
    protected void pushEntities() {
    }

    @Override
    public boolean causeFallDamage(double distance, float multiplier, DamageSource source) {
        return false;
    }

    @Override
    public boolean isIgnoringBlockTriggers() {
        return true;
    }

    @Override
    public int getMaxSpawnClusterSize() {
        return 5;
    }
}
