package com.replecant.retrocosmos.dinosaur;

import java.util.EnumSet;
import javax.annotation.Nullable;
import net.minecraft.world.entity.ai.goal.Goal;

/** Idle raptors that strayed from their pack trot back to the nearest packmate. */
public class RaptorPackGoal extends Goal {
    private static final double SEARCH = 24.0;
    private static final double TOO_FAR_SQR = 9.0 * 9.0;
    private static final double CLOSE_ENOUGH_SQR = 4.0 * 4.0;

    private final VenusRaptor raptor;
    @Nullable
    private VenusRaptor mate;
    private int recalc;

    public RaptorPackGoal(VenusRaptor raptor) {
        this.raptor = raptor;
        setFlags(EnumSet.of(Flag.MOVE));
    }

    @Override
    public boolean canUse() {
        if (raptor.getTarget() != null || raptor.getRandom().nextInt(reducedTickDelay(40)) != 0) {
            return false;
        }
        VenusRaptor nearest = null;
        double best = Double.MAX_VALUE;
        for (VenusRaptor other : raptor.level().getEntitiesOfClass(VenusRaptor.class, raptor.getBoundingBox().inflate(SEARCH, 8.0, SEARCH),
                r -> r != raptor && r.isAlive())) {
            double d = raptor.distanceToSqr(other);
            if (d < best) {
                best = d;
                nearest = other;
            }
        }
        if (nearest == null || best < TOO_FAR_SQR) {
            return false;
        }
        mate = nearest;
        return true;
    }

    @Override
    public boolean canContinueToUse() {
        return mate != null && mate.isAlive() && raptor.getTarget() == null && raptor.distanceToSqr(mate) > CLOSE_ENOUGH_SQR;
    }

    @Override
    public void start() {
        recalc = 0;
    }

    @Override
    public void stop() {
        mate = null;
        raptor.getNavigation().stop();
    }

    @Override
    public void tick() {
        if (mate != null && --recalc <= 0) {
            recalc = adjustedTickDelay(10);
            raptor.getNavigation().moveTo(mate, 1.0);
        }
    }
}
