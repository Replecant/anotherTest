package com.replecant.naturequirks.flowercreeper.client;

import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/** The vanilla creeper's model and walk: head follows the look, legs swing in diagonal pairs. */
public class FlowerCreeperModel extends EntityModel<FlowerCreeperRenderState> {
    private final ModelPart head;
    private final ModelPart body;
    private final ModelPart rightHindLeg;
    private final ModelPart leftHindLeg;
    private final ModelPart rightFrontLeg;
    private final ModelPart leftFrontLeg;

    public FlowerCreeperModel(ModelPart root) {
        super(root);
        head = root.getChild("head");
        body = root.getChild("body");
        rightHindLeg = root.getChild("right_hind_leg");
        leftHindLeg = root.getChild("left_hind_leg");
        rightFrontLeg = root.getChild("right_front_leg");
        leftFrontLeg = root.getChild("left_front_leg");
    }

    public ModelPart head() {
        return head;
    }

    public ModelPart body() {
        return body;
    }

    @Override
    public void setupAnim(FlowerCreeperRenderState s) {
        super.setupAnim(s);
        head.yRot = s.yRot * Mth.DEG_TO_RAD;
        head.xRot = s.xRot * Mth.DEG_TO_RAD;
        float pos = s.walkAnimationPos;
        float speed = s.walkAnimationSpeed;
        rightHindLeg.xRot = Mth.cos(pos * 0.6662F) * 1.4F * speed;
        leftHindLeg.xRot = Mth.cos(pos * 0.6662F + Mth.PI) * 1.4F * speed;
        rightFrontLeg.xRot = Mth.cos(pos * 0.6662F + Mth.PI) * 1.4F * speed;
        leftFrontLeg.xRot = Mth.cos(pos * 0.6662F) * 1.4F * speed;
    }
}
