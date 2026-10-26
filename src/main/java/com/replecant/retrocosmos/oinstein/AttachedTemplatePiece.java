package com.replecant.retrocosmos.oinstein;

import com.replecant.retrocosmos.RetroCosmos;
import java.util.LinkedHashMap;
import java.util.Map;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.Identifier;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.TemplateStructurePiece;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePieceSerializationContext;
import net.minecraft.world.level.levelgen.structure.templatesystem.BlockIgnoreProcessor;
import net.minecraft.world.level.levelgen.structure.templatesystem.LiquidSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplateManager;

/**
 * A template placed as it is, rotated with the jigsaw start piece it is attached to ({@code extra_pieces} of
 * {@link DryJigsawStructure}): the lower laboratory under the Oinstein Institute. Not a pool element, so the
 * Beardifier leaves the terrain round it alone - the template carries its own steel shell; waterlogging from the
 * world is never applied (a cave aquifer must not leak in through stairs or bars).
 *
 * <p>DATA structure blocks in the template are markers: {@code oinstein_boss_anchor} becomes
 * {@code retrocosmos:oinstein_boss_anchor} once that block is registered (air until then), any other marker air.
 * {@link #markers()} gives their world positions.
 */
public class AttachedTemplatePiece extends TemplateStructurePiece {
    public static final String BOSS_ANCHOR_MARKER = "oinstein_boss_anchor";
    public static final Identifier BOSS_ANCHOR = Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "oinstein_boss_anchor");

    public AttachedTemplatePiece(StructureTemplateManager templates, Identifier template, BlockPos pos, Rotation rotation) {
        super(ModOinstein.ATTACHED_TEMPLATE.get(), 0, templates, template, template.toString(), settings(rotation), pos);
    }

    public AttachedTemplatePiece(StructureTemplateManager templates, CompoundTag tag) {
        super(ModOinstein.ATTACHED_TEMPLATE.get(), tag, templates,
                id -> settings(Rotation.valueOf(tag.getStringOr("Rot", Rotation.NONE.name()))));
    }

    private static StructurePlaceSettings settings(Rotation rotation) {
        return new StructurePlaceSettings().setRotation(rotation).setMirror(Mirror.NONE)
                .addProcessor(BlockIgnoreProcessor.STRUCTURE_BLOCK).addProcessor(FurnitureFacingProcessor.INSTANCE).setLiquidSettings(LiquidSettings.IGNORE_WATERLOGGING)
                .setFinalizeEntities(true);
    }

    @Override
    protected void addAdditionalSaveData(StructurePieceSerializationContext context, CompoundTag tag) {
        super.addAdditionalSaveData(context, tag);
        tag.putString("Rot", placeSettings.getRotation().name());
    }

    @Override
    protected void handleDataMarker(String name, BlockPos pos, ServerLevelAccessor level, RandomSource random, BoundingBox box) {
        if (!box.isInside(pos)) {
            return;
        }
        BlockState state = Blocks.AIR.defaultBlockState();
        if (BOSS_ANCHOR_MARKER.equals(name)) {
            state = BuiltInRegistries.BLOCK.getOptional(BOSS_ANCHOR).map(Block::defaultBlockState).orElse(state);
        }
        level.setBlock(pos, state, Block.UPDATE_CLIENTS);
    }

    /** World positions of the template's DATA markers, by name (the boss anchor of the lower laboratory). */
    public Map<String, BlockPos> markers() {
        Map<String, BlockPos> out = new LinkedHashMap<>();
        for (StructureTemplate.StructureBlockInfo info : blocks(Blocks.STRUCTURE_BLOCK)) {
            if (info.nbt() != null) {
                out.put(info.nbt().getStringOr("metadata", ""), info.pos());
            }
        }
        return out;
    }

    /** Every block of the template of this kind, at its world position (not clipped to the chunk last placed). */
    public java.util.List<StructureTemplate.StructureBlockInfo> blocks(Block block) {
        return template.filterBlocks(templatePosition, placeSettings.copy().setBoundingBox(null), block);
    }

    /** A template-local position in the world. */
    public BlockPos toWorld(BlockPos local) {
        return templatePosition.offset(StructureTemplate.transform(local, Mirror.NONE, placeSettings.getRotation(), BlockPos.ZERO));
    }

    public Identifier templateId() {
        return Identifier.parse(templateName);
    }
}
