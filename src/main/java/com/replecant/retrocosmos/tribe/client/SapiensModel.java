package com.replecant.retrocosmos.tribe.client;

import java.util.function.Function;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/** Hominus Sapiens: an upright, careful gait; the blaster levelled at its target with a recoil kick; a throbbing brain. */
public class SapiensModel extends EntityModel<MutantRenderState> {
    private static final float DEG = Mth.DEG_TO_RAD;
    private final Function<String, ModelPart> parts;
    private final ModelPart body, head, brain, armL, armR, legL, legR, blaster;

    public SapiensModel(ModelPart root) {
        super(root);
        parts = root.createPartLookup();
        body = part("body");
        head = part("head");
        armL = part("arm_l");
        armR = part("arm_r");
        legL = part("leg_l");
        legR = part("leg_r");
        brain = part("brain");
        blaster = part("blaster");
    }

    private ModelPart part(String name) {
        ModelPart p = parts.apply(name);
        if (p == null) {
            throw new IllegalStateException("Sapiens model part missing: " + name);
        }
        return p;
    }

    @Override
    public void setupAnim(MutantRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        float amount = Math.min(1.0F, s.walkAnimationSpeed * 1.5F);
        float phase = s.walkAnimationPos * 0.6662F;
        float cos = Mth.cos(phase);
        legL.xRot += cos * 0.9F * amount;
        legR.xRot -= cos * 0.9F * amount;
        armL.xRot -= cos * 0.6F * amount;
        armR.xRot += cos * 0.35F * amount * (1.0F - s.aim);
        body.y += Math.abs(Mth.sin(phase)) * 0.4F * amount;
        armL.zRot -= 0.04F + Mth.sin(t * 0.07F) * 0.03F;
        armR.zRot += 0.04F + Mth.sin(t * 0.07F) * 0.03F;
        head.yRot += s.yRot * DEG;
        head.xRot += s.xRot * DEG;
        // aiming: the pistol arm follows the eyes
        TribeGeometry.applyPose(parts, TribeGeometry.SAPIENS_AIM, s.aim);
        armR.xRot += s.xRot * DEG * s.aim;
        armR.yRot += s.yRot * DEG * s.aim;
        float kick = s.attackAnim <= 0.0F ? 0.0F : Mth.sin(s.attackAnim * Mth.PI);
        armR.xRot -= kick * 0.35F;
        // keep the pistol level in the fist: cancel the arm's (and torso's) pitch, then tip it to where it looks
        blaster.xRot = -(armR.xRot + body.xRot) + s.xRot * DEG * s.aim - kick * 0.25F;
        // that brain: a slow, wet throb
        float throb = 1.0F + 0.012F * Mth.sin(t * 0.12F);
        brain.xScale = throb;
        brain.zScale = throb;
    }
}
