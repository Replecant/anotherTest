package com.replecant.retrocosmos.venus;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.registry.ModBlocks;
import com.replecant.retrocosmos.registry.ModItems;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Set;
import java.util.function.BiFunction;
import java.util.function.Function;
import java.util.function.UnaryOperator;
import net.minecraft.core.particles.ColorParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.DoubleHighBlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HugeMushroomBlock;
import net.minecraft.world.level.block.RotatedPillarBlock;
import net.minecraft.world.level.block.SlabBlock;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.StairBlock;
import net.minecraft.world.level.block.UntintedParticleLeavesBlock;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.properties.NoteBlockInstrument;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.configurations.NoneFeatureConfiguration;
import net.minecraft.world.level.material.MapColor;
import net.minecraft.world.level.material.PushReaction;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * Venus blocks and items (registered into the mod's shared deferred registers), plus the few Venus-only
 * registries: the fumarole block entity and the cinder-cone world-gen feature.
 */
public final class ModVenus {
    private static final List<DeferredItem<? extends Item>> ITEMS = new ArrayList<>();

    public static final DeferredRegister<BlockEntityType<?>> BLOCK_ENTITIES =
            DeferredRegister.create(Registries.BLOCK_ENTITY_TYPE, RetroCosmos.MODID);
    public static final DeferredRegister<Feature<?>> FEATURES = DeferredRegister.create(Registries.FEATURE, RetroCosmos.MODID);

    // ---------------- Rock & soil ----------------
    public static final DeferredBlock<Block> VENUS_STONE = block("venus_stone", Block::new,
            p -> p.mapColor(MapColor.TERRACOTTA_PURPLE).instrument(NoteBlockInstrument.BASEDRUM).requiresCorrectToolForDrops()
                    .strength(1.5F, 6.0F));
    public static final DeferredBlock<Block> VENUS_COBBLESTONE = block("venus_cobblestone", Block::new,
            p -> p.mapColor(MapColor.TERRACOTTA_PURPLE).instrument(NoteBlockInstrument.BASEDRUM).requiresCorrectToolForDrops()
                    .strength(2.0F, 6.0F));
    public static final DeferredBlock<Block> VENUS_STONE_BRICKS = block("venus_stone_bricks", Block::new,
            p -> p.mapColor(MapColor.TERRACOTTA_PURPLE).instrument(NoteBlockInstrument.BASEDRUM).requiresCorrectToolForDrops()
                    .strength(1.5F, 6.0F));
    public static final DeferredBlock<Block> VENUS_BLACK_ROCK = block("venus_black_rock", Block::new,
            p -> p.mapColor(MapColor.COLOR_BLACK).instrument(NoteBlockInstrument.BASEDRUM).requiresCorrectToolForDrops()
                    .strength(1.25F, 4.2F).sound(SoundType.BASALT));
    public static final DeferredBlock<FumaroleBlock> VENUS_FUMAROLE = block("venus_fumarole", FumaroleBlock::new,
            p -> p.mapColor(MapColor.COLOR_BLACK).instrument(NoteBlockInstrument.BASEDRUM).requiresCorrectToolForDrops()
                    .strength(1.25F, 4.2F).sound(SoundType.BASALT).lightLevel(s -> 7)
                    .emissiveRendering((s, l, pos) -> true));
    public static final DeferredBlock<Block> VENUS_MUD = block("venus_mud", Block::new,
            p -> p.mapColor(MapColor.TERRACOTTA_BROWN).strength(0.5F).sound(SoundType.MUD).speedFactor(0.8F));
    public static final DeferredBlock<Block> VENUS_SOIL = block("venus_soil", Block::new,
            p -> p.mapColor(MapColor.DIRT).strength(0.5F).sound(SoundType.ROOTED_DIRT));
    public static final DeferredBlock<Block> VENUS_MOSS = block("venus_moss", Block::new,
            p -> p.mapColor(MapColor.WARPED_NYLIUM).strength(0.6F).sound(SoundType.MOSS));
    public static final DeferredBlock<TarBlock> VENUS_TAR = block("venus_tar", TarBlock::new,
            p -> p.mapColor(MapColor.COLOR_BLACK).strength(0.6F).sound(SoundType.HONEY_BLOCK).speedFactor(0.3F).jumpFactor(0.4F));

    // ---------------- Giant jungle tree ----------------
    public static final DeferredBlock<RotatedPillarBlock> VENUS_LOG = block("venus_log", RotatedPillarBlock::new,
            p -> p.mapColor(s -> MapColor.TERRACOTTA_BROWN).instrument(NoteBlockInstrument.BASS).strength(2.0F)
                    .sound(SoundType.WOOD).ignitedByLava());
    public static final DeferredBlock<RotatedPillarBlock> VENUS_WOOD = block("venus_wood", RotatedPillarBlock::new,
            p -> p.mapColor(MapColor.TERRACOTTA_BROWN).instrument(NoteBlockInstrument.BASS).strength(2.0F)
                    .sound(SoundType.WOOD).ignitedByLava());
    public static final DeferredBlock<Block> VENUS_PLANKS = block("venus_planks", Block::new,
            p -> p.mapColor(MapColor.TERRACOTTA_ORANGE).instrument(NoteBlockInstrument.BASS).strength(2.0F, 3.0F)
                    .sound(SoundType.WOOD).ignitedByLava());
    public static final DeferredBlock<StairBlock> VENUS_STAIRS = block("venus_stairs",
            p -> new StairBlock(VENUS_PLANKS.get().defaultBlockState(), p),
            p -> p.mapColor(MapColor.TERRACOTTA_ORANGE).instrument(NoteBlockInstrument.BASS).strength(2.0F, 3.0F)
                    .sound(SoundType.WOOD).ignitedByLava());
    public static final DeferredBlock<SlabBlock> VENUS_SLAB = block("venus_slab", SlabBlock::new,
            p -> p.mapColor(MapColor.TERRACOTTA_ORANGE).instrument(NoteBlockInstrument.BASS).strength(2.0F, 3.0F)
                    .sound(SoundType.WOOD).ignitedByLava());
    public static final DeferredBlock<UntintedParticleLeavesBlock> VENUS_LEAVES = block("venus_leaves",
            p -> new UntintedParticleLeavesBlock(0.01F, ColorParticleOption.create(ParticleTypes.TINTED_LEAVES, 0xFF3F7A5C), p),
            p -> p.mapColor(MapColor.WARPED_NYLIUM).strength(0.2F).randomTicks().sound(SoundType.AZALEA_LEAVES).noOcclusion()
                    .isValidSpawn((s, l, pos, t) -> false).isSuffocating((s, l, pos) -> false)
                    .isViewBlocking((s, l, pos) -> false).ignitedByLava().pushReaction(PushReaction.DESTROY)
                    .isRedstoneConductor((s, l, pos) -> false));

    public static final DeferredBlock<UntintedParticleLeavesBlock> VENUS_AMBER_LEAVES = block("venus_amber_leaves",
            p -> new UntintedParticleLeavesBlock(0.02F, ColorParticleOption.create(ParticleTypes.TINTED_LEAVES, 0xFFC0782E), p),
            p -> p.mapColor(MapColor.TERRACOTTA_ORANGE).strength(0.2F).randomTicks().sound(SoundType.AZALEA_LEAVES).noOcclusion()
                    .isValidSpawn((s, l, pos, t) -> false).isSuffocating((s, l, pos) -> false)
                    .isViewBlocking((s, l, pos) -> false).ignitedByLava().pushReaction(PushReaction.DESTROY)
                    .isRedstoneConductor((s, l, pos) -> false));

    // ---------------- Plants ----------------
    public static final DeferredBlock<VenusPlantBlock> VENUS_SEDGE = block("venus_sedge",
            p -> new VenusPlantBlock(p, Block.box(2, 0, 2, 14, 12, 14), false), ModVenus::grassy);
    public static final DeferredBlock<VenusPlantBlock> VENUS_HORSETAIL = block("venus_horsetail",
            p -> new VenusPlantBlock(p, Block.box(3, 0, 3, 13, 16, 13), false), ModVenus::grassy);
    public static final DeferredBlock<VenusPlantBlock> VENUS_CYCAD = block("venus_cycad",
            p -> new VenusPlantBlock(p, Block.box(3, 0, 3, 13, 15, 13), false),
            p -> p.mapColor(MapColor.PLANT).noCollision().instabreak().sound(SoundType.AZALEA).offsetType(BlockBehaviour.OffsetType.XZ)
                    .ignitedByLava().pushReaction(PushReaction.DESTROY));
    public static final DeferredBlock<VenusPlantBlock> VENUS_FIRE_LILY = block("venus_fire_lily",
            p -> new VenusPlantBlock(p, Block.box(4, 0, 4, 12, 13, 12), false), ModVenus::grassy);
    public static final DeferredBlock<VenusTallPlantBlock> VENUS_TREE_FERN = doubleBlock("venus_tree_fern",
            p -> new VenusTallPlantBlock(p, Block.box(4, 0, 4, 12, 16, 12), false),
            p -> p.mapColor(MapColor.PLANT).noCollision().instabreak().sound(SoundType.AZALEA).offsetType(BlockBehaviour.OffsetType.XZ)
                    .ignitedByLava().pushReaction(PushReaction.DESTROY));
    public static final DeferredBlock<VenusTallPlantBlock> VENUS_GIANT_FERN = doubleBlock("venus_giant_fern",
            p -> new VenusTallPlantBlock(p, Block.box(2, 0, 2, 14, 16, 14), false), ModVenus::grassy);
    public static final DeferredBlock<HangingVinesBlock> VENUS_HANGING_VINES = block("venus_hanging_vines", HangingVinesBlock::new,
            p -> p.mapColor(MapColor.PLANT).noCollision().instabreak().sound(SoundType.CAVE_VINES).ignitedByLava()
                    .pushReaction(PushReaction.DESTROY));

    // ---------------- Fungi ----------------
    public static final DeferredBlock<VenusPlantBlock> VENUS_GLOWCAP = block("venus_glowcap",
            p -> new VenusPlantBlock(p, Block.box(4, 0, 4, 12, 9, 12), true),
            p -> p.mapColor(MapColor.COLOR_LIGHT_BLUE).noCollision().instabreak().sound(SoundType.FUNGUS)
                    .lightLevel(s -> 10).emissiveRendering((s, l, pos) -> true).offsetType(BlockBehaviour.OffsetType.XZ)
                    .pushReaction(PushReaction.DESTROY));
    public static final DeferredBlock<VenusTallPlantBlock> VENUS_GLOWSTALK = doubleBlock("venus_glowstalk",
            p -> new VenusTallPlantBlock(p, Block.box(3, 0, 3, 13, 16, 13), true),
            p -> p.mapColor(MapColor.COLOR_CYAN).noCollision().instabreak().sound(SoundType.FUNGUS)
                    .lightLevel(s -> 12).emissiveRendering((s, l, pos) -> true).offsetType(BlockBehaviour.OffsetType.XZ)
                    .pushReaction(PushReaction.DESTROY));
    public static final DeferredBlock<HugeMushroomBlock> VENUS_GLOWCAP_BLOCK = block("venus_glowcap_block", HugeMushroomBlock::new,
            p -> p.mapColor(MapColor.COLOR_LIGHT_BLUE).instrument(NoteBlockInstrument.BASS).strength(0.2F).sound(SoundType.FUNGUS)
                    .lightLevel(s -> 12).ignitedByLava());
    public static final DeferredBlock<HugeMushroomBlock> VENUS_GLOWCAP_STEM = block("venus_glowcap_stem", HugeMushroomBlock::new,
            p -> p.mapColor(MapColor.TERRACOTTA_WHITE).instrument(NoteBlockInstrument.BASS).strength(0.2F).sound(SoundType.STEM)
                    .ignitedByLava());

    // ---------------- Block entity & world-gen feature ----------------
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<FumaroleBlockEntity>> FUMAROLE_BE =
            BLOCK_ENTITIES.register("venus_fumarole", () -> new BlockEntityType<>(FumaroleBlockEntity::new, Set.of(VENUS_FUMAROLE.get())));
    public static final DeferredHolder<Feature<?>, CinderConeFeature> CINDER_CONE =
            FEATURES.register("cinder_cone", () -> new CinderConeFeature(NoneFeatureConfiguration.CODEC));
    public static final DeferredHolder<Feature<?>, HotSpringFeature> HOT_SPRING =
            FEATURES.register("hot_spring", () -> new HotSpringFeature(NoneFeatureConfiguration.CODEC));

    private ModVenus() {}

    /** Called from the mod constructor before the deferred registers are attached. */
    public static void init(IEventBus modEventBus) {
        BLOCK_ENTITIES.register(modEventBus);
        FEATURES.register(modEventBus);
    }

    /** Items for the Venus creative tab, in order. */
    public static List<DeferredItem<? extends Item>> items() {
        return Collections.unmodifiableList(ITEMS);
    }

    private static BlockBehaviour.Properties grassy(BlockBehaviour.Properties p) {
        return p.mapColor(MapColor.PLANT).replaceable().noCollision().instabreak().sound(SoundType.GRASS)
                .offsetType(BlockBehaviour.OffsetType.XZ).ignitedByLava().pushReaction(PushReaction.DESTROY);
    }

    private static <B extends Block> DeferredBlock<B> block(String name, Function<BlockBehaviour.Properties, B> factory,
                                                           UnaryOperator<BlockBehaviour.Properties> props) {
        return register(name, factory, props, BlockItem::new);
    }

    private static <B extends Block> DeferredBlock<B> doubleBlock(String name, Function<BlockBehaviour.Properties, B> factory,
                                                                 UnaryOperator<BlockBehaviour.Properties> props) {
        return register(name, factory, props, DoubleHighBlockItem::new);
    }

    private static <B extends Block> DeferredBlock<B> register(String name, Function<BlockBehaviour.Properties, B> factory,
                                                              UnaryOperator<BlockBehaviour.Properties> props,
                                                              BiFunction<Block, Item.Properties, ? extends BlockItem> item) {
        DeferredBlock<B> block = ModBlocks.BLOCKS.register(name, id -> factory.apply(props.apply(
                BlockBehaviour.Properties.of().setId(ResourceKey.create(Registries.BLOCK, id)))));
        ITEMS.add(ModItems.ITEMS.register(name, id -> item.apply(block.get(),
                new Item.Properties().setId(ResourceKey.create(Registries.ITEM, id)).useBlockDescriptionPrefix())));
        return block;
    }
}
