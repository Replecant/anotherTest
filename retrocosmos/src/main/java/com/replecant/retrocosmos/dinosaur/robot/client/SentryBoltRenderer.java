package com.replecant.retrocosmos.dinosaur.robot.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.dinosaur.robot.SentryBolt;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.state.EntityRenderState;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.state.CameraRenderState;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;

/** The blaster bolt: three crossed full-bright glow quads, so it reads as a hot red spark from every angle. */
public class SentryBoltRenderer extends EntityRenderer<SentryBolt, EntityRenderState> {
    private static final Identifier TEXTURE = Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "textures/entity/dinosaur/sentry_bolt.png");
    private static final int FULL_BRIGHT = 0xF000F0;
    private static final float SIZE = 0.22F;

    public SentryBoltRenderer(EntityRendererProvider.Context context) {
        super(context);
    }

    @Override
    public EntityRenderState createRenderState() {
        return new EntityRenderState();
    }

    @Override
    public void submit(EntityRenderState state, PoseStack poseStack, SubmitNodeCollector collector, CameraRenderState camera) {
        poseStack.pushPose();
        poseStack.translate(0.0, 0.15, 0.0);
        collector.submitCustomGeometry(poseStack, RenderTypes.entityTranslucentEmissive(TEXTURE), (pose, buffer) -> {
            float s = SIZE;
            // XY, ZY and XZ planes, each double sided
            quad(buffer, pose, -s, -s, 0, s, -s, 0, s, s, 0, -s, s, 0);
            quad(buffer, pose, 0, -s, -s, 0, -s, s, 0, s, s, 0, s, -s);
            quad(buffer, pose, -s, 0, -s, s, 0, -s, s, 0, s, -s, 0, s);
        });
        poseStack.popPose();
        super.submit(state, poseStack, collector, camera);
    }

    private static void quad(VertexConsumer b, PoseStack.Pose pose, float x0, float y0, float z0, float x1, float y1, float z1,
                             float x2, float y2, float z2, float x3, float y3, float z3) {
        vertex(b, pose, x0, y0, z0, 0, 1);
        vertex(b, pose, x1, y1, z1, 1, 1);
        vertex(b, pose, x2, y2, z2, 1, 0);
        vertex(b, pose, x3, y3, z3, 0, 0);
        vertex(b, pose, x3, y3, z3, 0, 0);
        vertex(b, pose, x2, y2, z2, 1, 0);
        vertex(b, pose, x1, y1, z1, 1, 1);
        vertex(b, pose, x0, y0, z0, 0, 1);
    }

    private static void vertex(VertexConsumer b, PoseStack.Pose pose, float x, float y, float z, float u, float v) {
        b.addVertex(pose, x, y, z).setColor(0xFFFFFFFF).setUv(u, v).setOverlay(OverlayTexture.NO_OVERLAY)
                .setLight(FULL_BRIGHT).setNormal(pose, 0, 1, 0);
    }
}
