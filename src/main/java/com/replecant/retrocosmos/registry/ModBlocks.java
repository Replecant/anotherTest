package com.replecant.retrocosmos.registry;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.block.LaunchPadBlock;
import com.replecant.retrocosmos.block.RocketBlock;
import com.replecant.retrocosmos.block.ServiceTowerBlock;
import com.replecant.retrocosmos.console.ConsoleBlock;
import com.replecant.retrocosmos.machine.MachineKind;
import com.replecant.retrocosmos.machine.ProcessingBlock;
import java.util.function.Function;
import java.util.function.UnaryOperator;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.util.valueproviders.UniformInt;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.DropExperienceBlock;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.minecraft.world.level.material.PushReaction;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredRegister;

public final class ModBlocks {
    public static final DeferredRegister.Blocks BLOCKS = DeferredRegister.createBlocks(RetroCosmos.MODID);

    // --- Ores ---
    public static final DeferredBlock<Block> BAUXITE_ORE = register("bauxite_ore",
            p -> new DropExperienceBlock(UniformInt.of(0, 2), p),
            p -> p.mapColor(MapColor.STONE).requiresCorrectToolForDrops().strength(3.0F, 3.0F));
    public static final DeferredBlock<Block> DEEPSLATE_BAUXITE_ORE = register("deepslate_bauxite_ore",
            p -> new DropExperienceBlock(UniformInt.of(0, 2), p),
            p -> p.mapColor(MapColor.DEEPSLATE).requiresCorrectToolForDrops().strength(4.5F, 3.0F).sound(SoundType.DEEPSLATE));
    public static final DeferredBlock<Block> TITANIUM_ORE = register("titanium_ore",
            p -> new DropExperienceBlock(UniformInt.of(1, 3), p),
            p -> p.mapColor(MapColor.STONE).requiresCorrectToolForDrops().strength(3.5F, 3.0F));
    public static final DeferredBlock<Block> DEEPSLATE_TITANIUM_ORE = register("deepslate_titanium_ore",
            p -> new DropExperienceBlock(UniformInt.of(1, 3), p),
            p -> p.mapColor(MapColor.DEEPSLATE).requiresCorrectToolForDrops().strength(5.0F, 3.0F).sound(SoundType.DEEPSLATE));

    public static final DeferredBlock<Block> OIL_SHALE = register("oil_shale",
            p -> new DropExperienceBlock(UniformInt.of(0, 1), p),
            p -> p.mapColor(MapColor.COLOR_BLACK).requiresCorrectToolForDrops().strength(2.5F, 3.0F));

    // --- Storage blocks ---
    public static final DeferredBlock<Block> ALUMINUM_BLOCK = register("aluminum_block", Block::new,
            p -> p.mapColor(MapColor.METAL).requiresCorrectToolForDrops().strength(4.0F, 6.0F).sound(SoundType.METAL));
    public static final DeferredBlock<Block> TITANIUM_BLOCK = register("titanium_block", Block::new,
            p -> p.mapColor(MapColor.METAL).requiresCorrectToolForDrops().strength(6.0F, 10.0F).sound(SoundType.METAL));

    // --- Launch infrastructure ---
    public static final DeferredBlock<Block> LAUNCH_PAD = register("launch_pad", LaunchPadBlock::new,
            p -> p.mapColor(MapColor.COLOR_YELLOW).requiresCorrectToolForDrops().strength(5.0F, 1200.0F).sound(SoundType.METAL));
    public static final DeferredBlock<Block> SERVICE_TOWER = register("service_tower", ServiceTowerBlock::new,
            p -> p.mapColor(MapColor.COLOR_RED).requiresCorrectToolForDrops().strength(3.0F, 6.0F).sound(SoundType.METAL).noOcclusion());
    public static final DeferredBlock<RocketBlock> ROCKET = register("rocket", RocketBlock::new,
            p -> p.mapColor(MapColor.COLOR_RED).strength(2.0F, 6.0F).sound(SoundType.METAL).noOcclusion()
                    .pushReaction(PushReaction.BLOCK));

    // --- Machines ---
    public static final DeferredBlock<ProcessingBlock> FUEL_REFINERY = register("fuel_refinery", p -> new ProcessingBlock(p, MachineKind.REFINERY),
            p -> p.mapColor(MapColor.METAL).requiresCorrectToolForDrops().strength(3.5F, 6.0F).sound(SoundType.METAL)
                    .lightLevel(s -> s.getValue(ProcessingBlock.LIT) ? 13 : 0));
    public static final DeferredBlock<ProcessingBlock> AIR_LIQUEFIER = register("air_liquefier", p -> new ProcessingBlock(p, MachineKind.LIQUEFIER),
            p -> p.mapColor(MapColor.METAL).requiresCorrectToolForDrops().strength(3.5F, 6.0F).sound(SoundType.METAL)
                    .lightLevel(s -> s.getValue(ProcessingBlock.LIT) ? 9 : 0));
    public static final DeferredBlock<ConsoleBlock> MISSION_CONTROL_CONSOLE = register("mission_control_console", ConsoleBlock::new,
            p -> p.mapColor(MapColor.COLOR_CYAN).requiresCorrectToolForDrops().strength(3.0F, 6.0F).sound(SoundType.METAL)
                    .noOcclusion().lightLevel(s -> 6));

    private static <B extends Block> DeferredBlock<B> register(String name, Function<BlockBehaviour.Properties, B> factory,
                                                               UnaryOperator<BlockBehaviour.Properties> props) {
        return BLOCKS.register(name, id -> factory.apply(props.apply(
                BlockBehaviour.Properties.of().setId(ResourceKey.create(Registries.BLOCK, id)))));
    }

    private ModBlocks() {}
}
