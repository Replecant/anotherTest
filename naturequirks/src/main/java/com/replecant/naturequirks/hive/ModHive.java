package com.replecant.naturequirks.hive;

import com.replecant.naturequirks.NatureQuirks;
import com.replecant.naturequirks.registry.ModTab;
import java.util.function.Function;
import java.util.function.UnaryOperator;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.food.FoodProperties;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.BucketItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.LiquidBlock;
import net.minecraft.world.level.block.SlabBlock;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.StairBlock;
import net.minecraft.world.level.block.TransparentBlock;
import net.minecraft.world.level.block.WallBlock;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.properties.NoteBlockInstrument;
import net.minecraft.world.level.levelgen.structure.StructureType;
import net.minecraft.world.level.material.Fluid;
import net.minecraft.world.level.material.MapColor;
import net.minecraft.world.level.material.PushReaction;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.common.SoundActions;
import net.neoforged.neoforge.fluids.BaseFlowingFluid;
import net.neoforged.neoforge.fluids.FluidType;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;
import net.neoforged.neoforge.registries.NeoForgeRegistries;

/**
 * Giant wild beehives: the comb, brick and royal-jelly blocks, the Hive Heart that calls guardian bees, honey as a
 * fluid (and its bucket), the honey cookie and the honey cake, and the hive structure type. Assets and data are
 * written by tools/giant_hive.py.
 */
public final class ModHive {
    public static final DeferredRegister.Blocks BLOCKS = DeferredRegister.createBlocks(NatureQuirks.MODID);
    public static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(NatureQuirks.MODID);
    public static final DeferredRegister<FluidType> FLUID_TYPES = DeferredRegister.create(NeoForgeRegistries.Keys.FLUID_TYPES, NatureQuirks.MODID);
    public static final DeferredRegister<Fluid> FLUIDS = DeferredRegister.create(Registries.FLUID, NatureQuirks.MODID);
    public static final DeferredRegister<BlockEntityType<?>> BLOCK_ENTITIES = DeferredRegister.create(Registries.BLOCK_ENTITY_TYPE, NatureQuirks.MODID);
    public static final DeferredRegister<StructureType<?>> STRUCTURE_TYPES = DeferredRegister.create(Registries.STRUCTURE_TYPE, NatureQuirks.MODID);

    // ---------------- honey, the fluid ----------------
    public static final DeferredHolder<FluidType, FluidType> HONEY_TYPE = FLUID_TYPES.register("honey", () -> new HoneyFluidType(
            FluidType.Properties.create().descriptionId("fluid_type.naturequirks.honey").density(3000).viscosity(12000)
                    .motionScale(0.002).canSwim(false).canDrown(true).canPushEntity(true).fallDistanceModifier(0.0F)
                    .canExtinguish(true).canConvertToSource(false).supportsBoating(false).canHydrate(false)
                    .sound(SoundActions.BUCKET_FILL, SoundEvents.BOTTLE_FILL).sound(SoundActions.BUCKET_EMPTY, SoundEvents.HONEY_BLOCK_PLACE)));
    public static final DeferredHolder<Fluid, BaseFlowingFluid.Source> HONEY = FLUIDS.register("honey",
            () -> new BaseFlowingFluid.Source(fluidProperties()));
    public static final DeferredHolder<Fluid, BaseFlowingFluid.Flowing> FLOWING_HONEY = FLUIDS.register("flowing_honey",
            () -> new BaseFlowingFluid.Flowing(fluidProperties()));
    public static final DeferredBlock<LiquidBlock> HONEY_BLOCK = BLOCKS.register("honey", id -> new LiquidBlock(HONEY.get(),
            BlockBehaviour.Properties.of().setId(ResourceKey.create(Registries.BLOCK, id)).mapColor(MapColor.COLOR_ORANGE).replaceable()
                    .noCollision().strength(100.0F).pushReaction(PushReaction.DESTROY).noLootTable().liquid().sound(SoundType.EMPTY)));
    public static final DeferredItem<BucketItem> HONEY_BUCKET = ITEMS.register("honey_bucket", id -> new BucketItem(HONEY.get(),
            new Item.Properties().setId(ResourceKey.create(Registries.ITEM, id)).craftRemainder(Items.BUCKET).stacksTo(1)));

