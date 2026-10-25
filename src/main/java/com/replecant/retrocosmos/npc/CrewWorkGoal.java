package com.replecant.retrocosmos.npc;

import java.util.ArrayList;
import java.util.EnumSet;
import java.util.List;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.phys.Vec3;

/**
 * Scientists (and Dr. Cooper, in his office) look for "work" around their post - instruments, lab benches, plants,
 * relics - walk over, face it and busy themselves with it for a while, sometimes writing up the results in their
 * notebook afterwards, then move on to the next thing.
 */
public class CrewWorkGoal extends Goal {
    private static final int SCAN_EVERY = 1200;
    private static final int MAX_PLANTS = 8;

    private final ExpeditionMember member;
    private final List<BlockPos> spots = new ArrayList<>();
    private long scannedAt;
    private boolean scanned;
    private long nextAt;
    @Nullable
    private BlockPos spot;
    @Nullable
    private BlockPos last;
    @Nullable
    private BlockPos stand;
    private WorkKind kind = WorkKind.CONSOLE;
    private boolean arrived;
    private int walkTicks;
    private int workTicks;
    private int notesTicks;

    public CrewWorkGoal(ExpeditionMember member) {
        this.member = member;
        setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
    }

    /** The work spots around the post (cached, rescanned once a minute). */
    List<BlockPos> spots(ServerLevel level) {
        long now = level.getGameTime();
        if (scanned && now - scannedAt < SCAN_EVERY) {
            return spots;
        }
        scanned = true;
        scannedAt = now;
        spots.clear();
        List<BlockPos> plants = new ArrayList<>();
        BlockPos home = member.home();
        int r = member.role().radius;
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
        for (int dx = -r; dx <= r; dx++) {
            for (int dz = -r; dz <= r; dz++) {
                for (int dy = -3; dy <= 3; dy++) {
                    p.set(home.getX() + dx, home.getY() + dy, home.getZ() + dz);
                    if (!level.isLoaded(p)) {
                        continue;
                    }
                    WorkKind k = WorkKind.of(level.getBlockState(p));
                    if (k != null && k.interests(member.role())) {
                        (k == WorkKind.PLANT ? plants : spots).add(p.immutable());
                    }
                }
            }
        }
        // plenty of ferns in a jungle camp: keep a handful so the instruments still get attention
        while (plants.size() > MAX_PLANTS) {
            plants.remove(member.getRandom().nextInt(plants.size()));
        }
        spots.addAll(plants);
        return spots;
    }

    @Override
    public boolean canUse() {
        if (member.role() == CrewRole.GUARD || member.isBusy() || !(member.level() instanceof ServerLevel level)) {
            return false;
        }
        long now = level.getGameTime();
        if (now < nextAt) {
            return false;
        }
        nextAt = now + 20;
        List<BlockPos> candidates = new ArrayList<>(spots(level));
        if (candidates.size() > 1 && last != null) {
            candidates.remove(last);
        }
        while (!candidates.isEmpty()) {
            BlockPos s = candidates.remove(member.getRandom().nextInt(candidates.size()));
            WorkKind k = WorkKind.of(level.getBlockState(s));
            if (k == null) {
                scanned = false;  // the camp changed: rescan next time
                continue;
            }
            BlockPos at = standBeside(level, s);
            if (at != null) {
                spot = s;
                stand = at;
                kind = k;
                return true;
            }
        }
        nextAt = now + 200;
        return false;
    }

    /** The free spot next to the work block that is closest to us. */
    @Nullable
    private BlockPos standBeside(ServerLevel level, BlockPos s) {
        BlockPos best = null;
        double bestDist = Double.MAX_VALUE;
        for (int dx = -1; dx <= 1; dx++) {
            for (int dz = -1; dz <= 1; dz++) {
                if (dx == 0 && dz == 0) {
                    continue;
                }
                for (int dy = -1; dy <= 1; dy++) {
                    BlockPos p = s.offset(dx, dy, dz);
                    if (CrewWanderGoal.canStand(level, p)) {
                        // facing the block square-on beats a diagonal
                        double d = p.distSqr(member.blockPosition()) + (dx != 0 && dz != 0 ? 4.0 : 0.0);
                        if (d < bestDist) {
                            bestDist = d;
                            best = p;
                        }
                    }
                }
            }
        }
        return best;
    }

    @Override
    public void start() {
        arrived = false;
        walkTicks = 0;
        notesTicks = 0;
        workTicks = 0;
        moveToStand();
    }

    private void moveToStand() {
        if (stand != null) {
            member.getNavigation().moveTo(stand.getX() + 0.5, stand.getY(), stand.getZ() + 0.5, 0.55);
        }
    }

    @Override
    public boolean requiresUpdateEveryTick() {
        return true;
    }

    @Override
    public void tick() {
        if (spot == null || stand == null) {
            return;
        }
        Vec3 look = new Vec3(spot.getX() + 0.5, spot.getY() + kind.lookHeight, spot.getZ() + 0.5);
        if (!arrived) {
            walkTicks++;
            double d = member.distanceToSqr(stand.getX() + 0.5, stand.getY(), stand.getZ() + 0.5);
            double dx = member.getX() - look.x;
            double dz = member.getZ() - look.z;
            boolean close = dx * dx + dz * dz < 2.4 * 2.4 && Math.abs(member.getY() - spot.getY()) < 1.5;
            // the navigation counts "within a block" as there, so a stop next to the stand spot will do
            if (d < 0.6 || (member.getNavigation().isDone() && (d < 2.6 || close))) {
                arrived = true;
                member.getNavigation().stop();
                workTicks = 120 + member.getRandom().nextInt(180);
                member.beginWork(kind);
            } else if (member.getNavigation().isDone() && walkTicks % 40 == 0) {
                moveToStand();
            }
            return;
        }
        member.getLookControl().setLookAt(look.x, look.y, look.z, 30.0F, 30.0F);
        if (workTicks > 0) {
            workTicks--;
            member.workTick(spot, kind);
            if (workTicks == 0 && kind != WorkKind.DESK && member.getRandom().nextInt(3) == 0) {
                notesTicks = 80 + member.getRandom().nextInt(60);  // write up the results
                member.beginWork(WorkKind.DESK);
            }
        } else if (notesTicks > 0) {
            notesTicks--;
            member.workTick(spot, WorkKind.DESK);
        }
    }

    @Override
    public boolean canContinueToUse() {
        if (member.isBusy() || spot == null) {
            return false;
        }
        return arrived ? workTicks > 0 || notesTicks > 0 : walkTicks < 240;
    }

    @Override
    public void stop() {
        member.endWork();
        last = spot;
        spot = null;
        stand = null;
        nextAt = member.level().getGameTime() + 80 + member.getRandom().nextInt(220);
    }
}
