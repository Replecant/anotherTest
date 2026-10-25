package com.replecant.retrocosmos.tribe.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.math.Axis;
import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.tribe.mutant.BlasterBolt;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.state.EntityRenderState;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.state.CameraRenderState;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;

/** A blaster bolt: a full-bright streak of crossed glowing quads along its flight path, plus a head-on glow. */
public class BlasterBoltRenderer extends EntityRenderer<BlasterBolt, BlasterBoltRenderer.State> {
    private static final Identifier TEXTURE = Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "textures/entity/tribe/blaster_bolt.png");
    private static final int FULL_BRIGHT = 0xF000F0;

    public static class State extends EntityRenderState {
        public float yRot;
        public float xRot;
    }

    public BlasterBoltRenderer(EntityRendererProvider.Context context) {
        super(context);
    }

    @Override
    public State createRenderState() {
        return new State();
    }

    @Override
    public void extractRenderState(BlasterBolt bolt, State state, float partialTick) {
        super.extractRenderState(bolt, state, partialTick);
        state.yRot = Mth.rotLerp(partialTick, bolt.yRotO, bolt.getYRot());
        state.xRot = Mth.lerp(partialTick, bolt.xRotO, bolt.getXRot());
    }

    @Override
    protected int getBlockLightLevel(BlasterBolt entity, net.minecraft.core.BlockPos pos) {
        return 15;
    }

    @Override
    public void submit(State state, PoseStack poseStack, SubmitNodeCollector collector, CameraRenderState camera) {
        poseStack.pushPose();
        poseStack.mulPose(Axis.YP.rotationDegrees(state.yRot - 90.0F));
        poseStack.mulPose(Axis.ZP.rotationDegrees(state.xRot));
        float len = 0.55F;
        float half = 0.11F;
        float pulse = 1.0F + 0.15F * Mth.sin(state.ageInTicks * 2.1F);
        collector.submitCustomGeometry(poseStack, RenderTypes.entityTranslucentEmissive(TEXTURE), (pose, buffer) -> {
            // two crossed planes along the flight axis (x)
            quad(buffer, pose, -len, -half * pulse, 0, len, half * pulse, 0, true);
            quad(buffer, pose, -len, 0, -half * pulse, len, 0, half * pulse, false);
            // a small cross-section card so the bolt still glows when it flies straight at you
            float c = half * 1.6F * pulse;
            vertex(buffer, pose, 0, -c, -c, 0, 0);
            vertex(buffer, pose, 0, c, -c, 0, 1);
            vertex(buffer, pose, 0, c, c, 1, 1);
            vertex(buffer, pose, 0, -c, c, 1, 0);
            vertex(buffer, pose, 0, -c, c, 1, 0);
            vertex(buffer, pose, 0, c, c, 1, 1);
            vertex(buffer, pose, 0, c, -c, 0, 1);
            vertex(buffer, pose, 0, -c, -c, 0, 0);
        });
        poseStack.popPose();
        super.submit(state, poseStack, collector, camera);
    }

    /** A double-sided quad from (x0, y0, z0) to (x1, y1, z1); vertical=true spans y, otherwise z. */
    private static void quad(VertexConsumer b, PoseStack.Pose pose, float x0, float y0, float z0, float x1, float y1, float z1, boolean vertical) {
        if (vertical) {
            vertex(b, pose, x0, y0, 0, 0, 0);
            vertex(b, pose, x0, y1, 0, 0, 1);
            vertex(b, pose, x1, y1, 0, 1, 1);
            vertex(b, pose, x1, y0, 0, 1, 0);
            vertex(b, pose, x1, y0, 0, 1, 0);
            vertex(b, pose, x1, y1, 0, 1, 1);
            vertex(b, pose, x0, y1, 0, 0, 1);
            vertex(b, pose, x0, y0, 0, 0, 0);
        } else {
            vertex(b, pose, x0, 0, z0, 0, 0);
            vertex(b, pose, x0, 0, z1, 0, 1);
            vertex(b, pose, x1, 0, z1, 1, 1);
            vertex(b, pose, x1, 0, z0, 1, 0);
            vertex(b, pose, x1, 0, z0, 1, 0);
            vertex(b, pose, x1, 0, z1, 1, 1);
            vertex(b, pose, x0, 0, z1, 0, 1);
            vertex(b, pose, x0, 0, z0, 0, 0);
        }
    }

    private static void vertex(VertexConsumer buffer, PoseStack.Pose pose, float x, float y, float z, float u, float v) {
        buffer.addVertex(pose, x, y, z).setColor(0xFFFFFFFF).setUv(u, v).setOverlay(OverlayTexture.NO_OVERLAY)
                .setLight(FULL_BRIGHT).setNormal(pose, 0, 1, 0);
    }
}
