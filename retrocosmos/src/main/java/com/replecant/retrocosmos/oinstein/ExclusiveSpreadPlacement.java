package com.replecant.retrocosmos.oinstein;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import java.util.List;
import java.util.Optional;
import net.minecraft.core.Vec3i;
import net.minecraft.util.ExtraCodecs;
import net.minecraft.world.level.chunk.ChunkGeneratorStructureState;
import net.minecraft.world.level.levelgen.structure.placement.RandomSpreadStructurePlacement;
import net.minecraft.world.level.levelgen.structure.placement.RandomSpreadType;
import net.minecraft.world.level.levelgen.structure.placement.StructurePlacement;
import net.minecraft.world.level.levelgen.structure.placement.StructurePlacementType;

/**
 * {@code retrocosmos:exclusive_spread}: vanilla random spread placement that may keep clear of several other
 * structure sets ({@code exclusion_zones}, a list of {other_set, chunk_count}) instead of just one.
 * Used by the ruins and Dr. Oinstein's outposts to stay out of each other's way and away from the Institute.
 */
public class ExclusiveSpreadPlacement extends RandomSpreadStructurePlacement {
    public static final MapCodec<ExclusiveSpreadPlacement> CODEC = RecordCodecBuilder.mapCodec(i -> i.group(
            Vec3i.offsetCodec(16).optionalFieldOf("locate_offset", Vec3i.ZERO).forGetter(ExclusiveSpreadPlacement::locateOffset),
            StructurePlacement.FrequencyReductionMethod.CODEC.optionalFieldOf("frequency_reduction_method",
                    StructurePlacement.FrequencyReductionMethod.DEFAULT).forGetter(ExclusiveSpreadPlacement::frequencyReductionMethod),
            Codec.floatRange(0.0F, 1.0F).optionalFieldOf("frequency", 1.0F).forGetter(ExclusiveSpreadPlacement::frequency),
            ExtraCodecs.NON_NEGATIVE_INT.fieldOf("salt").forGetter(ExclusiveSpreadPlacement::salt),
            ExclusionZone.CODEC.optionalFieldOf("exclusion_zone").forGetter(ExclusiveSpreadPlacement::exclusionZone),
            Codec.intRange(0, 4096).fieldOf("spacing").forGetter(ExclusiveSpreadPlacement::spacing),
            Codec.intRange(0, 4096).fieldOf("separation").forGetter(ExclusiveSpreadPlacement::separation),
            RandomSpreadType.CODEC.optionalFieldOf("spread_type", RandomSpreadType.LINEAR).forGetter(ExclusiveSpreadPlacement::spreadType),
            ExclusionZone.CODEC.listOf().optionalFieldOf("exclusion_zones", List.of()).forGetter(ExclusiveSpreadPlacement::zones))
            .apply(i, ExclusiveSpreadPlacement::new));
    public static final StructurePlacementType<ExclusiveSpreadPlacement> TYPE = () -> CODEC;

    private final List<ExclusionZone> zones;

    public ExclusiveSpreadPlacement(Vec3i locateOffset, StructurePlacement.FrequencyReductionMethod method, float frequency, int salt,
                                    Optional<ExclusionZone> exclusionZone, int spacing, int separation, RandomSpreadType spreadType,
                                    List<ExclusionZone> zones) {
        super(locateOffset, method, frequency, salt, exclusionZone, spacing, separation, spreadType);
        this.zones = List.copyOf(zones);
    }

    public List<ExclusionZone> zones() {
        return zones;
    }

    @Override
    public boolean applyInteractionsWithOtherStructures(ChunkGeneratorStructureState state, int x, int z) {
        if (!super.applyInteractionsWithOtherStructures(state, x, z)) {
            return false;
        }
        for (ExclusionZone zone : zones) {
            if (state.hasStructureChunkInRange(zone.otherSet(), x, z, zone.chunkCount())) {
                return false;
            }
        }
        return true;
    }

    @Override
    public StructurePlacementType<?> type() {
        return ModOinstein.EXCLUSIVE_SPREAD.get();
    }
}
