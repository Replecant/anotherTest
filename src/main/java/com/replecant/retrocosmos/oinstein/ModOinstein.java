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
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.tags.TagKey;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.SpawnPlacementTypes;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.structure.StructureType;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePieceType;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureProcessorType;
import net.minecraft.ChatFormatting;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.component.ItemLore;
import net.neoforged.neoforge.event.entity.RegisterSpawnPlacementsEvent;
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

    public static final DeferredRegister<StructureType<?>> STRUCTURE_TYPES =
            DeferredRegister.create(Registries.STRUCTURE_TYPE, RetroCosmos.MODID);
    public static final DeferredHolder<StructureType<?>, StructureType<DryJigsawStructure>> DRY_JIGSAW =
            STRUCTURE_TYPES.register("dry_jigsaw", () -> DryJigsawStructure.TYPE);

    public static final DeferredRegister<StructurePieceType> STRUCTURE_PIECES =
            DeferredRegister.create(Registries.STRUCTURE_PIECE, RetroCosmos.MODID);
    public static final DeferredHolder<StructurePieceType, StructurePieceType> ATTACHED_TEMPLATE =
            STRUCTURE_PIECES.register("attached_template",
                    () -> (StructurePieceType.StructureTemplateType) AttachedTemplatePiece::new);

    public static final DeferredRegister<StructureProcessorType<?>> PROCESSORS =
            DeferredRegister.create(Registries.STRUCTURE_PROCESSOR, RetroCosmos.MODID);
    public static final DeferredHolder<StructureProcessorType<?>, StructureProcessorType<FurnitureFacingProcessor>> FURNITURE_FACING =
            PROCESSORS.register("furniture_facing", () -> FurnitureFacingProcessor.TYPE);

    /** Dr. Oinstein's mutants and robots (entity type tag, data from the mob packages). */
    public static final TagKey<EntityType<?>> FORCES = TagKey.create(Registries.ENTITY_TYPE,
            Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "oinstein_forces"));

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

    // ---------------- Security clearance: the reader beside each barrier and its three cards ----------------
    public static final DeferredBlock<KeycardReaderBlock> KEYCARD_READER = block("keycard_reader", KeycardReaderBlock::new,
            p -> unbreakable(p).mapColor(MapColor.METAL).sound(SoundType.METAL).noOcclusion()
                    .lightLevel(s -> s.getValue(KeycardReaderBlock.STATUS) == KeycardReaderBlock.Status.LOCKED ? 4 : 8)
                    .isRedstoneConductor((s, l, pos) -> false));
    public static final DeferredItem<KeycardItem> KEYCARD_ALPHA = keycard(KeycardReaderBlock.Clearance.A, Rarity.UNCOMMON);
    public static final DeferredItem<KeycardItem> KEYCARD_BETA = keycard(KeycardReaderBlock.Clearance.B, Rarity.UNCOMMON);
    public static final DeferredItem<KeycardItem> KEYCARD_GAMMA = keycard(KeycardReaderBlock.Clearance.C, Rarity.RARE);

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
        STRUCTURE_TYPES.register(modEventBus);
        STRUCTURE_PIECES.register(modEventBus);
        PROCESSORS.register(modEventBus);
        modEventBus.addListener(ModOinstein::registerSpawnPlacements);
    }

    /** The four Oinstein mobs share {@link OinsteinSpawns#check} (also set where the mutants are registered). */
    private static void registerSpawnPlacements(RegisterSpawnPlacementsEvent event) {
        for (String name : new String[] {"atomic_sentry", "atomic_automaton", "hominid_novus", "hominus_sapiens"}) {
            BuiltInRegistries.ENTITY_TYPE.getOptional(Identifier.fromNamespaceAndPath(RetroCosmos.MODID, name))
                    .ifPresent(type -> register(event, type));
        }
    }

    private static <T extends Entity> void register(RegisterSpawnPlacementsEvent event, EntityType<T> type) {
        event.register(type, SpawnPlacementTypes.ON_GROUND, Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, OinsteinSpawns::check,
                RegisterSpawnPlacementsEvent.Operation.REPLACE);
    }

    /** Items for the Venus creative tab, in order. */
    public static List<DeferredItem<? extends Item>> items() {
        return Collections.unmodifiableList(ITEMS);
    }

    /** A security card: stacks to one, never used up; a grey lore line names the barrier it opens. */
    private static DeferredItem<KeycardItem> keycard(KeycardReaderBlock.Clearance clearance, Rarity rarity) {
        String name = clearance.card();
        DeferredItem<KeycardItem> item = ModItems.ITEMS.register(name, id -> new KeycardItem(new Item.Properties()
                .setId(ResourceKey.create(Registries.ITEM, id)).stacksTo(1).rarity(rarity)
                .component(DataComponents.LORE, new ItemLore(List.of(Component.translatable("item.retrocosmos." + name + ".lore")
                        .withStyle(ChatFormatting.GRAY)))), clearance));
        ITEMS.add(item);
        return item;
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
