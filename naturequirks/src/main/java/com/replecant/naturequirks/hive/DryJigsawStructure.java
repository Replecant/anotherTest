package com.replecant.naturequirks.hive;

import com.mojang.datafixers.util.Either;
import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import java.util.List;
import java.util.Optional;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructurePiece;
import net.minecraft.world.level.levelgen.structure.StructureType;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePiecesBuilder;
import net.minecraft.world.level.levelgen.structure.structures.JigsawStructure;

/**
 * {@code naturequirks:dry_jigsaw}: a vanilla jigsaw structure that only stands on dry, fairly even land. The footprint
 * of the start piece is sampled (centre, corners, edge middles): every sample must be dry ground (the world-gen
 * surface is the ocean floor - no water or lava over it - and not below sea level), and the ground may rise and fall
 * by at most {@code max_relief} blocks over the footprint.
 */
public class DryJigsawStructure extends Structure {
    public static final MapCodec<DryJigsawStructure> CODEC = RecordCodecBuilder.mapCodec(i -> i.group(
            JigsawStructure.CODEC.forGetter(s -> s.inner),
            Codec.intRange(0, 64).optionalFieldOf("max_relief", 6).forGetter(s -> s.maxRelief))
            .apply(i, DryJigsawStructure::new));
    public static final StructureType<DryJigsawStructure> TYPE = () -> CODEC;

    private final JigsawStructure inner;
    private final int maxRelief;

    public DryJigsawStructure(JigsawStructure inner, int maxRelief) {
        super(new StructureSettings(inner.biomes(), inner.spawnOverrides(), inner.step(), inner.terrainAdaptation()));
        this.inner = inner;
        this.maxRelief = maxRelief;
    }

    @Override
    protected Optional<GenerationStub> findGenerationPoint(GenerationContext context) {
        Optional<GenerationStub> stub = inner.findValidGenerationPoint(context);
        if (stub.isEmpty()) {
            return stub;
        }
        StructurePiecesBuilder pieces = stub.get().getPiecesBuilder();
        List<StructurePiece> list = pieces.build().pieces();
        if (list.isEmpty() || !dryAndEven(context, list.get(0).getBoundingBox())) {
            return Optional.empty();
        }
        return Optional.of(new GenerationStub(stub.get().position(), Either.right(pieces)));
    }

    private boolean dryAndEven(GenerationContext ctx, BoundingBox box) {
        ChunkGenerator gen = ctx.chunkGenerator();
        int x0 = box.minX() + 1, x1 = box.maxX() - 1, z0 = box.minZ() + 1, z1 = box.maxZ() - 1;
        int xm = (x0 + x1) / 2, zm = (z0 + z1) / 2;
        int lo = Integer.MAX_VALUE, hi = Integer.MIN_VALUE;
        for (int[] p : new int[][] {{xm, zm}, {x0, z0}, {x1, z0}, {x0, z1}, {x1, z1}, {xm, z0}, {xm, z1}, {x0, zm}, {x1, zm}}) {
            int surface = gen.getFirstOccupiedHeight(p[0], p[1], Heightmap.Types.WORLD_SURFACE_WG, ctx.heightAccessor(), ctx.randomState());
            int floor = gen.getFirstOccupiedHeight(p[0], p[1], Heightmap.Types.OCEAN_FLOOR_WG, ctx.heightAccessor(), ctx.randomState());
            if (surface > floor || floor < gen.getSeaLevel()) {
                return false;
            }
            lo = Math.min(lo, floor);
            hi = Math.max(hi, floor);
            if (hi - lo > maxRelief) {
                return false;
            }
        }
        return true;
    }

    @Override
    public StructureType<?> type() {
        return ModHive.DRY_JIGSAW.get();
    }
}
