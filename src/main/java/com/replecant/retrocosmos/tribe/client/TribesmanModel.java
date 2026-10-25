package com.replecant.retrocosmos.tribe.client;

import com.replecant.retrocosmos.tribe.TribeRole;
import java.util.Map;
import java.util.function.Function;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * The stooped, long-armed tribesman: a rolling ape-man walk with swinging knuckles, breathing and looking around,
 * a spear thrust (or the chief's overhead club smash), a head-shake when refusing, squatting by the fire and a
 * hopping, arm-waving fire dance.
 */
public class TribesmanModel extends EntityModel<TribesmanRenderState> {
    private static final float DEG = Mth.DEG_TO_RAD;
    private final Function<String, ModelPart> parts;
    private final ModelPart hips;
    private final ModelPart flapFront;
    private final ModelPart flapBack;
    private final ModelPart body;
    private final ModelPart head;
    private final ModelPart armL;
    private final ModelPart armR;
    private final ModelPart legL;
    private final ModelPart legR;
    private final ModelPart[] roleParts;
    private final int[][] roleMasks;

    public TribesmanModel(ModelPart root) {
        super(root);
        this.parts = root.createPartLookup();
        hips = part("hips");
        flapFront = part("flap_front");
        flapBack = part("flap_back");
        body = part("body");
        head = part("head");
        armL = part("arm_l");
        armR = part("arm_r");
        legL = part("leg_l");
        legR = part("leg_r");
        roleParts = new ModelPart[TribeGeometry.ROLE_PARTS.size()];
        roleMasks = new int[roleParts.length][];
        int i = 0;
        for (Map.Entry<String, int[]> e : TribeGeometry.ROLE_PARTS.entrySet()) {
            roleParts[i] = part(e.getKey());
            roleMasks[i] = e.getValue();
            i++;
        }
    }

    private ModelPart part(String name) {
        ModelPart part = parts.apply(name);
        if (part == null) {
            throw new IllegalStateException("Tribesman model part missing: " + name);
        }
        return part;
    }

    @Override
    public void setupAnim(TribesmanRenderState s) {
        super.setupAnim(s);
        for (int i = 0; i < roleParts.length; i++) {
            boolean shown = false;
            for (int r : roleMasks[i]) {
                shown |= r == s.role;
            }
            roleParts[i].visible = shown;
        }
        float t = s.ageInTicks;
        float still = (1.0F - s.sit) * (1.0F - s.dance);
        float amount = Math.min(1.0F, s.walkAnimationSpeed * 1.4F) * still;
        float phase = s.walkAnimationPos * 0.62F;
        float sin = Mth.sin(phase);
        float cos = Mth.cos(phase);

        // rolling, bow-legged gait; long arms swing opposite and knuckles brush the ferns
        legL.xRot += cos * 0.85F * amount;
        legR.xRot -= cos * 0.85F * amount;
        armL.xRot -= cos * 0.55F * amount;
        armR.xRot += cos * 0.55F * amount;
        float bob = Math.abs(sin) * 0.9F * amount;
        body.y += bob;
        hips.y += bob;
        body.zRot += sin * 0.06F * amount;
        body.yRot += sin * 0.05F * amount;
        flapFront.xRot -= Math.abs(cos) * 0.35F * amount;
        flapBack.xRot += Math.abs(cos) * 0.3F * amount;

        // idle: breathing, a lazy sway of the arms
        float breathe = Mth.sin(t * 0.07F);
        body.xRot += breathe * 0.02F;
        armL.zRot -= (0.03F + breathe * 0.03F) * still;
        armR.zRot += (0.03F + breathe * 0.03F) * still;
        flapFront.xRot += Mth.sin(t * 0.05F) * 0.04F;

        // where it looks
        head.yRot += s.yRot * DEG * 0.85F;
        head.xRot += s.xRot * DEG * 0.7F;
        if (s.unhappy) {
            head.zRot += 0.3F * Mth.sin(t * 0.45F);
            head.yRot += 0.2F * Mth.sin(t * 0.45F);
        }

        // fighting: weapon raised, then the strike
        boolean chief = s.role == TribeRole.CHIEF.ordinal();
        if (s.aggressive) {
            armR.xRot -= chief ? 0.8F : 0.45F;
            body.xRot += 0.08F;
        }
        float strike = s.attackAnim <= 0.0F ? 0.0F : Mth.sin(s.attackAnim * Mth.PI);
        if (chief) {
            // up over the head on the way in, smashing down on the way out
            float up = s.attackAnim < 0.5F ? Mth.sin(s.attackAnim * Mth.PI) : 1.0F - (s.attackAnim - 0.5F) * 2.6F;
            TribeGeometry.applyPose(parts, TribeGeometry.SMASH, Math.max(-0.3F, up));
        } else {
            TribeGeometry.applyPose(parts, TribeGeometry.THRUST, strike);
        }

        // squatting by the fire
        TribeGeometry.applyPose(parts, TribeGeometry.SIT, s.sit);
        armL.xRot += Mth.sin(t * 0.03F) * 0.05F * s.sit;

        // the dance: arms up and waving, hop from foot to foot, twisting back and forth
        if (s.dance > 0.0F) {
            TribeGeometry.applyPose(parts, TribeGeometry.DANCE, s.dance);
            float beat = t * 0.42F;
            armL.zRot -= Mth.sin(beat) * 0.35F * s.dance;
            armR.zRot += Mth.sin(beat) * 0.35F * s.dance;
            armL.xRot += Mth.cos(beat) * 0.3F * s.dance;
            armR.xRot -= Mth.cos(beat) * 0.3F * s.dance;
            legL.xRot += Mth.sin(beat) * 0.45F * s.dance;
            legR.xRot -= Mth.sin(beat) * 0.45F * s.dance;
            head.xRot += Mth.sin(beat * 2.0F) * 0.15F * s.dance;
        }

        // babies: small with a big head; scaling about the ground keeps their feet down
        ModelPart root = root();
        float scale = s.isBaby ? 0.55F : 1.0F;
        root.xScale = scale;
        root.yScale = scale;
        root.zScale = scale;
        root.y = 24.0F * (1.0F - scale) + 7.5F * s.sit * scale;
        if (s.dance > 0.0F) {
            root.y -= Math.abs(Mth.sin(t * 0.42F)) * 2.2F * s.dance * scale;
            root.yRot += Mth.sin(t * 0.09F) * 0.9F * s.dance;
        }
        if (s.isBaby) {
            head.xScale = 1.35F;
            head.yScale = 1.35F;
            head.zScale = 1.35F;
        }
    }
}
