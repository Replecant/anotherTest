package com.replecant.naturequirks.guardianbee.client;

import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/** The vanilla bee's animation (BeeModel.setupAnim): buzzing wings, legs tucked in flight, a lazy bob when calm. */
public class GuardianBeeModel extends EntityModel<GuardianBeeRenderState> {
    private final ModelPart bone;
    private final ModelPart rightWing;
    private final ModelPart leftWing;
    private final ModelPart frontLeg;
    private final ModelPart midLeg;
    private final ModelPart backLeg;
    private final ModelPart leftAntenna;
    private final ModelPart rightAntenna;

    public GuardianBeeModel(ModelPart root) {
        super(root);
        bone = root.getChild("bone");
        ModelPart body = bone.getChild("body");
        leftAntenna = body.getChild("left_antenna");
        rightAntenna = body.getChild("right_antenna");
        rightWing = bone.getChild("right_wing");
        leftWing = bone.getChild("left_wing");
        frontLeg = bone.getChild("front_legs");
        midLeg = bone.getChild("middle_legs");
        backLeg = bone.getChild("back_legs");
    }

    @Override
    public void setupAnim(GuardianBeeRenderState s) {
        super.setupAnim(s);
        if (!s.isOnGround) {
            float f = s.ageInTicks * 120.32113F * Mth.DEG_TO_RAD;
            rightWing.yRot = 0.0F;
            rightWing.zRot = Mth.cos(f) * Mth.PI * 0.15F;
            leftWing.xRot = rightWing.xRot;
            leftWing.yRot = rightWing.yRot;
            leftWing.zRot = -rightWing.zRot;
            frontLeg.xRot = Mth.PI / 4.0F;
            midLeg.xRot = Mth.PI / 4.0F;
            backLeg.xRot = Mth.PI / 4.0F;
        }
        if (!s.isAngry && !s.isOnGround) {
            float c = Mth.cos(s.ageInTicks * 0.18F);
            bone.xRot = 0.1F + c * Mth.PI * 0.025F;
            leftAntenna.xRot = c * Mth.PI * 0.03F;
            rightAntenna.xRot = c * Mth.PI * 0.03F;
            frontLeg.xRot = -c * Mth.PI * 0.1F + Mth.PI / 8.0F;
            backLeg.xRot = -c * Mth.PI * 0.05F + Mth.PI / 4.0F;
            bone.y = bone.y - c * 0.9F;
        }
    }
}
