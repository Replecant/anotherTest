package com.replecant.retrocosmos.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.block.RocketBlock;
import com.replecant.retrocosmos.block.RocketPart;
import com.replecant.retrocosmos.flight.RocketEntity;
import com.replecant.retrocosmos.registry.ModBlocks;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.state.CameraRenderState;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.world.level.block.state.BlockState;

/** Draws the flying rocket from the same nine block models it is built from, plus an engine plume. */
public class RocketRenderer extends EntityRenderer<RocketEntity, RocketRenderState> {
    private static final Identifier PLUME = Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "textures/entity/rocket_plume.png");
    private static final int FULL_BRIGHT = 0xF000F0;

    public RocketRenderer(EntityRendererProvider.Context context) {
        super(context);
        shadowRadius = 1.2F;
    }

    @Override
    public RocketRenderState createRenderState() {
        return new RocketRenderState();
    }

    @Override
    public void extractRenderState(RocketEntity rocket, RocketRenderState state, float partialTick) {
        super.extractRenderState(rocket, state, partialTick);
        state.phase = rocket.phase();
        state.phaseTicks = rocket.phaseTicks();
        state.heightAbovePad = rocket.getY() - rocket.padY();
    }

    @Override
    public void submit(RocketRenderState state, PoseStack poseStack, SubmitNodeCollector collector, CameraRenderState camera) {
        BlockState base = ModBlocks.ROCKET.get().defaultBlockState();
        for (int i = 0; i < RocketPart.HEIGHT; i++) {
            poseStack.pushPose();
            poseStack.translate(-0.5, i, -0.5);
            collector.submitBlock(poseStack, base.setValue(RocketBlock.PART, RocketPart.byOffset(i)), state.lightCoords,
                    OverlayTexture.NO_OVERLAY, state.outlineColor);
            poseStack.popPose();
        }

        float length = plumeLength(state);
        if (length > 0) {
            float flicker = 0.85F + 0.15F * Mth.sin(state.ageInTicks * 1.7F) * Mth.sin(state.ageInTicks * 0.63F);
            float len = length * flicker;
            float half = 0.45F;
            collector.submitCustomGeometry(poseStack, RenderTypes.entityTranslucentEmissive(PLUME), (pose, buffer) -> {
                quad(buffer, pose, -half, 0, half, 0, len);
                quad(buffer, pose, 0, -half, 0, half, len);
            });
        }
        super.submit(state, poseStack, collector, camera);
    }

    private static float plumeLength(RocketRenderState state) {
        return switch (state.phase) {
            case RocketEntity.PHASE_PAD -> state.phaseTicks > RocketEntity.PAD_COUNTDOWN - 60 ? 1.2F : 0;
            case RocketEntity.PHASE_ASCENT -> Math.min(6.0F, 2.5F + state.phaseTicks * 0.03F);
            case RocketEntity.PHASE_DESCENT -> state.heightAbovePad < 48 ? 2.5F : 0;
            default -> 0;
        };
    }

    /** A vertical double-sided quad hanging down from the nozzle, from (x0,z0) to (x1,z1). */
    private static void quad(VertexConsumer buffer, PoseStack.Pose pose, float x0, float z0, float x1, float z1, float len) {
        float top = 0.05F;
        float bottom = top - len;
        vertex(buffer, pose, x0, top, z0, 0, 0);
        vertex(buffer, pose, x0, bottom, z0, 0, 1);
        vertex(buffer, pose, x1, bottom, z1, 1, 1);
        vertex(buffer, pose, x1, top, z1, 1, 0);
        vertex(buffer, pose, x1, top, z1, 1, 0);
        vertex(buffer, pose, x1, bottom, z1, 1, 1);
        vertex(buffer, pose, x0, bottom, z0, 0, 1);
        vertex(buffer, pose, x0, top, z0, 0, 0);
    }

    private static void vertex(VertexConsumer buffer, PoseStack.Pose pose, float x, float y, float z, float u, float v) {
        buffer.addVertex(pose, x, y, z).setColor(0xFFFFFFFF).setUv(u, v).setOverlay(OverlayTexture.NO_OVERLAY)
                .setLight(FULL_BRIGHT).setNormal(pose, 0, 1, 0);
    }
}
