package com.replecant.retrocosmos.dinosaur.client;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * Venus Creeper: the vanilla creeper body and walk, exactly; only the leaf fringe at the neck flares and the spore
 * bulb throbs while the fuse burns.
 */
public class VenusCreeperModel extends DinoModel {
    private final ModelPart head;
    private final ModelPart bulb;
    private final ModelPart leafFront;
    private final ModelPart leafBack;
    private final ModelPart leafL;
    private final ModelPart leafR;
    private final ModelPart legFrontL;
    private final ModelPart legFrontR;
    private final ModelPart legBackL;
    private final ModelPart legBackR;

    public VenusCreeperModel(ModelPart root) {
        super(root, "head", 1.0F);
        head = part("head");
        bulb = part("bulb");
        leafFront = part("leaf_front");
        leafBack = part("leaf_back");
        leafL = part("leaf_l");
        leafR = part("leaf_r");
        legFrontL = part("leg_front_l");
        legFrontR = part("leg_front_r");
        legBackL = part("leg_back_l");
        legBackR = part("leg_back_r");
    }

    @Override
    public void setupAnim(DinosaurRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        // vanilla CreeperModel walk: diagonal leg pairs, 1.4 rad swing
        float swing = Mth.cos(s.walkAnimationPos * 0.6662F) * 1.4F * s.walkAnimationSpeed;
        legFrontL.xRot += swing;
        legBackR.xRot += swing;
        legFrontR.xRot -= swing;
        legBackL.xRot -= swing;

        head.yRot += s.yRot * DEG;
        head.xRot += s.xRot * DEG;

        // sepals flutter, then flare wide open as the fuse burns
        float flutter = Mth.sin(t * 0.15F) * 0.05F;
        float flare = s.swell * 0.6F;
        leafFront.xRot += flutter - flare;
        leafBack.xRot -= flutter - flare;
        leafL.zRot += flutter - flare;
        leafR.zRot -= flutter - flare;

        // the spore bulb nods on its stem and swells with the fuse
        bulb.xRot += Mth.sin(t * 0.09F) * 0.1F;
        bulb.zRot += Mth.cos(t * 0.07F) * 0.08F;
        float pulse = 1.0F + s.swell * 0.45F + Mth.sin(t * (0.2F + s.swell * 1.2F)) * (0.03F + s.swell * 0.08F);
        bulb.xScale *= pulse;
        bulb.yScale *= pulse;
        bulb.zScale *= pulse;
        applyAge(s);
    }
}
