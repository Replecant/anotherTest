package com.replecant.retrocosmos.dinosaur.client;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * Pteranodon: slow heavy wing-beats with a lagging wingtip, banking and pitching with the flight path; on the roost
 * the wings fold like a cloak, and in the stoop they sweep back.
 */
public class PteranodonModel extends DinoModel {
    private final ModelPart body;
    private final ModelPart neck;
    private final ModelPart head;
    private final ModelPart jaw;
    private final ModelPart tail;
    private final ModelPart wingL;
    private final ModelPart wingR;
    private final ModelPart tipL;
    private final ModelPart tipR;

    public PteranodonModel(ModelPart root) {
        super(root, "head", 1.0F);
        body = part("body");
        neck = part("neck");
        head = part("head");
        jaw = part("jaw");
        tail = part("tail");
        wingL = part("wing_l");
        wingR = part("wing_r");
        tipL = part("wingtip_l");
        tipR = part("wingtip_r");
    }

    @Override
    public void setupAnim(DinosaurRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        float flying = 1.0F - s.perch;

        // the whole body pitches with the flight path
        body.xRot += Mth.clamp(s.flightPitch, -0.7F, 0.9F) * flying * (1.0F - s.dive);

        // wing-beats: big and slow, the tips trailing; gliding when diving
        float beat = 0.55F * flying * (1.0F - s.dive * 0.85F);
        float phase = t * 0.42F;
        wingL.zRot += Mth.sin(phase) * beat;
        wingR.zRot -= Mth.sin(phase) * beat;
        tipL.zRot += Mth.sin(phase - 0.7F) * beat * 0.7F;
        tipR.zRot -= Mth.sin(phase - 0.7F) * beat * 0.7F;
        body.y -= Mth.cos(phase) * 0.6F * beat;

        // head looks around, beak opens in a screech now and then
        neck.yRot += s.yRot * DEG * 0.4F;
        head.yRot += s.yRot * DEG * 0.4F;
        head.xRot += s.xRot * DEG * 0.5F;
        float squawk = Mth.sin(t * 0.05F);
        jaw.xRot += Math.max(0.0F, squawk * squawk * squawk * squawk * squawk * squawk) * 0.45F + (s.aggressive ? 0.25F : 0.0F);
        tail.yRot += Mth.sin(t * 0.1F) * 0.1F;

        DinoGeometry.applyPose(parts, DinoGeometry.PTERANODON_PERCH, s.perch);
        DinoGeometry.applyPose(parts, DinoGeometry.PTERANODON_DIVE, s.dive * flying);
        if (s.perch > 0.0F) {
            // fidgets on the roost: breathing, a shuffle of the folded wings
            body.xRot += Mth.sin(t * 0.08F) * 0.03F * s.perch;
            wingL.zRot -= Math.max(0.0F, Mth.sin(t * 0.03F)) * 0.15F * s.perch;
            wingR.zRot += Math.max(0.0F, Mth.sin(t * 0.03F)) * 0.15F * s.perch;
        }
        applyAge(s);
    }
}
