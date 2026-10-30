package com.replecant.retrocosmos.dinosaur.client;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/** Plesiosaur: slow underwater flight on four paddles, the long neck swaying; rears it up out of the water to look. */
public class PlesiosaurModel extends DinoModel {
    private final ModelPart body;
    private final ModelPart[] neck;
    private final ModelPart head;
    private final ModelPart jaw;
    private final ModelPart tail1;
    private final ModelPart tail2;
    private final ModelPart frontL;
    private final ModelPart frontR;
    private final ModelPart backL;
    private final ModelPart backR;

    public PlesiosaurModel(ModelPart root) {
        super(root, "head", 1.0F);
        body = part("body");
        neck = new ModelPart[]{part("neck1"), part("neck2"), part("neck3"), part("neck4")};
        head = part("head");
        jaw = part("jaw");
        tail1 = part("tail1");
        tail2 = part("tail2");
        frontL = part("flipper_front_l");
        frontR = part("flipper_front_r");
        backL = part("flipper_back_l");
        backR = part("flipper_back_r");
    }

    @Override
    public void setupAnim(DinosaurRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        float effort = 0.3F + Math.min(1.0F, s.walkAnimationSpeed * 2.0F) * 0.5F;
        float phase = t * (0.09F + effort * 0.08F);

        // the four paddles beat like wings, front and back pairs out of step
        float front = Mth.sin(phase) * 0.5F * effort;
        float back = Mth.sin(phase + 1.6F) * 0.45F * effort;
        frontL.zRot += front;
        frontR.zRot -= front;
        backL.zRot += back;
        backR.zRot -= back;
        frontL.xRot += Mth.cos(phase) * 0.25F * effort;
        frontR.xRot += Mth.cos(phase) * 0.25F * effort;
        backL.xRot += Mth.cos(phase + 1.6F) * 0.2F * effort;
        backR.xRot += Mth.cos(phase + 1.6F) * 0.2F * effort;
        body.y -= Mth.cos(phase * 2.0F) * 0.4F * effort;

        // body pitches with the swim; neck held level in the swim, swaying gently
        float swim = 1.0F - s.peek;
        body.xRot += s.xRot * DEG * swim;
        for (int i = 0; i < neck.length; i++) {
            neck[i].yRot += Mth.sin(t * 0.05F - i * 0.6F) * 0.07F + s.yRot * DEG * 0.08F;
            neck[i].xRot += Mth.sin(t * 0.04F - i * 0.5F) * 0.03F;
        }
        tail1.yRot += Mth.sin(phase * 0.5F) * 0.12F;
        tail2.yRot += Mth.sin(phase * 0.5F - 0.8F) * 0.18F;

        // the Loch Ness pose: neck up out of the water, head turning to look about
        DinoGeometry.applyPose(parts, DinoGeometry.PLESIOSAUR_PEEK, s.peek);
        head.yRot += Mth.sin(t * 0.03F) * 0.5F * s.peek;

        float bite = swingPulse(s.attackAnim);
        jaw.xRot += 0.05F + bite * 0.8F;
        neck[3].xRot += bite * 0.3F;
        applyAge(s);
    }
}
