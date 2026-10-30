package com.replecant.retrocosmos.ruins;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.util.Mth;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.IntegerProperty;

/** Carved stone bearing one of four Venusian glyphs; a placed block picks its glyph from its position. */
public class GlyphStoneBlock extends Block {
    public static final MapCodec<GlyphStoneBlock> CODEC = simpleCodec(GlyphStoneBlock::new);
    public static final IntegerProperty GLYPH = IntegerProperty.create("glyph", 0, 3);

    public GlyphStoneBlock(Properties properties) {
        super(properties);
        registerDefaultState(stateDefinition.any().setValue(GLYPH, 0));
    }

    @Override
    protected MapCodec<? extends Block> codec() {
        return CODEC;
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(GLYPH);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        BlockPos pos = context.getClickedPos();
        return defaultBlockState().setValue(GLYPH, (int) Math.floorMod(Mth.getSeed(pos) >> 7, 4L));
    }
}
