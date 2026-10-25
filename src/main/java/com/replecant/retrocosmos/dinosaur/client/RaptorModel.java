package com.replecant.retrocosmos.dinosaur.client;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * Venus Raptor: springy two-legged run with big strides, stiff counter-balancing tail, snapping jaws and a
 * pounce pose in mid-air (legs tucked, claws thrown forward).
 */
public class RaptorModel extends DinoModel {
    private final ModelPart body;
    private final ModelPart neck;
    private final ModelPart head;
    private final ModelPart jaw;
    private final ModelPart tail1;
    private final ModelPart tail2;
    private final ModelPart thighL;
    private final ModelPart thighR;
    private final ModelPart shinL;
    private final ModelPart shinR;
    private final ModelPart footL;
    private final ModelPart footR;
    private final ModelPart armL;
    private final ModelPart armR;
    private final ModelPart handL;
    private final ModelPart handR;

    public RaptorModel(ModelPart root) {
        super(root, "head", 1.35F);
        body = part("body");
        neck = part("neck");
        head = part("head");
        jaw = part("jaw");
        tail1 = part("tail1");
        tail2 = part("tail2");
        thighL = part("thigh_l");
        thighR = part("thigh_r");
        shinL = part("shin_l");
        shinR = part("shin_r");
        footL = part("foot_l");
        footR = part("foot_r");
        armL = part("arm_l");
        armR = part("arm_r");
        handL = part("hand_l");
        handR = part("hand_r");
    }

    @Override
    public void setupAnim(DinosaurRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        float amount = Math.min(1.0F, s.walkAnimationSpeed * 1.2F) * (1.0F - s.leap);
        float phase = s.walkAnimationPos * 0.75F;
        float sin = Mth.sin(phase);
        float cos = Mth.cos(phase);

        // legs: long strides, knee lifts on the forward swing, toes stay flat-ish
        thighL.xRot += cos * 0.85F * amount;
        thighR.xRot -= cos * 0.85F * amount;
        shinL.xRot += Math.max(0.0F, sin) * 0.9F * amount;
        shinR.xRot += Math.max(0.0F, -sin) * 0.9F * amount;
        footL.xRot -= (cos * 0.4F + Math.max(0.0F, sin) * 0.5F) * amount;
        footR.xRot -= (-cos * 0.4F + Math.max(0.0F, -sin) * 0.5F) * amount;

        // body bobs twice per stride and leans into the run; the tail counter-sways
        float bob = Math.abs(cos);
        body.y += (1.0F - bob) * 0.9F * amount;
        body.xRot += 0.12F * amount;
        body.zRot += sin * 0.05F * amount;
        tail1.yRot += Mth.sin(t * 0.11F) * 0.10F - sin * 0.14F * amount;
        tail2.yRot += Mth.sin(t * 0.11F - 0.9F) * 0.16F - sin * 0.12F * amount;
        tail1.xRot -= 0.1F * amount;

        // breathing and head bob, then where it looks
        neck.xRot += Mth.sin(t * 0.08F) * 0.03F + cos * cos * 0.08F * amount - 0.1F * amount;
        head.xRot += 0.1F * amount;
        neck.yRot += s.yRot * DEG * 0.45F;
        head.yRot += s.yRot * DEG * 0.45F;
        neck.xRot += s.xRot * DEG * 0.4F;
        head.xRot += s.xRot * DEG * 0.4F;

        // jaws: a slow pant at rest, snapping when hunting, a big bite on the swing
        float bite = swingPulse(s.attackAnim);
        float jawOpen = 0.04F + 0.04F * Mth.sin(t * 0.1F);
        if (s.aggressive) {
            jawOpen = 0.22F + 0.18F * Math.max(0.0F, Mth.sin(t * 0.55F));
        }
        jaw.xRot += jawOpen + bite * 0.75F;
        neck.xRot += bite * 0.35F;
        head.xRot -= bite * 0.2F;

        // little arms: twitch at rest, raking claws when hunting
        float rake = s.aggressive ? Mth.sin(t * 0.5F) * 0.35F : Mth.sin(t * 0.07F) * 0.05F;
        armL.xRot += rake - bite * 0.8F;
        armR.xRot += -rake - bite * 0.8F;
        handL.xRot += Math.abs(rake) * 0.5F;
        handR.xRot += Math.abs(rake) * 0.5F;

        // mid-air pounce
        DinoGeometry.applyPose(parts, DinoGeometry.RAPTOR_LEAP, s.leap);
        applyAge(s);
    }
}
