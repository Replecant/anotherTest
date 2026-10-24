package com.replecant.retrocosmos.registry;

import com.replecant.retrocosmos.furniture.FurnitureBlock;
import com.replecant.retrocosmos.furniture.FurnitureSpec;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.function.Function;
import java.util.function.UnaryOperator;
import javax.annotation.Nullable;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.RotatedPillarBlock;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.TransparentBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredItem;

/** "Atomic Home" furniture and decor pack. */
public final class ModFurniture {
    private static final List<DeferredItem<BlockItem>> ITEMS = new ArrayList<>();

    // --- Lighting ---
    public static final DeferredBlock<FurnitureBlock> ATOMIC_FLOOR_LAMP = furniture("atomic_floor_lamp",
            spec(Block.box(5, 0, 5, 11, 16, 11), false, false, true, 15, -1, null), metal(MapColor.METAL));
    public static final DeferredBlock<FurnitureBlock> ROCKET_TABLE_LAMP = furniture("rocket_table_lamp",
            spec(Block.box(5, 0, 5, 11, 13, 11), true, false, true, 12, -1, null), metal(MapColor.COLOR_RED));
    public static final DeferredBlock<FurnitureBlock> SPUTNIK_CHANDELIER = furniture("sputnik_chandelier",
            spec(Block.box(2, 4, 2, 14, 16, 14), false, false, true, 15, -1, null), metal(MapColor.METAL));

    // --- Seating & tables ---
    public static final DeferredBlock<FurnitureBlock> DINER_STOOL = furniture("diner_stool",
            spec(Block.box(3, 0, 3, 13, 10, 13), false, false, false, 0, 10, null), metal(MapColor.COLOR_RED));
    public static final DeferredBlock<FurnitureBlock> EGG_CHAIR = furniture("egg_chair",
            spec(Shapes.or(Block.box(1, 0, 1, 15, 6, 15), Block.box(1, 6, 10, 15, 16, 15)), true, false, false, 0, 6, null),
            soft(MapColor.SNOW));
    public static final DeferredBlock<FurnitureBlock> GOOGIE_SOFA = furniture("googie_sofa",
            spec(Shapes.or(Block.box(0, 0, 0, 16, 7, 16), Block.box(0, 7, 12, 16, 14, 16)), true, false, false, 0, 7, null),
            soft(MapColor.COLOR_CYAN));
    public static final DeferredBlock<FurnitureBlock> BOOMERANG_TABLE = furniture("boomerang_table",
            spec(Shapes.or(Block.box(0, 10, 0, 16, 12, 16), Block.box(7, 0, 7, 9, 10, 9)), true, false, false, 0, -1, null),
            metal(MapColor.SAND));

    // --- Electronics ---
    public static final DeferredBlock<FurnitureBlock> ATOMIC_TV = furniture("atomic_tv",
            spec(Block.box(1, 0, 2, 15, 15, 14), true, false, true, 7, -1, SoundEvents.BEACON_POWER_SELECT), wood(MapColor.COLOR_BROWN));
    public static final DeferredBlock<FurnitureBlock> TUBE_RADIO = furniture("tube_radio",
            spec(Block.box(2, 0, 5, 14, 9, 11), true, false, true, 3, -1, SoundEvents.NOTE_BLOCK_CHIME.value()), wood(MapColor.TERRACOTTA_WHITE));

    // --- Wall decor ---
    public static final DeferredBlock<FurnitureBlock> STARBURST_CLOCK = furniture("starburst_clock",
            spec(Block.box(1, 1, 15, 15, 15, 16), true, true, false, 0, -1, null), metal(MapColor.GOLD).noCollision());
    public static final DeferredBlock<FurnitureBlock> NEON_ROCKET_SIGN = furniture("neon_rocket_sign",
            spec(Block.box(2, 1, 15, 14, 15, 16), true, true, true, 10, -1, null), metal(MapColor.COLOR_PINK).noCollision());

