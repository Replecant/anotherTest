package com.replecant.retrocosmos.dinosaur.client;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * Triceratops: sturdy rhino trot; when angry it drops its head so the three horns point straight ahead, raises
 * the frill like a shield, and paws the ground with a front foot before the charge.
 */
public class TriceratopsModel extends DinoModel {
    private final ModelPart body;
    private final ModelPart head;
    private final ModelPart frill;
    private final ModelPart tail1;
    private final ModelPart tail2;
    private final ModelPart legFrontL;
    private final ModelPart legFrontR;
    private final ModelPart legBackL;
    private final ModelPart legBackR;

    public TriceratopsModel(ModelPart root) {
        super(root, "head", 1.45F);
        body = part("body");
        head = part("head");
        frill = part("frill");
        tail1 = part("tail1");
        tail2 = part("tail2");
        legFrontL = part("leg_front_l");
        legFrontR = part("leg_front_r");
        legBackL = part("leg_back_l");
        legBackR = part("leg_back_r");
    }

    @Override
    public void setupAnim(DinosaurRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        float amount = Math.min(1.0F, s.walkAnimationSpeed * 1.3F);
        float phase = s.walkAnimationPos * 0.55F;
        float sin = Mth.sin(phase);
        float cos = Mth.cos(phase);

        float swing = cos * 0.6F * amount;
        legFrontL.xRot += swing;
        legBackR.xRot += swing;
        legFrontR.xRot -= swing;
        legBackL.xRot -= swing;
        body.y += Math.abs(sin) * 0.6F * amount;
        body.zRot += sin * 0.03F * amount;

        // head: heavy nod with the steps, looks around
        head.xRot += Math.abs(sin) * 0.06F * amount + Mth.sin(t * 0.06F) * 0.02F;
        head.yRot += s.yRot * DEG * 0.6F * (1.0F - s.charge * 0.7F);
        head.xRot += s.xRot * DEG * 0.4F * (1.0F - s.charge);
        frill.xRot += Mth.sin(t * 0.05F) * 0.015F;

        tail1.yRot += Mth.sin(t * 0.08F) * 0.12F + sin * 0.12F * amount;
        tail2.yRot += Mth.sin(t * 0.08F - 0.8F) * 0.16F + sin * 0.1F * amount;

        // charge: horns levelled, frill up; the windup paws the ground and shakes the head
        DinoGeometry.applyPose(parts, DinoGeometry.TRICERATOPS_CHARGE, s.charge);
        if (s.windup) {
            legFrontR.xRot += -0.5F - Mth.sin(t * 0.7F) * 0.45F;
            head.zRot += Mth.sin(t * 0.9F) * 0.08F;
            body.xRot += 0.04F;
        }
        float gore = swingPulse(s.attackAnim);
        head.xRot -= gore * 0.6F;
        applyAge(s);
    }
}
