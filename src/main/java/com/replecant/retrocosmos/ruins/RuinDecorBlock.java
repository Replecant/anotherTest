package com.replecant.retrocosmos.ruins;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/** A small carved furnishing with a fixed, symmetric shape (altar, urn). */
public class RuinDecorBlock extends Block {
    public static final MapCodec<RuinDecorBlock> CODEC = simpleCodec(p -> new RuinDecorBlock(p, Shapes.block()));
    private final VoxelShape shape;

    public RuinDecorBlock(Properties properties, VoxelShape shape) {
        super(properties);
        this.shape = shape;
    }

    @Override
    protected MapCodec<? extends Block> codec() {
        return CODEC;
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return shape;
    }
}
