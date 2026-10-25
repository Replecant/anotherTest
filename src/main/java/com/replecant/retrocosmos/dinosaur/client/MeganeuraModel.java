package com.replecant.retrocosmos.dinosaur.client;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.util.Mth;

/** Meganeura: four glassy wings in a blur (drawn translucent), the long tail bobbing as it hovers. */
public class MeganeuraModel extends DinoModel {
    private final ModelPart thorax;
    private final ModelPart abdomen;
    private final ModelPart frontL;
    private final ModelPart frontR;
    private final ModelPart backL;
    private final ModelPart backR;

    public MeganeuraModel(ModelPart root) {
        super(root, "head", 1.0F, RenderTypes::entityTranslucent);
        thorax = part("thorax");
        abdomen = part("abdomen");
        frontL = part("wing_front_l");
        frontR = part("wing_front_r");
        backL = part("wing_back_l");
        backR = part("wing_back_r");
    }

    @Override
    public void setupAnim(DinosaurRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        float beat = t * 2.7F;
        frontL.zRot += Mth.sin(beat) * 0.55F;
        frontR.zRot -= Mth.sin(beat) * 0.55F;
        backL.zRot += Mth.sin(beat + 1.4F) * 0.55F;
        backR.zRot -= Mth.sin(beat + 1.4F) * 0.55F;
        thorax.y += Mth.sin(t * 0.3F) * 0.4F;
        abdomen.xRot += Mth.sin(t * 0.2F) * 0.08F;
        applyAge(s);
    }
}
