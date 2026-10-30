package com.replecant.retrocosmos.tribe.boss.client;

import com.replecant.retrocosmos.tribe.client.TribeGeometry;
import java.util.function.Function;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * Homo Novus: a lurching, heavy-armed run, the brain throbbing in its flask (faster in a rage), the crouch, the
 * leap with both fists overhead and the slam, the two-handed grab, the head-back psychic scream.
 */
public class HomoNovusModel extends EntityModel<BossRenderState> {
    private static final float DEG = Mth.DEG_TO_RAD;
    private final Function<String, ModelPart> parts;
    private final ModelPart body, head, brain, armL, armR, foreL, foreR, legL, legR, coattail;

    public HomoNovusModel(ModelPart root) {
        super(root);
        parts = root.createPartLookup();
        body = part("body");
        head = part("head");
        brain = part("brain");
        armL = part("arm_l");
        armR = part("arm_r");
        foreL = part("forearm_l");
        foreR = part("forearm_r");
        legL = part("leg_l");
        legR = part("leg_r");
        coattail = part("coattail");
    }

    private ModelPart part(String name) {
        ModelPart p = parts.apply(name);
        if (p == null) {
            throw new IllegalStateException("Homo Novus model part missing: " + name);
        }
        return p;
    }

    @Override
    public void setupAnim(BossRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        float busy = Math.max(Math.max(s.crouch, s.leap), Math.max(s.grab, s.scream));
        float amount = Math.min(1.0F, s.walkAnimationSpeed * 1.2F) * (1.0F - busy);
        float phase = s.walkAnimationPos * 0.45F;
        float cos = Mth.cos(phase);
        float sin = Mth.sin(phase);
        legL.xRot += cos * 0.75F * amount;
        legR.xRot -= cos * 0.75F * amount;
        armL.xRot -= cos * 0.55F * amount;
        armR.xRot += cos * 0.55F * amount;
        foreL.xRot -= Math.max(0.0F, cos) * 0.3F * amount;
        foreR.xRot -= Math.max(0.0F, -cos) * 0.3F * amount;
        body.zRot += sin * 0.06F * amount;
        body.y += Math.abs(sin) * 1.0F * amount;
        coattail.xRot -= Math.abs(cos) * 0.25F * amount;
        head.yRot += s.yRot * DEG * 0.7F;
        head.xRot += s.xRot * DEG * 0.6F;
        // heaving breath; the brain throbs
        float breath = s.rage ? 0.25F : 0.08F;
        body.xRot += Mth.sin(t * breath) * 0.03F;
        float pulse = 1.0F + Mth.sin(t * (s.rage ? 0.7F : 0.22F)) * (s.rage ? 0.06F : 0.035F);
        brain.xScale = pulse;
        brain.yScale = pulse;
        brain.zScale = pulse;
        if (s.rage) {
            body.xRot += 0.12F;
            armL.zRot -= 0.15F;
            armR.zRot += 0.15F;
        }
        // a two-fisted haymaker
        float hit = s.attackAnim <= 0.0F ? 0.0F : Mth.sin(s.attackAnim * Mth.PI);
        armR.xRot -= hit * 1.6F;
        armL.xRot -= hit * 0.6F;
        body.yRot -= hit * 0.3F;
        // specials
        TribeGeometry.applyPose(parts, TribeGeometry.HOMO_CROUCH, s.crouch);
        if (s.crouch > 0.0F) {
            root().y += 4.0F * s.crouch;
        }
        if (s.leap > 0.0F) {
            armL.xRot -= 2.7F * s.leap;
            armR.xRot -= 2.7F * s.leap;
            legL.xRot -= 0.5F * s.leap;
            legR.xRot -= 0.3F * s.leap;
            body.xRot -= 0.2F * s.leap;
        }
        if (s.slam > 0.0F) {
            armL.xRot -= 1.1F * s.slam;
            armR.xRot -= 1.1F * s.slam;
            body.xRot += 0.5F * s.slam;
            root().y += 3.0F * s.slam;
        }
        TribeGeometry.applyPose(parts, TribeGeometry.HOMO_GRAB, s.grab);
        TribeGeometry.applyPose(parts, TribeGeometry.HOMO_SCREAM, s.scream);
        if (s.scream > 0.0F) {
            head.yRot += Mth.sin(t * 2.0F) * 0.15F * s.scream;
        }
    }
}
