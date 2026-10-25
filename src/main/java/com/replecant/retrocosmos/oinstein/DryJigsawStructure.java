package com.replecant.retrocosmos.oinstein;

import com.mojang.datafixers.util.Either;
import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Optional;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructurePiece;
import net.minecraft.world.level.levelgen.structure.StructureType;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePiecesBuilder;
import net.minecraft.world.level.levelgen.structure.structures.JigsawStructure;

/**
 * {@code retrocosmos:dry_jigsaw}: a vanilla jigsaw structure that refuses wet sites. After the pieces are assembled
 * the footprint of every piece is sampled (centre and corners); a sample is wet when the world-gen surface lies
 * above the ocean floor there, i.e. water (or lava) covers the ground, or when the ground lies below sea level (the
 * terrain adaptation would dig into the aquifer): the ground must lie at least {@code sea_level_margin} blocks above
 * sea level (0 by default; a half-buried bunker needs its depth, -64 switches the test off). The start piece must be
 * completely dry, the
 * other pieces may have at most {@code wet_tolerance} of their samples wet (streams through a village).
 * With {@code dry_search_chunks} > 0 (the one-per-world Institute) nearby chunks are tried in turn when the placement
 * chunk itself is wet, so the structure still appears - on dry land a little to the side.
 */
public class DryJigsawStructure extends Structure {
    public static final MapCodec<DryJigsawStructure> CODEC = RecordCodecBuilder.mapCodec(i -> i.group(
            JigsawStructure.CODEC.forGetter(s -> s.inner),
            Codec.intRange(0, 3).optionalFieldOf("dry_search_chunks", 0).forGetter(s -> s.searchChunks),
            Codec.floatRange(0.0F, 1.0F).optionalFieldOf("wet_tolerance", 0.0F).forGetter(s -> s.wetTolerance),
            Codec.intRange(-64, 32).optionalFieldOf("sea_level_margin", 0).forGetter(s -> s.seaLevelMargin))
            .apply(i, DryJigsawStructure::new));
    public static final StructureType<DryJigsawStructure> TYPE = () -> CODEC;

    private final JigsawStructure inner;
    private final int searchChunks;
    private final float wetTolerance;
    private final int seaLevelMargin;

    public DryJigsawStructure(JigsawStructure inner, int searchChunks, float wetTolerance, int seaLevelMargin) {
        super(new StructureSettings(inner.biomes(), inner.spawnOverrides(), inner.step(), inner.terrainAdaptation()));
        this.inner = inner;
        this.searchChunks = searchChunks;
        this.wetTolerance = wetTolerance;
        this.seaLevelMargin = seaLevelMargin;
    }

    @Override
    protected Optional<GenerationStub> findGenerationPoint(GenerationContext context) {
        ChunkPos home = context.chunkPos();
        List<ChunkPos> candidates = new ArrayList<>();
        for (int dx = -searchChunks; dx <= searchChunks; dx++) {
            for (int dz = -searchChunks; dz <= searchChunks; dz++) {
                candidates.add(new ChunkPos(home.x + dx, home.z + dz));
            }
        }
        candidates.sort(Comparator.comparingInt(c -> (c.x - home.x) * (c.x - home.x) + (c.z - home.z) * (c.z - home.z)));
        for (ChunkPos chunk : candidates) {
            GenerationContext ctx = chunk.equals(home) ? context : new GenerationContext(context.registryAccess(),
                    context.chunkGenerator(), context.biomeSource(), context.randomState(), context.structureTemplateManager(),
                    context.seed(), chunk, context.heightAccessor(), context.validBiome());
            Optional<GenerationStub> stub = inner.findValidGenerationPoint(ctx);
            if (stub.isEmpty()) {
                continue;
            }
            StructurePiecesBuilder pieces = stub.get().getPiecesBuilder();
            if (isDry(ctx, pieces.build().pieces())) {
                return Optional.of(new GenerationStub(stub.get().position(), Either.right(pieces)));
            }
        }
        return Optional.empty();
    }

    private boolean isDry(GenerationContext ctx, List<StructurePiece> pieces) {
        int samples = 0;
        int wet = 0;
        for (int i = 0; i < pieces.size(); i++) {
            BoundingBox box = pieces.get(i).getBoundingBox();
            int x0 = box.minX() + Math.min(1, box.getXSpan() / 4), x1 = box.maxX() - Math.min(1, box.getXSpan() / 4);
            int z0 = box.minZ() + Math.min(1, box.getZSpan() / 4), z1 = box.maxZ() - Math.min(1, box.getZSpan() / 4);
            int[][] points = {{(x0 + x1) / 2, (z0 + z1) / 2}, {x0, z0}, {x1, z0}, {x0, z1}, {x1, z1}};
            for (int[] p : points) {
                boolean w = isWet(ctx, p[0], p[1], seaLevelMargin);
                if (w && i == 0) {
                    return false;           // the start piece (plaza, temple, compound) must stand on dry land
                }
                samples++;
                wet += w ? 1 : 0;
            }
        }
        return wet <= wetTolerance * samples;
    }

    /** Water over the ground, or dry ground below sea level (levelling it for the structure lets the aquifer in). */
    private static boolean isWet(GenerationContext ctx, int x, int z, int seaLevelMargin) {
        ChunkGenerator gen = ctx.chunkGenerator();
        int surface = gen.getFirstOccupiedHeight(x, z, Heightmap.Types.WORLD_SURFACE_WG, ctx.heightAccessor(), ctx.randomState());
        int floor = gen.getFirstOccupiedHeight(x, z, Heightmap.Types.OCEAN_FLOOR_WG, ctx.heightAccessor(), ctx.randomState());
        return surface > floor || floor < gen.getSeaLevel() + seaLevelMargin;
    }

    @Override
    public StructureType<?> type() {
        return ModOinstein.DRY_JIGSAW.get();
    }
}
