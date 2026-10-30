package com.replecant.retrocosmos.dinosaur.client;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/** Spore moth: lazy, deep wing-beats, feathery antennae twitching. */
public class SporeMothModel extends DinoModel {
    private final ModelPart body;
    private final ModelPart wingL;
    private final ModelPart wingR;
    private final ModelPart hindL;
    private final ModelPart hindR;
    private final ModelPart antennaL;
    private final ModelPart antennaR;

    public SporeMothModel(ModelPart root) {
        super(root, "head", 1.0F);
        body = part("body");
        wingL = part("wing_l");
        wingR = part("wing_r");
        hindL = part("hindwing_l");
        hindR = part("hindwing_r");
        antennaL = part("antenna_l");
        antennaR = part("antenna_r");
    }

    @Override
    public void setupAnim(DinosaurRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        float beat = Mth.sin(t * 0.7F) * 0.75F;
        wingL.zRot += beat;
        wingR.zRot -= beat;
        hindL.zRot += beat * 0.8F;
        hindR.zRot -= beat * 0.8F;
        body.y -= Mth.cos(t * 0.7F) * 0.5F;
        body.xRot += Mth.sin(t * 0.05F) * 0.1F;
        antennaL.zRot += Mth.sin(t * 0.3F) * 0.1F;
        antennaR.zRot -= Mth.sin(t * 0.3F + 0.5F) * 0.1F;
        applyAge(s);
    }
}
