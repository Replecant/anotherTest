package com.replecant.retrocosmos.dinosaur;

import java.util.List;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.phys.Vec3;

/** Anything sneaking up behind or beside the tyrant gets swatted by a swing of that tail. */
public class TyrannosaurusTailSweepGoal extends Goal {
    private static final double RANGE = 6.0;
    private static final int DURATION = 14;
    private static final int HIT_AT = 7;
    private static final float DAMAGE = 8.0F;

    private final Tyrannosaurus rex;
    private int ticks;

    public TyrannosaurusTailSweepGoal(Tyrannosaurus rex) {
        this.rex = rex;
    }

    private List<LivingEntity> victims() {
        Vec3 facing = Vec3.directionFromRotation(0.0F, rex.getYRot());
        return rex.level().getEntitiesOfClass(LivingEntity.class, rex.getBoundingBox().inflate(RANGE, 1.0, RANGE), e -> {
            if (e == rex || e instanceof Tyrannosaurus || !e.isAlive() || e.isSpectator()
                    || e instanceof net.minecraft.world.entity.player.Player p && p.isCreative()) {
                return false;
            }
            Vec3 to = e.position().subtract(rex.position()).multiply(1.0, 0.0, 1.0);
            return to.lengthSqr() < RANGE * RANGE && to.normalize().dot(facing) < 0.2;  // behind or beside
        });
    }

    @Override
    public boolean canUse() {
        return rex.sweepCooldown <= 0 && rex.getTarget() != null && rex.getRandom().nextInt(10) == 0 && !victims().isEmpty();
    }

    @Override
    public boolean canContinueToUse() {
        return ticks < DURATION;
    }

    @Override
    public void start() {
        ticks = 0;
        rex.setSweeping(true);
        rex.playSound(SoundEvents.PLAYER_ATTACK_SWEEP, 2.0F, 0.5F);
    }

    @Override
    public void stop() {
        rex.setSweeping(false);
        rex.sweepCooldown = 100;
    }

    @Override
    public boolean requiresUpdateEveryTick() {
        return true;
    }

    @Override
    public void tick() {
        ticks++;
        if (ticks == HIT_AT && rex.level() instanceof ServerLevel level) {
            for (LivingEntity victim : victims()) {
                if (victim.hurtServer(level, level.damageSources().mobAttack(rex), DAMAGE)) {
                    Vec3 away = victim.position().subtract(rex.position()).multiply(1.0, 0.0, 1.0).normalize();
                    victim.knockback(1.6, -away.x, -away.z);
                    victim.hurtMarked = true;
                }
            }
            rex.playSound(SoundEvents.PLAYER_ATTACK_KNOCKBACK, 2.0F, 0.5F);
        }
    }
}
