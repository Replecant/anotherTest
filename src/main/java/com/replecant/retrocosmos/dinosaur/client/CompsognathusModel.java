package com.replecant.retrocosmos.dinosaur.client;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/** Compsognathus: quick bird-like scamper, pecking head and a balancing whip of a tail. */
public class CompsognathusModel extends DinoModel {
    private final ModelPart body;
    private final ModelPart neck;
    private final ModelPart head;
    private final ModelPart tail1;
    private final ModelPart tail2;
    private final ModelPart legL;
    private final ModelPart legR;

    public CompsognathusModel(ModelPart root) {
        super(root, "head", 1.4F);
        body = part("body");
        neck = part("neck");
        head = part("head");
        tail1 = part("tail1");
        tail2 = part("tail2");
        legL = part("leg_l");
        legR = part("leg_r");
    }

    @Override
    public void setupAnim(DinosaurRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        float amount = Math.min(1.0F, s.walkAnimationSpeed * 1.3F);
        float phase = s.walkAnimationPos * 1.1F;
        legL.xRot += Mth.cos(phase) * 1.1F * amount;
        legR.xRot -= Mth.cos(phase) * 1.1F * amount;
        body.y += (1.0F - Math.abs(Mth.cos(phase))) * 0.4F * amount;
        body.xRot += 0.15F * amount;
        neck.xRot -= 0.1F * amount;
        // bird-like head bob and the odd curious peck at the ground
        neck.xRot += Mth.cos(phase * 2.0F) * 0.12F * amount;
        float peck = Mth.sin(t * 0.13F);
        neck.xRot += Math.max(0.0F, peck * peck * peck * peck * peck * peck * peck * peck) * 0.9F * (1.0F - amount);
        neck.xRot += swingPulse(s.attackAnim) * 0.9F;
        head.yRot += s.yRot * DEG * 0.6F;
        head.xRot += s.xRot * DEG * 0.5F;
        tail1.yRot += Mth.sin(t * 0.25F) * 0.15F - Mth.sin(phase) * 0.15F * amount;
        tail2.yRot += Mth.sin(t * 0.25F - 0.8F) * 0.2F;
        applyAge(s);
    }
}
