package com.replecant.retrocosmos.tribe.boss.client;

import com.replecant.retrocosmos.tribe.client.TribeGeometry;
import java.util.function.Function;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * The Atomic Strider: a heavy chicken-walker gait (knees forward, feet kept flat), the hull turning on its hips to
 * aim, cannons trembling while they charge, one foot raised for the stomp - and the wreck: sagging on its knees,
 * shaking itself apart. Dr. Oinstein works the levers under the glass.
 */
public class StriderModel extends EntityModel<BossRenderState> {
    private static final float DEG = Mth.DEG_TO_RAD;
    private final Function<String, ModelPart> parts;
    private final ModelPart hips, body, cannonL, cannonR, thighL, thighR, shinL, shinR, footL, footR;
    private final ModelPart pilot, pilotHead, pilotArmL, pilotArmR;

    public StriderModel(ModelPart root) {
        super(root);
        parts = root.createPartLookup();
        hips = part("hips");
        body = part("body");
        cannonL = part("cannon_l");
        cannonR = part("cannon_r");
        thighL = part("thigh_l");
        thighR = part("thigh_r");
        shinL = part("shin_l");
        shinR = part("shin_r");
        footL = part("foot_l");
        footR = part("foot_r");
        pilot = part("pilot_body");
        pilotHead = part("pilot_head");
        pilotArmL = part("pilot_arm_l");
        pilotArmR = part("pilot_arm_r");
    }

    private ModelPart part(String name) {
        ModelPart p = parts.apply(name);
        if (p == null) {
            throw new IllegalStateException("Strider model part missing: " + name);
        }
        return p;
    }

    @Override
    public void setupAnim(BossRenderState s) {
        super.setupAnim(s);
        TribeGeometry.applyScales(parts);
        float t = s.ageInTicks;
        float still = 1.0F - Math.max(s.raise, s.wreck);
        float amount = Math.min(1.0F, s.walkAnimationSpeed * 1.4F) * still;
        float phase = s.walkAnimationPos * 0.32F;
        float sin = Mth.sin(phase);
        float cos = Mth.cos(phase);
        // left leg, right leg half a stride apart; the knee lifts on the forward swing, the foot stays level
        float tl = sin * 0.42F * amount;
        float sl = Math.max(0.0F, cos) * 0.55F * amount;
        float tr = -sin * 0.42F * amount;
        float sr = Math.max(0.0F, -cos) * 0.55F * amount;
        thighL.xRot += tl;
        shinL.xRot += sl;
        footL.xRot -= tl + sl;
        thighR.xRot += tr;
        shinR.xRot += sr;
        footR.xRot -= tr + sr;
        hips.y += Math.abs(cos) * 1.2F * amount;
        hips.zRot += sin * 0.035F * amount;
        // idle hum
        body.y += Mth.sin(t * 0.12F) * 0.25F;
        // turn the hull and aim the cannons
        body.yRot += s.yRot * DEG * 0.75F;
        float pitch = Mth.clamp(s.xRot * DEG, -0.6F, 0.6F);
        cannonL.xRot += pitch;
        cannonR.xRot += pitch;
        pilotHead.yRot += s.yRot * DEG * 0.25F;
        pilotHead.xRot += pitch * 0.5F;
        // the doctor at the levers
        float levers = s.aggressive ? 0.3F : 0.12F;
        pilotArmL.xRot += Mth.sin(t * 0.35F) * levers;
        pilotArmR.xRot += Mth.sin(t * 0.35F + 1.7F) * levers;
        // charging: the cannons tremble, he leans in
        if (s.charge > 0.0F) {
            float tremble = Mth.sin(t * 3.1F) * 0.025F * s.charge;
            cannonL.zRot += tremble;
            cannonR.zRot -= tremble;
            cannonL.z += s.charge * 0.8F;
            cannonR.z += s.charge * 0.8F;
            pilot.xRot += 0.2F * s.charge;
        }
        // stomp: one leg up - and down
        TribeGeometry.applyPose(parts, TribeGeometry.STRIDER_STOMP, s.raise);
        if (s.impact > 0.0F) {
            body.y += 1.5F * s.impact;
            body.xRot += 0.06F * s.impact;
        }
        // the wreck: on its knees, shaking apart, the doctor thrown about
        if (s.wreck > 0.0F) {
            TribeGeometry.applyPose(parts, TribeGeometry.STRIDER_WRECK, s.wreck);
            ModelPart r = root();
            r.y += 4.0F * s.wreck;
            r.x += Mth.sin(t * 2.7F) * 0.7F * s.wreck;
            body.zRot += Mth.sin(t * 1.9F) * 0.06F * s.wreck;
            cannonL.zRot += Mth.sin(t * 2.3F) * 0.12F * s.wreck;
            pilot.zRot += Mth.sin(t * 1.3F) * 0.3F * s.wreck;
            pilotArmL.xRot -= 2.2F * s.wreck;
            pilotArmR.xRot -= 2.4F * s.wreck;
        }
    }
}
