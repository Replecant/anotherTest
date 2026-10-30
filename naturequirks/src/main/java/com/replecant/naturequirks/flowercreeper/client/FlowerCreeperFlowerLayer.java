package com.replecant.naturequirks.flowercreeper.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.LivingEntityRenderer;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;

/**
 * Real flowers growing on the creeper's head and back, drawn from their block models the way the mooshroom wears its
 * mushrooms. Each creeper has its own mix (picked from its UUID); they flash white with the fuse like the rest of it.
 */
public class FlowerCreeperFlowerLayer extends RenderLayer<FlowerCreeperRenderState, FlowerCreeperModel> {
    private static final BlockState[] KINDS = {Blocks.POPPY.defaultBlockState(), Blocks.DANDELION.defaultBlockState(),
            Blocks.CORNFLOWER.defaultBlockState(), Blocks.ALLIUM.defaultBlockState()};

    public FlowerCreeperFlowerLayer(RenderLayerParent<FlowerCreeperRenderState, FlowerCreeperModel> parent) {
        super(parent);
    }

    @Override
    public void submit(PoseStack poseStack, SubmitNodeCollector collector, int light, FlowerCreeperRenderState state, float yRot, float xRot) {
        if (state.isInvisible) {
            return;
        }
        int overlay = LivingEntityRenderer.getOverlayCoords(state, FlowerCreeperRenderer.whiteFlash(state.swelling));
        FlowerCreeperModel model = getParentModel();
        for (int i = 0; i < FlowerSlots.SLOTS.length; i++) {
            float[] slot = FlowerSlots.SLOTS[i];
            poseStack.pushPose();
            (slot[0] == 0 ? model.head() : model.body()).translateAndRotate(poseStack);
            poseStack.translate(slot[1] / 16.0F, slot[2] / 16.0F, slot[3] / 16.0F);
            poseStack.mulPose(Axis.YP.rotation(slot[5]));
            poseStack.mulPose(Axis.XP.rotation(slot[4]));
            poseStack.scale(-slot[6], -slot[6], slot[6]);
            poseStack.translate(-0.5F, 0.0F, -0.5F);
            int kind = (int) Math.floorMod(state.flowerSeed >> (i * 5) ^ (i * 0x9E37L), (long) KINDS.length);
            collector.submitBlock(poseStack, KINDS[kind], light, overlay, state.outlineColor);
            poseStack.popPose();
        }
    }
}
