package com.replecant.retrocosmos.ruins;

import com.replecant.retrocosmos.registry.ModBlocks;
import com.replecant.retrocosmos.registry.ModItems;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.function.Function;
import java.util.function.UnaryOperator;
import net.minecraft.ChatFormatting;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.component.ItemLore;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.RotatedPillarBlock;
import net.minecraft.world.level.block.SlabBlock;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.StairBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.properties.NoteBlockInstrument;
import net.minecraft.world.level.material.MapColor;
import net.minecraft.world.level.material.PushReaction;
import net.minecraft.world.phys.shapes.Shapes;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredItem;

/**
 * Ancient Venusian ruins: the carved stone of a long-vanished civilisation (temple bricks, glyph stones, pillars,
 * sun-disc reliefs, altars, stelae and urns) and the artifacts found in its pyramids, ziggurats, villages and
 * shrines. The structures themselves are pure data (templates, pools and processors written by tools/ruins.py).
 */
public final class ModRuins {
    private static final List<DeferredItem<? extends Item>> ITEMS = new ArrayList<>();

    // ---------------- Building stone ----------------
    public static final DeferredBlock<Block> TEMPLE_BRICKS = block("venusian_temple_bricks", Block::new, ModRuins::bricks);
    public static final DeferredBlock<Block> CRACKED_TEMPLE_BRICKS = block("venusian_cracked_temple_bricks", Block::new,
            ModRuins::bricks);
    public static final DeferredBlock<Block> MOSSY_TEMPLE_BRICKS = block("venusian_mossy_temple_bricks", Block::new,
            ModRuins::bricks);
    public static final DeferredBlock<StairBlock> TEMPLE_BRICK_STAIRS = block("venusian_temple_brick_stairs",
            p -> new StairBlock(TEMPLE_BRICKS.get().defaultBlockState(), p), ModRuins::bricks);
    public static final DeferredBlock<SlabBlock> TEMPLE_BRICK_SLAB = block("venusian_temple_brick_slab", SlabBlock::new,
            ModRuins::bricks);
    public static final DeferredBlock<Block> CARVED_STONE = block("venusian_carved_stone", Block::new, ModRuins::carved);
    public static final DeferredBlock<StairBlock> CARVED_STONE_STAIRS = block("venusian_carved_stone_stairs",
            p -> new StairBlock(CARVED_STONE.get().defaultBlockState(), p), ModRuins::carved);
    public static final DeferredBlock<SlabBlock> CARVED_STONE_SLAB = block("venusian_carved_stone_slab", SlabBlock::new,
            ModRuins::carved);
    public static final DeferredBlock<GlyphStoneBlock> GLYPH_STONE = block("venusian_glyph_stone", GlyphStoneBlock::new,
            ModRuins::carved);
    public static final DeferredBlock<Block> INLAID_STONE = block("venusian_inlaid_stone", Block::new,
            p -> carved(p).mapColor(MapColor.COLOR_CYAN));
    public static final DeferredBlock<RotatedPillarBlock> PILLAR = block("venusian_pillar", RotatedPillarBlock::new,
            ModRuins::carved);

    // ---------------- Carved furnishings ----------------
    public static final DeferredBlock<RuinFacingBlock> SUN_DISC = block("venusian_sun_disc",
            p -> new RuinFacingBlock(p, Shapes.block()),
            p -> carved(p).mapColor(MapColor.GOLD).lightLevel(s -> 12));
    public static final DeferredBlock<RuinFacingBlock> STELE = block("venusian_stele",
            p -> new RuinFacingBlock(p, Block.box(2, 0, 5, 14, 16, 11)),
            p -> carved(p).noOcclusion().pushReaction(PushReaction.BLOCK));
    public static final DeferredBlock<RuinDecorBlock> ALTAR = block("venusian_altar",
            p -> new RuinDecorBlock(p, Shapes.or(Block.box(3, 0, 3, 13, 9, 13), Block.box(1, 9, 1, 15, 13, 15))),
            p -> carved(p).noOcclusion());
    public static final DeferredBlock<RuinDecorBlock> URN = block("venusian_urn",
            p -> new RuinDecorBlock(p, Shapes.or(Block.box(3, 0, 3, 13, 10, 13), Block.box(5, 10, 5, 11, 15, 11))),
            p -> p.mapColor(MapColor.TERRACOTTA_ORANGE).instrument(NoteBlockInstrument.BASEDRUM).strength(0.8F)
                    .sound(SoundType.DECORATED_POT).noOcclusion().pushReaction(PushReaction.DESTROY));

    // ---------------- Artifacts ----------------
    public static final DeferredItem<Item> VENUSIAN_IDOL = artifact("venusian_idol", Rarity.UNCOMMON, 16, false);
    public static final DeferredItem<Item> GLYPH_TABLET = artifact("glyph_tablet", Rarity.COMMON, 16, false);
    public static final DeferredItem<Item> SUN_DISK_FRAGMENT = artifact("sun_disk_fragment", Rarity.UNCOMMON, 64, false);
    public static final DeferredItem<Item> ANCIENT_AMULET = artifact("ancient_amulet", Rarity.RARE, 1, true);

    private ModRuins() {}

    /** Called from the mod constructor before the deferred registers are attached. */
    public static void init(IEventBus modEventBus) {
    }

    /** Items for the Venus creative tab, in order. */
    public static List<DeferredItem<? extends Item>> items() {
        return Collections.unmodifiableList(ITEMS);
    }

    private static BlockBehaviour.Properties bricks(BlockBehaviour.Properties p) {
        return p.mapColor(MapColor.TERRACOTTA_CYAN).instrument(NoteBlockInstrument.BASEDRUM).requiresCorrectToolForDrops()
                .strength(2.0F, 6.0F).sound(SoundType.STONE);
    }

    private static BlockBehaviour.Properties carved(BlockBehaviour.Properties p) {
        return p.mapColor(MapColor.TERRACOTTA_YELLOW).instrument(NoteBlockInstrument.BASEDRUM).requiresCorrectToolForDrops()
                .strength(2.0F, 6.0F).sound(SoundType.STONE);
    }

    private static <B extends Block> DeferredBlock<B> block(String name, Function<BlockBehaviour.Properties, B> factory,
                                                           UnaryOperator<BlockBehaviour.Properties> props) {
        DeferredBlock<B> block = ModBlocks.BLOCKS.register(name, id -> factory.apply(props.apply(
                BlockBehaviour.Properties.of().setId(ResourceKey.create(Registries.BLOCK, id)))));
        ITEMS.add(ModItems.ITEMS.register(name, id -> new BlockItem(block.get(),
                new Item.Properties().setId(ResourceKey.create(Registries.ITEM, id)).useBlockDescriptionPrefix())));
        return block;
    }

    /** An artifact with a grey lore line ("item.retrocosmos.<name>.lore") shown in its tooltip. */
    private static DeferredItem<Item> artifact(String name, Rarity rarity, int stack, boolean glint) {
        DeferredItem<Item> item = ModItems.ITEMS.register(name, id -> {
            Item.Properties p = new Item.Properties().setId(ResourceKey.create(Registries.ITEM, id)).rarity(rarity)
                    .stacksTo(stack).component(DataComponents.LORE, new ItemLore(List.of(
                            Component.translatable("item.retrocosmos." + name + ".lore").withStyle(ChatFormatting.GRAY))));
            if (glint) {
                p.component(DataComponents.ENCHANTMENT_GLINT_OVERRIDE, true);
            }
            return new Item(p);
        });
        ITEMS.add(item);
        return item;
    }
}
