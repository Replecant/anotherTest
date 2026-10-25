package com.replecant.retrocosmos.npc;

import java.util.EnumSet;
import java.util.List;
import javax.annotation.Nullable;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.util.DefaultRandomPos;
import net.minecraft.world.phys.Vec3;

/** Scientists run from raptors and monsters - toward the nearest guard if there is one, otherwise just away. */
public class CrewFleeGoal extends Goal {
    private static final double SCARE_RANGE = 10.0;
    private static final double SAFE_RANGE = 16.0;

    private final ExpeditionMember member;
    @Nullable
    private LivingEntity threat;
    private int repath;

    public CrewFleeGoal(ExpeditionMember member) {
        this.member = member;
        setFlags(EnumSet.of(Flag.MOVE));
    }

    @Nullable
    private LivingEntity findThreat() {
        LivingEntity hurtBy = member.getLastHurtByMob();
        if (hurtBy != null && hurtBy.isAlive() && ExpeditionMember.isThreat(hurtBy) && member.distanceToSqr(hurtBy) < SAFE_RANGE * SAFE_RANGE
                && member.tickCount - member.getLastHurtByMobTimestamp() < 200) {
            return hurtBy;
        }
        List<LivingEntity> near = member.level().getEntitiesOfClass(LivingEntity.class,
                member.getBoundingBox().inflate(SCARE_RANGE, 4.0, SCARE_RANGE), ExpeditionMember::isThreat);
        LivingEntity best = null;
        double bestDist = Double.MAX_VALUE;
        for (LivingEntity e : near) {
            double d = member.distanceToSqr(e);
            if (d < bestDist && member.getSensing().hasLineOfSight(e)) {
                bestDist = d;
                best = e;
            }
        }
        return best;
    }

    @Override
    public boolean canUse() {
        if (member.role() == CrewRole.GUARD || member.tickCount % 5 != 0 || member.isTrading()) {
            return false;
        }
        threat = findThreat();
        return threat != null;
    }

    @Override
    public void start() {
        member.setFleeing(true);
        member.shout("flee");
        repath = 0;
        run();
    }

    private void run() {
        if (threat == null) {
            return;
        }
        Vec3 from = threat.position();
        ExpeditionMember guard = member.nearestGuard(32.0);
        Vec3 dest = null;
        if (guard != null && guard.distanceToSqr(threat) > 9.0) {
            // behind the guard, as seen from the threat
            Vec3 g = guard.position();
            Vec3 away = g.subtract(from);
            away = away.lengthSqr() < 1.0E-4 ? Vec3.ZERO : away.normalize().scale(2.5);
            dest = g.add(away);
        }
        if (dest == null) {
            dest = DefaultRandomPos.getPosAway(member, 16, 7, from);
        }
        if (dest != null) {
            member.getNavigation().moveTo(dest.x, dest.y, dest.z, 1.0);
        }
    }

    @Override
    public boolean requiresUpdateEveryTick() {
        return true;
    }

    @Override
    public void tick() {
        if (++repath >= 20) {
            repath = 0;
            LivingEntity again = findThreat();
            if (again != null) {
                threat = again;
                run();
            }
        }
    }

    @Override
    public boolean canContinueToUse() {
        return threat != null && threat.isAlive() && member.distanceToSqr(threat) < SAFE_RANGE * SAFE_RANGE
                && !member.getNavigation().isDone();
    }

    @Override
    public void stop() {
        member.setFleeing(false);
        threat = null;
    }
}
