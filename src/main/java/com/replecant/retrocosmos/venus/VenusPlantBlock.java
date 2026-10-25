package com.replecant.retrocosmos.venus;

import com.mojang.serialization.MapCodec;
import com.replecant.retrocosmos.RetroCosmos;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.tags.TagKey;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.VegetationBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * A small Venus plant (sedge, horsetail, cycad, fire lily, glowcap). Grows on soil-like blocks (#minecraft:dirt);
 * fungi ({@code onStone}) also take root on natural rock floors (#retrocosmos:venus_rock_floor), so they can carpet
 * cave bottoms - but not the steel and concrete of structures.
 */
public class VenusPlantBlock extends VegetationBlock {
    /** Natural rock floors fungi may grow on (#retrocosmos:venus_rock_floor) - never steel, concrete or masonry. */
    public static final TagKey<Block> ROCK_FLOOR = TagKey.create(Registries.BLOCK,
            Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "venus_rock_floor"));
    private final VoxelShape shape;
    private final boolean onStone;

    public VenusPlantBlock(Properties properties, VoxelShape shape, boolean onStone) {
        super(properties);
        this.shape = shape;
        this.onStone = onStone;
    }

    @Override
    protected MapCodec<? extends VegetationBlock> codec() {
        VoxelShape s = shape;
        boolean stone = onStone;
        return simpleCodec(p -> new VenusPlantBlock(p, s, stone));
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return shape.move(state.getOffset(pos));
    }

    @Override
    protected boolean mayPlaceOn(BlockState state, BlockGetter level, BlockPos pos) {
        return super.mayPlaceOn(state, level, pos) || (onStone && state.is(ROCK_FLOOR));
    }
}
