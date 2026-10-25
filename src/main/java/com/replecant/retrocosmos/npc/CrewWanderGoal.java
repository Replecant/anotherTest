package com.replecant.retrocosmos.npc;

import java.util.EnumSet;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.level.Level;

/**
 * Strolls between random spots around the crew member's post, pausing at each (a guard "stands watch" there, Cooper
 * clasps his hands behind his back). Someone who strayed far from the post heads straight back to it.
 */
public class CrewWanderGoal extends Goal {
    private final ExpeditionMember member;
    private long nextMoveAt;

    public CrewWanderGoal(ExpeditionMember member) {
        this.member = member;
        setFlags(EnumSet.of(Flag.MOVE));
    }

    private double speed() {
        return switch (member.role()) {
            case COOPER -> 0.45;
            case GUARD -> 0.5;
            case SCIENTIST -> 0.55;
        };
    }

    private int pause() {
        return switch (member.role()) {
            case COOPER -> 160 + member.getRandom().nextInt(300);
            case GUARD -> 100 + member.getRandom().nextInt(260);
            case SCIENTIST -> 120 + member.getRandom().nextInt(240);
        };
    }

    @Override
    public boolean canUse() {
        if (member.isBusy() || member.level().getGameTime() < nextMoveAt) {
            return false;
        }
        BlockPos target = pickTarget();
        if (target == null) {
            nextMoveAt = member.level().getGameTime() + 40;
            return false;
        }
        return member.getNavigation().moveTo(target.getX() + 0.5, target.getY(), target.getZ() + 0.5, speed());
    }

    @Nullable
    private BlockPos pickTarget() {
        BlockPos home = member.home();
        int r = member.role().radius;
        boolean strayed = member.blockPosition().distSqr(home) > (double) (r + 6) * (r + 6);
        int spread = strayed ? 2 : (member.role() == CrewRole.COOPER ? r - 1 : r);
        for (int tries = 0; tries < 12; tries++) {
            int dx = member.getRandom().nextInt(spread * 2 + 1) - spread;
            int dz = member.getRandom().nextInt(spread * 2 + 1) - spread;
            BlockPos stand = standable(member.level(), home.offset(dx, 0, dz), 4);
            if (stand != null) {
                return stand;
            }
        }
        return null;
    }

    /** A spot near {@code around} (searching {@code dy} up and down) where a person can stand. */
    @Nullable
    static BlockPos standable(Level level, BlockPos around, int dy) {
        for (int i = 0; i <= dy * 2; i++) {
            int off = (i % 2 == 0) ? i / 2 : -(i + 1) / 2;
            BlockPos p = around.above(off);
            if (canStand(level, p)) {
                return p;
            }
        }
        return null;
    }

    static boolean canStand(Level level, BlockPos feet) {
        if (!level.isLoaded(feet)) {
            return false;
        }
        BlockPos below = feet.below();
        return level.getBlockState(below).isFaceSturdy(level, below, net.minecraft.core.Direction.UP)
                && level.getBlockState(feet).getCollisionShape(level, feet).isEmpty()
                && level.getBlockState(feet.above()).getCollisionShape(level, feet.above()).isEmpty()
                && level.getFluidState(feet).isEmpty();
    }

    @Override
    public boolean canContinueToUse() {
        return !member.isBusy() && !member.getNavigation().isDone();
    }

    @Override
    public void stop() {
        nextMoveAt = member.level().getGameTime() + pause();
    }
}