    // --- Building blocks ---
    public static final DeferredBlock<Block> PORTHOLE_WINDOW = block("porthole_window", TransparentBlock::new,
            p -> p.mapColor(MapColor.METAL).strength(1.5F, 6.0F).sound(SoundType.METAL).noOcclusion()
                    .isValidSpawn((s, l, pos, t) -> false).isRedstoneConductor((s, l, pos) -> false)
                    .isSuffocating((s, l, pos) -> false).isViewBlocking((s, l, pos) -> false));
    public static final DeferredBlock<Block> CHECKERED_TILE = block("checkered_tile", Block::new,
            p -> p.mapColor(MapColor.QUARTZ).strength(1.5F, 6.0F).requiresCorrectToolForDrops());
    public static final DeferredBlock<Block> TURQUOISE_PANEL = block("turquoise_panel", Block::new,
            p -> p.mapColor(MapColor.COLOR_CYAN).strength(1.5F, 6.0F).requiresCorrectToolForDrops());
    public static final DeferredBlock<Block> CREAM_PANEL = block("cream_panel", Block::new,
            p -> p.mapColor(MapColor.SAND).strength(1.5F, 6.0F).requiresCorrectToolForDrops());
    public static final DeferredBlock<RotatedPillarBlock> CHROME_TRIM = block("chrome_trim", RotatedPillarBlock::new,
            p -> p.mapColor(MapColor.METAL).strength(3.0F, 6.0F).sound(SoundType.METAL).requiresCorrectToolForDrops());

    private static FurnitureSpec spec(VoxelShape shape, boolean facing, boolean wall, boolean toggle, int light, float seat,
                                      @Nullable SoundEvent sound) {
        return new FurnitureSpec(shape, facing, wall, toggle, light, seat, sound);
    }

    private static BlockBehaviour.Properties metal(MapColor color) {
        return BlockBehaviour.Properties.of().mapColor(color).strength(1.5F, 4.0F).sound(SoundType.METAL).noOcclusion();
    }

    private static BlockBehaviour.Properties soft(MapColor color) {
        return BlockBehaviour.Properties.of().mapColor(color).strength(0.8F).sound(SoundType.WOOL).noOcclusion();
    }

    private static BlockBehaviour.Properties wood(MapColor color) {
        return BlockBehaviour.Properties.of().mapColor(color).strength(1.2F).sound(SoundType.WOOD).noOcclusion();
    }

    private static DeferredBlock<FurnitureBlock> furniture(String name, FurnitureSpec spec, BlockBehaviour.Properties base) {
        int light = spec.lightOn();
        return block(name, p -> FurnitureBlock.create(p, spec),
                p -> light > 0 ? p.lightLevel(state -> FurnitureBlock.lightLevel(state, light)) : p, base);
    }

    private static <B extends Block> DeferredBlock<B> block(String name, Function<BlockBehaviour.Properties, B> factory,
                                                           UnaryOperator<BlockBehaviour.Properties> props) {
        return block(name, factory, props, BlockBehaviour.Properties.of());
    }

    private static <B extends Block> DeferredBlock<B> block(String name, Function<BlockBehaviour.Properties, B> factory,
                                                           UnaryOperator<BlockBehaviour.Properties> props,
                                                           BlockBehaviour.Properties base) {
        DeferredBlock<B> block = ModBlocks.BLOCKS.register(name, id -> factory.apply(props.apply(
                base.setId(ResourceKey.create(Registries.BLOCK, id)))));
        ITEMS.add(ModItems.ITEMS.register(name, id -> new BlockItem(block.get(),
                new Item.Properties().setId(ResourceKey.create(Registries.ITEM, id)).useBlockDescriptionPrefix())));
        return block;
    }

    /** All furniture block items, in creative tab order. */
    public static List<DeferredItem<BlockItem>> items() {
        return Collections.unmodifiableList(ITEMS);
    }

    /** Forces class loading so the entries are added to the deferred registers in time. */
    public static void init() {
    }

    private ModFurniture() {}
}