    // ---------------- comb and wax ----------------
    public static final DeferredBlock<Block> WILD_COMB = block("wild_comb", Block::new, ModHive::comb);
    public static final DeferredBlock<DrippingCombBlock> DRIPPING_COMB = block("dripping_comb", DrippingCombBlock::new, ModHive::comb);
    public static final DeferredBlock<Block> HONEYCOMB_BRICKS = block("honeycomb_bricks", Block::new, ModHive::bricks);
    public static final DeferredBlock<StairBlock> HONEYCOMB_BRICK_STAIRS = block("honeycomb_brick_stairs",
            p -> new StairBlock(HONEYCOMB_BRICKS.get().defaultBlockState(), p), ModHive::bricks);
    public static final DeferredBlock<SlabBlock> HONEYCOMB_BRICK_SLAB = block("honeycomb_brick_slab", SlabBlock::new, ModHive::bricks);
    public static final DeferredBlock<WallBlock> HONEYCOMB_BRICK_WALL = block("honeycomb_brick_wall", WallBlock::new,
            p -> bricks(p).forceSolidOn());
    public static final DeferredBlock<TransparentBlock> COMB_WINDOW = block("comb_window", TransparentBlock::new,
            p -> p.mapColor(MapColor.COLOR_ORANGE).strength(0.5F).sound(SoundType.CORAL_BLOCK).noOcclusion()
                    .isValidSpawn((s, l, pos, t) -> false).isRedstoneConductor((s, l, pos) -> false)
                    .isSuffocating((s, l, pos) -> false).isViewBlocking((s, l, pos) -> false));
    public static final DeferredBlock<Block> ROYAL_JELLY = block("royal_jelly", Block::new,
            p -> p.mapColor(MapColor.TERRACOTTA_WHITE).strength(0.5F).sound(SoundType.HONEY_BLOCK).lightLevel(s -> 9));
    public static final DeferredBlock<HiveHeartBlock> HIVE_HEART = block("hive_heart", HiveHeartBlock::new,
            p -> p.mapColor(MapColor.COLOR_ORANGE).strength(3.0F, 6.0F).sound(SoundType.HONEY_BLOCK).lightLevel(s -> 11));
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<HiveHeartBlockEntity>> HIVE_HEART_BE =
            BLOCK_ENTITIES.register("hive_heart", () -> new BlockEntityType<>(HiveHeartBlockEntity::new, HIVE_HEART.get()));

    // ---------------- food ----------------
    public static final DeferredItem<Item> HONEY_COOKIE = ITEMS.register("honey_cookie", id -> new Item(new Item.Properties()
            .setId(ResourceKey.create(Registries.ITEM, id))
            .food(new FoodProperties.Builder().nutrition(3).saturationModifier(0.25F).build())));
    public static final DeferredBlock<HoneyCakeBlock> HONEY_CAKE = BLOCKS.register("honey_cake", id -> new HoneyCakeBlock(
            BlockBehaviour.Properties.of().setId(ResourceKey.create(Registries.BLOCK, id)).mapColor(MapColor.COLOR_ORANGE)
                    .forceSolidOn().strength(0.5F).sound(SoundType.WOOL).pushReaction(PushReaction.DESTROY)));
    public static final DeferredItem<BlockItem> HONEY_CAKE_ITEM = ITEMS.register("honey_cake", id -> new BlockItem(HONEY_CAKE.get(),
            new Item.Properties().setId(ResourceKey.create(Registries.ITEM, id)).stacksTo(1).useBlockDescriptionPrefix()));

    // ---------------- worldgen ----------------
    public static final DeferredHolder<StructureType<?>, StructureType<DryJigsawStructure>> DRY_JIGSAW =
            STRUCTURE_TYPES.register("dry_jigsaw", () -> DryJigsawStructure.TYPE);

    private ModHive() {}

    public static void init(IEventBus modEventBus) {
        BLOCKS.register(modEventBus);
        ITEMS.register(modEventBus);
        FLUID_TYPES.register(modEventBus);
        FLUIDS.register(modEventBus);
        BLOCK_ENTITIES.register(modEventBus);
        STRUCTURE_TYPES.register(modEventBus);
        NeoForge.EVENT_BUS.register(HiveEvents.class);
        ModTab.icon = HONEY_BUCKET;
        for (var item : new java.util.function.Supplier<?>[] {WILD_COMB, DRIPPING_COMB, HONEYCOMB_BRICKS, HONEYCOMB_BRICK_STAIRS,
                HONEYCOMB_BRICK_SLAB, HONEYCOMB_BRICK_WALL, COMB_WINDOW, ROYAL_JELLY, HIVE_HEART, HONEY_BUCKET, HONEY_COOKIE,
                HONEY_CAKE_ITEM}) {
            ModTab.add(() -> (net.minecraft.world.level.ItemLike) item.get());
        }
    }

    private static BaseFlowingFluid.Properties fluidProperties() {
        // slow (lava-like tick rate), short spread: honey creeps a few blocks and stops
        return new BaseFlowingFluid.Properties(HONEY_TYPE, HONEY, FLOWING_HONEY).bucket(HONEY_BUCKET).block(HONEY_BLOCK)
                .tickRate(30).slopeFindDistance(2).levelDecreasePerBlock(2).explosionResistance(100.0F);
    }

    private static BlockBehaviour.Properties comb(BlockBehaviour.Properties p) {
        return p.mapColor(MapColor.COLOR_ORANGE).strength(0.6F).sound(SoundType.CORAL_BLOCK);
    }

    private static BlockBehaviour.Properties bricks(BlockBehaviour.Properties p) {
        return p.mapColor(MapColor.COLOR_ORANGE).instrument(NoteBlockInstrument.BASEDRUM).strength(1.5F, 3.0F).sound(SoundType.CORAL_BLOCK);
    }

    private static <B extends Block> DeferredBlock<B> block(String name, Function<BlockBehaviour.Properties, B> factory,
                                                           UnaryOperator<BlockBehaviour.Properties> props) {
        DeferredBlock<B> block = BLOCKS.register(name, id -> factory.apply(props.apply(
                BlockBehaviour.Properties.of().setId(ResourceKey.create(Registries.BLOCK, id)))));
        ITEMS.register(name, id -> new BlockItem(block.get(), new Item.Properties().setId(ResourceKey.create(Registries.ITEM, id))
                .useBlockDescriptionPrefix()));
        return block;
    }
}
