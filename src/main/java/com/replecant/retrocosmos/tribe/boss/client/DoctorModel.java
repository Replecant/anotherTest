package com.replecant.retrocosmos.tribe.boss.client;

import com.replecant.retrocosmos.tribe.client.TribeGeometry;
import java.util.function.Function;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * Dr. Oinstein on foot: flat on his back after the fall, scrambling up, the syringe to the neck, convulsing as the
 * serum works, arms flung out for the shout.
 */
public class DoctorModel extends EntityModel<BossRenderState> {
    private static final float DEG = Mth.DEG_TO_RAD;
    private final Function<String, ModelPart> parts;
    private final ModelPart body, head, armL, armR, legL, legR, coattail, syringe;

    public DoctorModel(ModelPart root) {
        super(root);
        parts = root.createPartLookup();
        body = part("body");
        head = part("head");
        armL = part("arm_l");
        armR = part("arm_r");
        legL = part("leg_l");
        legR = part("leg_r");
        coattail = part("coattail");
        syringe = part("syringe");
    }

    private ModelPart part(String name) {
        ModelPart p = parts.apply(name);
        if (p == null) {
            throw new IllegalStateException("Doctor model part missing: " + name);
        }
        return p;
    }

    @Override
    public void setupAnim(BossRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        float amount = Math.min(1.0F, s.walkAnimationSpeed) * (1.0F - s.fallen);
        float phase = s.walkAnimationPos * 0.6662F;
        armL.xRot += Mth.cos(phase) * 0.9F * amount;
        armR.xRot -= Mth.cos(phase) * 0.9F * amount;
        legL.xRot -= Mth.cos(phase) * 1.1F * amount;
        legR.xRot += Mth.cos(phase) * 1.1F * amount;
        coattail.xRot += Math.abs(Mth.cos(phase)) * 0.3F * amount;
        head.yRot += s.yRot * DEG;
        head.xRot += s.xRot * DEG;
        // a nervous little fidget
        armL.zRot -= 0.05F + Mth.sin(t * 0.09F) * 0.04F;
        armR.zRot += 0.05F + Mth.sin(t * 0.09F) * 0.04F;
        syringe.visible = s.syringe;
        TribeGeometry.applyPose(parts, TribeGeometry.DOCTOR_INJECT, s.inject);
        TribeGeometry.applyPose(parts, TribeGeometry.DOCTOR_SHOUT, s.shout);
        if (s.shake > 0.0F) {
            ModelPart r = root();
            r.x += Mth.sin(t * 3.1F) * 0.45F * s.shake;
            head.zRot += Mth.sin(t * 2.3F) * 0.12F * s.shake;
            armL.zRot -= Math.abs(Mth.sin(t * 1.7F)) * 0.25F * s.shake;
            body.xRot += Mth.sin(t * 1.1F) * 0.06F * s.shake;
        }
        if (s.fallen > 0.0F) {
            // on his back, feet towards the wreck, arms and legs splayed
            ModelPart r = root();
            r.xRot -= Mth.HALF_PI * s.fallen;
            r.y += 20.0F * s.fallen;
            armL.zRot -= 0.9F * s.fallen;
            armR.zRot += 0.9F * s.fallen;
            legL.zRot -= 0.25F * s.fallen;
            legR.zRot += 0.25F * s.fallen;
            head.xRot -= s.xRot * DEG * s.fallen;
        }
    }
}
