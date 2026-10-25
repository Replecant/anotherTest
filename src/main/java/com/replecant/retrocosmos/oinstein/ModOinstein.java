package com.replecant.retrocosmos.oinstein;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.furniture.FurnitureBlock;
import com.replecant.retrocosmos.furniture.FurnitureSpec;
import com.replecant.retrocosmos.registry.ModBlocks;
import com.replecant.retrocosmos.registry.ModItems;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.function.Function;
import java.util.function.UnaryOperator;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.damagesource.DamageType;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.properties.NoteBlockInstrument;
import net.minecraft.world.level.levelgen.structure.placement.StructurePlacementType;
import net.minecraft.world.level.material.MapColor;
import net.minecraft.world.level.material.PushReaction;
import net.minecraft.world.phys.shapes.Shapes;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * Dr. Oinstein, the mad scientist of Venus: the laser barrier that seals his Institute, the steel and lab fittings of
 * his outposts, his propaganda posters, the laser damage type and the structure placement that keeps his bases (and
 * the ruins) apart. The structures themselves are data written by tools/oinstein.py.
 */
public final class ModOinstein {
    private static final List<DeferredItem<? extends Item>> ITEMS = new ArrayList<>();

    public static final DeferredRegister<StructurePlacementType<?>> PLACEMENTS =
            DeferredRegister.create(Registries.STRUCTURE_PLACEMENT, RetroCosmos.MODID);
    public static final DeferredHolder<StructurePlacementType<?>, StructurePlacementType<ExclusiveSpreadPlacement>> EXCLUSIVE_SPREAD =
            PLACEMENTS.register("exclusive_spread", () -> ExclusiveSpreadPlacement.TYPE);

    public static final ResourceKey<DamageType> LASER_DAMAGE = ResourceKey.create(Registries.DAMAGE_TYPE,
            Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "laser"));

    // ---------------- The laser barrier ----------------
    public static final DeferredBlock<LaserBarrierBlock> LASER_BARRIER = block("laser_barrier", LaserBarrierBlock::new,
            p -> unbreakable(p).mapColor(MapColor.COLOR_RED).sound(SoundType.AMETHYST).noOcclusion()
                    .lightLevel(s -> s.getValue(LaserBarrierBlock.POWERED) ? 9 : 0)
                    .emissiveRendering((s, l, pos) -> s.getValue(LaserBarrierBlock.POWERED))
                    .isValidSpawn((s, l, pos, t) -> false).isRedstoneConductor((s, l, pos) -> false)
                    .isSuffocating((s, l, pos) -> false).isViewBlocking((s, l, pos) -> false));
    public static final DeferredBlock<LaserEmitterBlock> LASER_EMITTER = block("laser_emitter", LaserEmitterBlock::new,
            p -> unbreakable(p).mapColor(MapColor.COLOR_GRAY).sound(SoundType.METAL).noOcclusion()
                    .lightLevel(s -> s.getValue(LaserEmitterBlock.POWERED) ? 7 : 0));

    // ---------------- Steel and lab fittings ----------------
    public static final DeferredBlock<Block> RIVETED_STEEL = block("oinstein_riveted_steel", Block::new, ModOinstein::steel);
    public static final DeferredBlock<Block> HAZARD_STEEL = block("oinstein_hazard_steel", Block::new,
            p -> steel(p).mapColor(MapColor.COLOR_YELLOW));
    public static final DeferredBlock<TeslaCoilBlock> TESLA_COIL = block("tesla_coil",
            p -> new TeslaCoilBlock(p, Shapes.or(Block.box(4, 0, 4, 12, 4, 12), Block.box(6, 4, 6, 10, 12, 10),
                    Block.box(3, 12, 3, 13, 16, 13)), true),
            p -> steel(p).mapColor(MapColor.COLOR_ORANGE).noOcclusion().lightLevel(s -> 9));
    public static final DeferredBlock<TeslaCoilBlock> BRAIN_JAR = block("brain_jar",
            p -> new TeslaCoilBlock(p, Block.box(4, 0, 4, 12, 14, 12), false),
            p -> p.mapColor(MapColor.COLOR_LIGHT_GREEN).strength(0.5F).sound(SoundType.GLASS).noOcclusion().lightLevel(s -> 6)
                    .isRedstoneConductor((s, l, pos) -> false).isViewBlocking((s, l, pos) -> false));

    // ---------------- Propaganda posters (two blocks tall, hang on a wall) ----------------
    public static final DeferredBlock<FurnitureBlock> POSTER_INSIGNIA = poster("oinstein_poster_insignia");
    public static final DeferredBlock<FurnitureBlock> POSTER_BETTER_APE = poster("oinstein_poster_better_ape");
    public static final DeferredBlock<FurnitureBlock> POSTER_RESTRICTED = poster("oinstein_poster_restricted");

    private ModOinstein() {}

    public static void init(IEventBus modEventBus) {
        PLACEMENTS.register(modEventBus);
    }

    /** Items for the Venus creative tab, in order. */
    public static List<DeferredItem<? extends Item>> items() {
        return Collections.unmodifiableList(ITEMS);
    }

    private static BlockBehaviour.Properties unbreakable(BlockBehaviour.Properties p) {
        return p.strength(-1.0F, 3600000.0F).noLootTable().pushReaction(PushReaction.BLOCK);
    }

    private static BlockBehaviour.Properties steel(BlockBehaviour.Properties p) {
        return p.mapColor(MapColor.COLOR_GRAY).instrument(NoteBlockInstrument.IRON_XYLOPHONE).requiresCorrectToolForDrops()
                .strength(5.0F, 6.0F).sound(SoundType.METAL);
    }

    private static DeferredBlock<FurnitureBlock> poster(String name) {
        FurnitureSpec spec = new FurnitureSpec(Block.box(1, 0, 15, 15, 16, 16), true, true, false, 0, -1, null).asTall();
        return block(name, p -> FurnitureBlock.create(p, spec),
                p -> p.mapColor(MapColor.WOOL).strength(0.5F).sound(SoundType.WOOL).noOcclusion().noCollision());
    }

    private static <B extends Block> DeferredBlock<B> block(String name, Function<BlockBehaviour.Properties, B> factory,
                                                           UnaryOperator<BlockBehaviour.Properties> props) {
        DeferredBlock<B> block = ModBlocks.BLOCKS.register(name, id -> factory.apply(props.apply(
                BlockBehaviour.Properties.of().setId(ResourceKey.create(Registries.BLOCK, id)))));
        ITEMS.add(ModItems.ITEMS.register(name, id -> new BlockItem(block.get(),
                new Item.Properties().setId(ResourceKey.create(Registries.ITEM, id)).useBlockDescriptionPrefix())));
        return block;
    }
}
