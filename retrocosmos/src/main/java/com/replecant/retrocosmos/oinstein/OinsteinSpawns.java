package com.replecant.retrocosmos.oinstein;

import com.replecant.retrocosmos.RetroCosmos;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.Difficulty;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructureStart;
import net.minecraft.world.phys.AABB;

/**
 * The one spawn rule for all of Dr. Oinstein's forces (#retrocosmos:oinstein_forces). They only spawn naturally
 * through the Institute's structure spawn overrides, and those would otherwise refill the monster cap inside the
 * compound day and night. So a natural spawn passes only one time in four, and only while fewer than
 * {@link #INSTITUTE_CAP} of his forces are within {@link #INSTITUTE_RADIUS} blocks (elsewhere {@link #CAP} within
 * {@link #RADIUS}); none at all in the lower laboratory (its {@link AttachedTemplatePiece}). Spawns from eggs,
 * commands, structures and spawners are not limited.
 */
public final class OinsteinSpawns {
    public static final ResourceKey<Structure> INSTITUTE = ResourceKey.create(Registries.STRUCTURE,
            Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "oinstein_complex"));
    public static final int INSTITUTE_RADIUS = 48;
    public static final int INSTITUTE_CAP = 8;
    public static final int RADIUS = 32;
    public static final int CAP = 3;

    private OinsteinSpawns() {}

    public static <T extends Entity> boolean check(EntityType<T> type, ServerLevelAccessor level, EntitySpawnReason reason,
                                                   BlockPos pos, RandomSource random) {
        if (reason != EntitySpawnReason.NATURAL && reason != EntitySpawnReason.CHUNK_GENERATION) {
            return true;
        }
        if (level.getDifficulty() == Difficulty.PEACEFUL || random.nextInt(4) != 0) {
            return false;
        }
        ServerLevel server = level.getLevel();
        StructureStart start = server.structureManager().getStructureWithPieceAt(pos, h -> h.is(INSTITUTE));
        boolean institute = start.isValid();
        if (institute && start.getPieces().stream().anyMatch(p -> p instanceof AttachedTemplatePiece && p.getBoundingBox().isInside(pos))) {
            return false;                   // the lower laboratory keeps its placed guards only
        }
        int radius = institute ? INSTITUTE_RADIUS : RADIUS;
        int cap = institute ? INSTITUTE_CAP : CAP;
        int near = level.getEntitiesOfClass(LivingEntity.class, new AABB(pos).inflate(radius),
                e -> e.getType().is(ModOinstein.FORCES)).size();
        return near < cap;
    }
}
