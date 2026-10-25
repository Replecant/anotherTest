package com.replecant.retrocosmos.dinosaur.robot.client;

import com.replecant.retrocosmos.dinosaur.client.DinoModel;
import com.replecant.retrocosmos.dinosaur.client.DinosaurRenderState;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * Atomic Automaton: a stiff, stomping march with arms swinging like pistons; a straight right jab for the punch and,
 * for the power fist, a wind-up and a big haymaker with the claws snapped open.
 */
public class AtomicAutomatonModel extends DinoModel {
    private final ModelPart body;
    private final ModelPart head;
    private final ModelPart armL;
    private final ModelPart armR;
    private final ModelPart forearmL;
    private final ModelPart forearmR;
    private final ModelPart clawR;
    private final ModelPart legL;
    private final ModelPart legR;
    private final ModelPart shinL;
    private final ModelPart shinR;

    public AtomicAutomatonModel(ModelPart root) {
        super(root, "head", 1.0F);
        body = part("body");
        head = part("head");
        armL = part("arm_l");
        armR = part("arm_r");
        forearmL = part("forearm_l");
        forearmR = part("forearm_r");
        clawR = part("claw_r");
        legL = part("leg_l");
        legR = part("leg_r");
        shinL = part("shin_l");
        shinR = part("shin_r");
    }

    @Override
    public void setupAnim(DinosaurRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        float amount = Math.min(1.0F, s.walkAnimationSpeed * 1.5F);
        float phase = s.walkAnimationPos * 0.55F;
        float cos = Mth.cos(phase);
        float sin = Mth.sin(phase);
        legL.xRot += cos * 0.55F * amount;
        legR.xRot -= cos * 0.55F * amount;
        shinL.xRot += Math.max(0.0F, sin) * 0.5F * amount;
        shinR.xRot += Math.max(0.0F, -sin) * 0.5F * amount;
        armL.xRot -= cos * 0.4F * amount;
        armR.xRot += cos * 0.4F * amount;
        body.y += (1.0F - Math.abs(cos)) * 0.6F * amount;
        body.zRot += sin * 0.03F * amount;
        // arms held forward a little when it hunts
        float ready = s.aggressive ? 1.0F : 0.0F;
        armL.xRot -= 0.5F * ready;
        armR.xRot -= 0.5F * ready;
        forearmL.xRot -= 0.4F * ready;
        forearmR.xRot -= 0.4F * ready;

        head.yRot += s.yRot * DEG;
        head.xRot += s.xRot * DEG * 0.6F;
        head.zRot += Mth.sin(t * 0.05F) * 0.02F;

        // the jab
        float jab = swingPulse(s.attackAnim);
        armR.xRot -= jab * 1.3F;
        forearmR.xRot -= jab * 0.5F;
        // the power fist: wind up, then swing through
        if (s.swing > 0.0F) {
            float wind = s.swing < 0.4F ? s.swing / 0.4F : 1.0F - (s.swing - 0.4F) / 0.6F;
            float strike = s.swing < 0.4F ? 0.0F : Mth.sin((s.swing - 0.4F) / 0.6F * Mth.PI);
            armR.xRot += wind * 0.9F - strike * 2.2F;
            armR.zRot += strike * 0.3F;
            body.yRot += wind * 0.35F - strike * 0.5F;
            clawR.xScale = 1.0F + strike * 0.3F;
        }
        applyAge(s);
    }
}
