package com.replecant.retrocosmos.dinosaur.client;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * Tyrannosaurus: ponderous stomping stride, the great tail swinging in counterpoint; it lunges and snaps when it
 * bites, throws its head up to roar, and whips the whole tail round in the sweep.
 */
public class TyrannosaurusModel extends DinoModel {
    private final ModelPart body;
    private final ModelPart neck;
    private final ModelPart head;
    private final ModelPart jaw;
    private final ModelPart[] tail;
    private final ModelPart thighL;
    private final ModelPart thighR;
    private final ModelPart shinL;
    private final ModelPart shinR;
    private final ModelPart footL;
    private final ModelPart footR;
    private final ModelPart armL;
    private final ModelPart armR;

    public TyrannosaurusModel(ModelPart root) {
        super(root, "head", 1.0F);
        body = part("body");
        neck = part("neck");
        head = part("head");
        jaw = part("jaw");
        tail = new ModelPart[]{part("tail1"), part("tail2"), part("tail3"), part("tail4")};
        thighL = part("thigh_l");
        thighR = part("thigh_r");
        shinL = part("shin_l");
        shinR = part("shin_r");
        footL = part("foot_l");
        footR = part("foot_r");
        armL = part("arm_l");
        armR = part("arm_r");
    }

    @Override
    public void setupAnim(DinosaurRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        float amount = Math.min(1.0F, s.walkAnimationSpeed * 1.4F) * (1.0F - s.roar);
        float phase = s.walkAnimationPos * 0.35F;
        float sin = Mth.sin(phase);
        float cos = Mth.cos(phase);

        thighL.xRot += cos * 0.55F * amount;
        thighR.xRot -= cos * 0.55F * amount;
        shinL.xRot += Math.max(0.0F, sin) * 0.6F * amount;
        shinR.xRot += Math.max(0.0F, -sin) * 0.6F * amount;
        footL.xRot -= (cos * 0.3F + Math.max(0.0F, sin) * 0.4F) * amount;
        footR.xRot -= (-cos * 0.3F + Math.max(0.0F, -sin) * 0.4F) * amount;

        // heavy body: sinks on each footfall, rolls side to side; leans forward into a charge
        body.y += (1.0F - Math.abs(cos)) * 1.6F * amount;
        body.zRot += sin * 0.05F * amount;
        body.xRot += (s.aggressive ? 0.2F : 0.05F) * amount;
        neck.xRot -= (s.aggressive ? 0.12F : 0.0F) * amount;

        for (int i = 0; i < tail.length; i++) {
            tail[i].yRot += Mth.sin(t * 0.06F - i * 0.7F) * (0.05F + 0.03F * i) - sin * 0.08F * amount;
            tail[i].xRot += Mth.sin(t * 0.05F - i * 0.5F) * 0.02F;
        }
        // the tail sweep: the whole tail whips round, the body twisting against it
        for (int i = 0; i < tail.length; i++) {
            tail[i].yRot += s.sweep * (0.5F + 0.15F * i);
        }
        body.yRot -= s.sweep * 0.25F;

        neck.yRot += s.yRot * DEG * 0.35F;
        head.yRot += s.yRot * DEG * 0.35F;
        neck.xRot += s.xRot * DEG * 0.3F;
        head.xRot += s.xRot * DEG * 0.3F;
        neck.xRot += Mth.sin(t * 0.07F) * 0.02F + Math.abs(cos) * 0.05F * amount;

        // jaws: a slow pant, hanging open when hunting, a lunge and snap on the bite
        float bite = swingPulse(s.attackAnim);
        jaw.xRot += 0.05F + 0.04F * Mth.sin(t * 0.08F) + (s.aggressive ? 0.25F : 0.0F) + bite * 0.7F;
        neck.xRot += bite * 0.45F;
        head.xRot += bite * 0.15F;

        float flail = Mth.sin(t * 0.6F) * 0.3F;
        armL.xRot += (s.aggressive ? flail : Mth.sin(t * 0.05F) * 0.05F);
        armR.xRot += (s.aggressive ? -flail : Mth.sin(t * 0.05F) * 0.05F);

        DinoGeometry.applyPose(parts, DinoGeometry.TYRANNOSAURUS_ROAR, s.roar);
        head.zRot += Mth.sin(t * 1.3F) * 0.07F * s.roar;
        applyAge(s);
    }
}
