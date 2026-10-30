package com.replecant.retrocosmos.dinosaur.client;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * Deinosuchus: a sprawling high-walk on land with an S-wiggle of the body; in the water the legs fold back and the
 * tail sculls. Jaws gape idly on the bank and fly open in the strike.
 */
public class DeinosuchusModel extends DinoModel {
    private final ModelPart body;
    private final ModelPart head;
    private final ModelPart jaw;
    private final ModelPart[] tail;
    private final ModelPart legFrontL;
    private final ModelPart legFrontR;
    private final ModelPart legBackL;
    private final ModelPart legBackR;

    public DeinosuchusModel(ModelPart root) {
        super(root, "head", 1.3F);
        body = part("body");
        head = part("head");
        jaw = part("jaw");
        tail = new ModelPart[]{part("tail1"), part("tail2"), part("tail3")};
        legFrontL = part("leg_front_l");
        legFrontR = part("leg_front_r");
        legBackL = part("leg_back_l");
        legBackR = part("leg_back_r");
    }

    @Override
    public void setupAnim(DinosaurRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        float amount = Math.min(1.0F, s.walkAnimationSpeed * 1.5F);
        float phase = s.walkAnimationPos * 0.7F;
        float water = s.isInWater ? 1.0F : 0.0F;
        float land = 1.0F - water;

        float stride = Mth.cos(phase) * 0.6F * amount * land;
        legFrontL.xRot += stride;
        legBackR.xRot += stride;
        legFrontR.xRot -= stride;
        legBackL.xRot -= stride;
        body.yRot += Mth.sin(phase) * 0.08F * amount * land;
        head.yRot -= Mth.sin(phase) * 0.08F * amount * land;

        // swimming: legs folded back along the flanks, the tail does the work
        legFrontL.xRot += 1.1F * water;
        legFrontR.xRot += 1.1F * water;
        legBackL.xRot += 1.2F * water;
        legBackR.xRot += 1.2F * water;
        float scull = t * (0.12F + 0.25F * amount);
        for (int i = 0; i < tail.length; i++) {
            float strength = (0.05F + 0.25F * amount) * water + 0.04F * land;
            tail[i].yRot += Mth.sin(scull - i * 0.9F) * strength * (1.0F + i * 0.4F);
            tail[i].yRot -= Mth.sin(phase - i * 0.8F) * 0.1F * amount * land;
        }

        head.yRot += s.yRot * DEG * 0.4F;
        head.xRot += s.xRot * DEG * 0.3F;
        // basking gape on the bank
        float gape = Math.max(0.0F, Mth.sin(t * 0.015F));
        jaw.xRot += gape * gape * gape * gape * 0.45F * land;
        DinoGeometry.applyPose(parts, DinoGeometry.DEINOSUCHUS_LUNGE, s.lunge);
        jaw.xRot += swingPulse(s.attackAnim) * 0.6F;
        applyAge(s);
    }
}
