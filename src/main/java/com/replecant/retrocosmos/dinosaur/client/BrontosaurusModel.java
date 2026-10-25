package com.replecant.retrocosmos.dinosaur.client;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * Brontosaurus: slow, heavy, elephant-like gait; the long neck sways and bobs, the tail swings in a lazy wave,
 * and when grazing the whole neck swings down to the ground while the head chews.
 */
public class BrontosaurusModel extends DinoModel {
    private final ModelPart body;
    private final ModelPart neck1;
    private final ModelPart neck2;
    private final ModelPart neck3;
    private final ModelPart head;
    private final ModelPart[] tail;
    private final ModelPart legFrontL;
    private final ModelPart legFrontR;
    private final ModelPart legBackL;
    private final ModelPart legBackR;

    public BrontosaurusModel(ModelPart root) {
        super(root, "head", 1.6F);
        body = part("body");
        neck1 = part("neck1");
        neck2 = part("neck2");
        neck3 = part("neck3");
        head = part("head");
        tail = new ModelPart[]{part("tail1"), part("tail2"), part("tail3"), part("tail4")};
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
        float phase = s.walkAnimationPos * 0.32F;
        float sin = Mth.sin(phase);
        float cos = Mth.cos(phase);

        // diagonal pairs of pillar legs, short heavy swings
        float swing = cos * 0.36F * amount;
        legFrontL.xRot += swing;
        legBackR.xRot += swing;
        legFrontR.xRot -= swing;
        legBackL.xRot -= swing;

        // the great body rolls and sags with each footfall
        body.zRot += sin * 0.035F * amount;
        body.y += Math.abs(sin) * 0.8F * amount;

        // neck: slow idle sway, bob with the steps, follow the look direction (less while grazing)
        float look = 1.0F - s.graze;
        float sway = Mth.sin(t * 0.03F) * 0.08F;
        neck1.yRot += sway + s.yRot * DEG * 0.2F * look;
        neck2.yRot += sway * 0.8F + s.yRot * DEG * 0.25F * look;
        neck3.yRot += sway * 0.6F + s.yRot * DEG * 0.25F * look;
        head.yRot += s.yRot * DEG * 0.2F * look;
        neck1.xRot += Mth.sin(t * 0.045F) * 0.025F + Math.abs(sin) * 0.05F * amount;
        neck3.xRot += s.xRot * DEG * 0.25F * look;
        head.xRot += s.xRot * DEG * 0.35F * look;

        // tail: a lazy travelling wave down the four segments, a bit livelier when walking
        for (int i = 0; i < tail.length; i++) {
            float wave = Mth.sin(t * 0.05F - i * 0.7F) * (0.06F + 0.03F * i);
            tail[i].yRot += wave + Mth.sin(phase - i * 0.6F) * 0.07F * amount;
            tail[i].xRot += Mth.sin(t * 0.04F - i * 0.5F) * 0.015F;
        }

        // grazing: neck down to the ground, chewing
        DinoGeometry.applyPose(parts, DinoGeometry.BRONTOSAURUS_GRAZE, s.graze);
        head.xRot += Mth.sin(t * 0.45F) * 0.09F * s.graze;
        neck3.yRot += Mth.sin(t * 0.06F) * 0.15F * s.graze;
        applyAge(s);
    }
}
