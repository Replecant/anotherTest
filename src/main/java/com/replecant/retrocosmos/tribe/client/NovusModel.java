package com.replecant.retrocosmos.tribe.client;

import java.util.function.Function;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * Hominid Novus: a heavy knuckle-walk (diagonal pairs, shoulders rolling), a hunched gallop when it charges,
 * a right hook, and the slam - rearing up with both fists over its head, then driving them into the ground.
 */
public class NovusModel extends EntityModel<MutantRenderState> {
    private static final float DEG = Mth.DEG_TO_RAD;
    private final Function<String, ModelPart> parts;
    private final ModelPart body, hips, head, jaw, armL, armR, foreL, foreR, legL, legR;

    public NovusModel(ModelPart root) {
        super(root);
        parts = root.createPartLookup();
        body = part("body");
        hips = part("hips");
        head = part("head");
        jaw = part("jaw");
        armL = part("arm_l");
        armR = part("arm_r");
        foreL = part("forearm_l");
        foreR = part("forearm_r");
        legL = part("leg_l");
        legR = part("leg_r");
    }

    private ModelPart part(String name) {
        ModelPart p = parts.apply(name);
        if (p == null) {
            throw new IllegalStateException("Novus model part missing: " + name);
        }
        return p;
    }

    @Override
    public void setupAnim(MutantRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        float still = 1.0F - Math.max(s.rear, s.impact);
        float amount = Math.min(1.0F, s.walkAnimationSpeed * 1.3F) * still;
        float phase = s.walkAnimationPos * (s.charging ? 0.5F : 0.38F);
        float sin = Mth.sin(phase);
        float cos = Mth.cos(phase);
        float stride = s.charging ? 0.8F : 0.55F;
        armL.xRot += cos * stride * amount;
        armR.xRot -= cos * stride * amount;
        legL.xRot -= cos * stride * 0.9F * amount;
        legR.xRot += cos * stride * 0.9F * amount;
        foreL.xRot -= Math.max(0.0F, cos) * 0.3F * amount;
        foreR.xRot -= Math.max(0.0F, -cos) * 0.3F * amount;
        body.zRot += sin * 0.06F * amount;
        body.yRot += sin * 0.05F * amount;
        body.y += Math.abs(sin) * 1.2F * amount;
        hips.y += Math.abs(sin) * 1.0F * amount;
        if (s.charging) {
            body.xRot += 0.15F;
            head.xRot -= 0.15F;
        }
        // breathing; looking about
        body.xRot += Mth.sin(t * 0.06F) * 0.025F;
        head.yRot += s.yRot * DEG * 0.6F;
        head.xRot += s.xRot * DEG * 0.5F;
        float snarl = s.aggressive || s.charging ? 0.25F + 0.15F * Mth.sin(t * 0.3F) : 0.05F + 0.04F * Mth.sin(t * 0.08F);
        jaw.xRot += snarl + s.rear * 0.5F;
        // a right hook
        float hit = s.attackAnim <= 0.0F ? 0.0F : Mth.sin(s.attackAnim * Mth.PI);
        armR.xRot -= hit * 1.3F;
        armR.zRot += hit * 0.3F;
        foreR.xRot -= hit * 0.4F;
        body.yRot -= hit * 0.25F;
        // the slam
        TribeGeometry.applyPose(parts, TribeGeometry.NOVUS_REAR, s.rear);
        TribeGeometry.applyPose(parts, TribeGeometry.NOVUS_SLAM, s.impact);
        if (s.rear > 0.0F) {
            ModelPart r = root();
            r.y -= 4.0F * s.rear;  // up on its hind legs
        }
    }
}
