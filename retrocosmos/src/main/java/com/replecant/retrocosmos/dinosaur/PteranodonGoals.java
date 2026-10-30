package com.replecant.retrocosmos.dinosaur;

import java.util.EnumSet;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;

/** The pteranodon's three moods: stooping on an intruder, flying home to roost, and wheeling over the jungle. */
final class PteranodonGoals {
    private PteranodonGoals() {}

    /** Climb above the target, then dive beak-first; after a few hits (or a long chase) it gives up and goes home. */
    static final class Stoop extends Goal {
        private static final int MAX_HITS = 3;
        /** The long beak reaches this far past the body (blocks). */
        private static final double BEAK_REACH = 0.7;
        private final Pteranodon ptero;
        private boolean diving;
        private int ticks;
        private int total;
        private int hits;

        Stoop(Pteranodon ptero) {
            this.ptero = ptero;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = ptero.getTarget();
            return t != null && t.isAlive();
        }

        @Override
        public boolean canContinueToUse() {
            LivingEntity t = ptero.getTarget();
            return t != null && t.isAlive() && ptero.distanceToSqr(t) < 40.0 * 40.0;
        }

        @Override
        public void start() {
            if (ptero.isPerched()) {
                ptero.setPerched(false);
            }
            diving = false;
            ticks = total = hits = 0;
        }

        @Override
        public void stop() {
            ptero.setDiving(false);
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void tick() {
            LivingEntity target = ptero.getTarget();
            if (target == null) {
                return;
            }
            ticks++;
            total++;
            if (diving) {
                ptero.getMoveControl().setWantedPosition(target.getX(), target.getY() + target.getBbHeight() * 0.6, target.getZ(), 1.7);
                ptero.getLookControl().setLookAt(target, 30.0F, 30.0F);
                if (ptero.getBoundingBox().inflate(BEAK_REACH).intersects(target.getBoundingBox())) {
                    if (ptero.level() instanceof net.minecraft.server.level.ServerLevel level && ptero.doHurtTarget(level, target)) {
                        hits++;
                        Vec3 push = target.position().subtract(ptero.position()).multiply(1.0, 0.0, 1.0).normalize().scale(0.8);
                        target.push(push.x, 0.25, push.z);
                        target.hurtMarked = true;
                    }
                    pullUp();
                } else if (ticks > 80) {
                    pullUp();
                }
            } else {
                // circle up above and a little away from the target
                double a = (total * 0.05) % (Math.PI * 2);
                double x = target.getX() + Math.cos(a) * 8.0;
                double z = target.getZ() + Math.sin(a) * 8.0;
                ptero.getMoveControl().setWantedPosition(x, target.getY() + 9.0, z, 1.0);
                if (ticks > 30 && ptero.getY() > target.getY() + 5.0 || ticks > 100) {
                    diving = true;
                    ticks = 0;
                    ptero.setDiving(true);
                    ptero.playSound(SoundEvents.PHANTOM_SWOOP, 1.4F, 0.8F);
                }
            }
            if (hits >= MAX_HITS || total > 600) {
                ptero.setTarget(null);
                ptero.setLastHurtByMob(null);
            }
        }

        private void pullUp() {
            diving = false;
            ticks = 0;
            ptero.setDiving(false);
        }
    }

    /** After a spell of flying, pick the highest treetop around and settle on it. */
    static final class Roost extends Goal {
        private final Pteranodon ptero;
        @Nullable
        private BlockPos perch;
        private int ticks;
        private int nextTry;

        Roost(Pteranodon ptero) {
            this.ptero = ptero;
            setFlags(EnumSet.of(Flag.MOVE));
        }

        @Override
        public boolean canUse() {
            if (ptero.isPerched() || ptero.getTarget() != null || ptero.flightTicks < 240 || --nextTry > 0) {
                return false;
            }
            nextTry = 40;
            perch = ptero.findPerch(ptero.anchor(), 20);
            if (perch == null) {
                perch = ptero.findPerch(ptero.blockPosition(), 24);
            }
            return perch != null;
        }

        @Override
        public boolean canContinueToUse() {
            return perch != null && !ptero.isPerched() && ptero.getTarget() == null && ticks < 500
                    && ptero.hasRoom(perch);
        }

        @Override
        public void start() {
            ticks = 0;
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void tick() {
            if (perch == null) {
                return;
            }
            ticks++;
            double cx = perch.getX() + 0.5;
            double cz = perch.getZ() + 0.5;
            double top = perch.getY() + 1.0;
            double dx = cx - ptero.getX();
            double dz = cz - ptero.getZ();
            double horiz = Math.sqrt(dx * dx + dz * dz);
            if (horiz > 3.5) {
                ptero.getMoveControl().setWantedPosition(cx, top + 5.0, cz, 0.8);
            } else {
                ptero.getMoveControl().setWantedPosition(cx, top + 0.1, cz, 0.35);
                if (horiz < 0.7 && ptero.getY() - top < 1.0) {
                    ptero.snapTo(cx, top, cz, ptero.getYRot(), 0.0F);
                    ptero.setPerched(true);
                    ptero.setAnchor(perch);
                }
            }
        }
    }

    /** Wheeling over the canopy around the home roost; now and then the loop drifts to new ground. */
    static final class Circle extends Goal {
        private final Pteranodon ptero;
        private double angle;
        private double radius;
        private double height;
        private int dir;

        Circle(Pteranodon ptero) {
            this.ptero = ptero;
            setFlags(EnumSet.of(Flag.MOVE));
        }

        @Override
        public boolean canUse() {
            return !ptero.isPerched() && ptero.getTarget() == null;
        }

        @Override
        public void start() {
            BlockPos a = ptero.anchor();
            angle = Mth.atan2(ptero.getZ() - a.getZ(), ptero.getX() - a.getX());
            dir = ptero.getRandom().nextBoolean() ? 1 : -1;
            newLoop();
        }

        private void newLoop() {
            radius = 9.0 + ptero.getRandom().nextDouble() * 12.0;
            height = 5.0 + ptero.getRandom().nextDouble() * 8.0;
            if (ptero.getRandom().nextInt(4) == 0) {
                BlockPos a = ptero.anchor();
                ptero.setAnchor(a.offset(ptero.getRandom().nextInt(33) - 16, 0, ptero.getRandom().nextInt(33) - 16));
            }
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void tick() {
            BlockPos a = ptero.anchor();
            double x = a.getX() + 0.5 + Math.cos(angle) * radius;
            double z = a.getZ() + 0.5 + Math.sin(angle) * radius;
            int canopy = ptero.level().getHeight(Heightmap.Types.MOTION_BLOCKING, Mth.floor(x), Mth.floor(z));
            double y = Math.max(canopy + 5.0, a.getY() + height);
            double dx = x - ptero.getX();
            double dz = z - ptero.getZ();
            if (dx * dx + dz * dz < 9.0) {
                angle += dir * 0.45;
                if (ptero.getRandom().nextInt(30) == 0) {
                    newLoop();
                }
            }
            ptero.getMoveControl().setWantedPosition(x, y, z, 0.6);
        }
    }
}
