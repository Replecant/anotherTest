package com.replecant.retrocosmos.oinstein;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureProcessor;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureProcessorType;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;

/**
 * {@code retrocosmos:furniture_facing}: turns the horizontal {@code facing} of blocks that do not rotate themselves
 * (the station furniture: control panels, posters, computer banks...) with the structure. Without it a rotated
 * Oinstein structure keeps their template facing, and wall pieces then pop off for want of a wall behind them.
 * Blocks whose {@code rotate} already turns the facing (stairs, the keycard reader...) are left alone, so this stays
 * correct if the furniture learns to rotate itself.
 */
public class FurnitureFacingProcessor extends StructureProcessor {
    public static final FurnitureFacingProcessor INSTANCE = new FurnitureFacingProcessor();
    public static final MapCodec<FurnitureFacingProcessor> CODEC = MapCodec.unit(() -> INSTANCE);
    public static final StructureProcessorType<FurnitureFacingProcessor> TYPE = () -> CODEC;

    @Override
    public StructureTemplate.StructureBlockInfo processBlock(LevelReader level, BlockPos offset, BlockPos pos,
                                                             StructureTemplate.StructureBlockInfo raw,
                                                             StructureTemplate.StructureBlockInfo info, StructurePlaceSettings settings) {
        Rotation rotation = settings.getRotation();
        BlockState state = info.state();
        if (rotation == Rotation.NONE || !state.hasProperty(BlockStateProperties.HORIZONTAL_FACING)
                || state.rotate(Rotation.CLOCKWISE_90) != state) {
            return info;
        }
        Direction facing = state.getValue(BlockStateProperties.HORIZONTAL_FACING);
        return new StructureTemplate.StructureBlockInfo(info.pos(),
                state.setValue(BlockStateProperties.HORIZONTAL_FACING, rotation.rotate(facing)), info.nbt());
    }

    @Override
    protected StructureProcessorType<?> getType() {
        return ModOinstein.FURNITURE_FACING.get();
    }
}
