package com.replecant.retrocosmos.dinosaur.client;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/** Ankylosaurus: a ponderous waddle, head down to graze, and the club sweeping side to side when it strikes. */
public class AnkylosaurusModel extends DinoModel {
    private final ModelPart body;
    private final ModelPart head;
    private final ModelPart tail1;
    private final ModelPart tail2;
    private final ModelPart club;
    private final ModelPart legFrontL;
    private final ModelPart legFrontR;
    private final ModelPart legBackL;
    private final ModelPart legBackR;

    public AnkylosaurusModel(ModelPart root) {
        super(root, "head", 1.5F);
        body = part("body");
        head = part("head");
        tail1 = part("tail1");
        tail2 = part("tail2");
        club = part("club");
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
        float phase = s.walkAnimationPos * 0.6F;
        float swingLegs = Mth.cos(phase) * 0.5F * amount;
        legFrontL.xRot += swingLegs;
        legBackR.xRot += swingLegs;
        legFrontR.xRot -= swingLegs;
        legBackL.xRot -= swingLegs;
        body.zRot += Mth.sin(phase) * 0.04F * amount;
        body.y += Math.abs(Mth.sin(phase)) * 0.4F * amount;

        head.yRot += s.yRot * DEG * 0.4F * (1.0F - s.graze);
        head.xRot += s.xRot * DEG * 0.3F * (1.0F - s.graze);
        DinoGeometry.applyPose(parts, DinoGeometry.ANKYLOSAURUS_GRAZE, s.graze);
        head.xRot += Mth.sin(t * 0.5F) * 0.06F * s.graze;

        // idle tail wag; the strike is one full sweep of the club, the body bracing against it
        tail1.yRot += Mth.sin(t * 0.07F) * 0.1F;
        tail2.yRot += Mth.sin(t * 0.07F - 0.6F) * 0.12F;
        float sweep = Mth.sin(s.swing * Mth.TWO_PI);
        tail1.yRot += sweep * 0.55F;
        tail2.yRot += sweep * 0.5F;
        club.yRot += sweep * 0.35F;
        body.yRot -= sweep * 0.12F;
        applyAge(s);
    }
}
