package com.replecant.retrocosmos.npc.client;

import com.replecant.retrocosmos.npc.CrewRole;
import com.replecant.retrocosmos.npc.ExpeditionMember;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * The crew's humanoid model, used twice: once with the vanilla player mesh (the skin), once with the gear mesh
 * (hat brim, helmet, packs, weapons - parts are only present there). On top of the vanilla humanoid animation it
 * adds the crew's work poses: punching keys, writing in a notebook, dusting a relic, hands clasped behind the back,
 * a salute, and aiming the ray pistol.
 */
public class CrewModel extends HumanoidModel<CrewRenderState> {
    private final List<ModelPart> gear = new ArrayList<>();
    private final List<String> groups = new ArrayList<>();

    public CrewModel(ModelPart root) {
        super(root);
        Function<String, ModelPart> parts = root.createPartLookup();
        for (Map.Entry<String, String> e : CrewGeometry.GEAR_GROUPS.entrySet()) {
            ModelPart part = parts.apply(e.getKey());
            if (part != null) {
                gear.add(part);
                groups.add(e.getValue());
            }
        }
    }

    private static boolean shows(String group, CrewRenderState s) {
        return switch (group) {
            case "cooper" -> s.role == CrewRole.COOPER.ordinal();
            case "guard" -> s.role == CrewRole.GUARD.ordinal();
            case "holstered" -> s.role == CrewRole.GUARD.ordinal() && s.weapon != ExpeditionMember.WEAPON_PISTOL;
            case "pistol" -> s.role == CrewRole.GUARD.ordinal() && s.weapon == ExpeditionMember.WEAPON_PISTOL;
            case "baton" -> s.role == CrewRole.GUARD.ordinal() && s.weapon == ExpeditionMember.WEAPON_BATON;
            default -> false;
        };
    }

    @Override
    public void setupAnim(CrewRenderState s) {
        super.setupAnim(s);
        for (int i = 0; i < gear.size(); i++) {
            gear.get(i).visible = shows(groups.get(i), s);
        }
        float t = s.ageInTicks;
        switch (s.action) {
            case ExpeditionMember.ACT_TYPING -> {
                // both hands busy at the instrument
                rightArm.xRot = -0.95F + Mth.sin(t * 0.8F) * 0.1F;
                rightArm.yRot = -0.25F;
                rightArm.zRot = 0.0F;
                leftArm.xRot = -0.95F + Mth.sin(t * 0.8F + 1.7F) * 0.1F;
                leftArm.yRot = 0.25F;
                leftArm.zRot = 0.0F;
            }
            case ExpeditionMember.ACT_NOTES -> {
                // notebook in the right hand, the left one scribbling, head bowed over it
                rightArm.xRot = -1.05F;
                rightArm.yRot = -0.42F;
                rightArm.zRot = 0.0F;
                leftArm.xRot = -0.85F + Mth.sin(t * 1.7F) * 0.05F;
                leftArm.yRot = 0.5F + Mth.cos(t * 1.1F) * 0.06F;
                leftArm.zRot = 0.0F;
                head.xRot = Math.max(head.xRot, 0.45F);
            }
            case ExpeditionMember.ACT_INSPECT -> {
                // reaching in to dust, sample or prod, the other hand on the hip
                rightArm.xRot = -0.8F + Mth.sin(t * 0.45F) * 0.12F;
                rightArm.yRot = -0.15F;
                rightArm.zRot = Mth.sin(t * 0.9F) * 0.12F;
                leftArm.xRot = 0.0F;
                leftArm.yRot = 0.0F;
                leftArm.zRot = -0.38F;
            }
            case ExpeditionMember.ACT_AT_EASE -> {
                // parade rest: hands clasped behind the back
                rightArm.xRot = 0.42F;
                rightArm.yRot = 0.0F;
                rightArm.zRot = -0.14F;
                leftArm.xRot = 0.42F;
                leftArm.yRot = 0.0F;
                leftArm.zRot = 0.14F;
            }
            case ExpeditionMember.ACT_SALUTE -> {
                rightArm.xRot = -2.53F;
                rightArm.yRot = -0.57F;
                rightArm.zRot = 0.0F;
                leftArm.xRot = 0.0F;
                leftArm.zRot = 0.0F;
            }
            default -> {
            }
        }
        if (s.weapon == ExpeditionMember.WEAPON_PISTOL) {
            rightArm.xRot = head.xRot - Mth.HALF_PI;
            rightArm.yRot = head.yRot - 0.06F;
            rightArm.zRot = 0.0F;
        }
    }
}
