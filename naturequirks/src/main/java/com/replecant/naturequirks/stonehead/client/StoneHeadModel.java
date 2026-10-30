package com.replecant.naturequirks.stonehead.client;

import com.replecant.naturequirks.stonehead.StoneHead;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * The head turns only a little toward you - the eyes do most of the following. Chewing works the great jaw up and
 * down with a slight nod; a grumble is a slow, heavy shake of the head.
 */
public class StoneHeadModel extends EntityModel<StoneHeadRenderState> {
    private final ModelPart head;
    private final ModelPart jaw;
    private final ModelPart pupilLeft;
    private final ModelPart pupilRight;

    public StoneHeadModel(ModelPart root) {
        super(root);
        ModelPart base = root.getChild("base");
        head = base.getChild("head");
        jaw = head.getChild("jaw");
        pupilLeft = head.getChild("pupil_l");
        pupilRight = head.getChild("pupil_r");
    }

    @Override
    public void setupAnim(StoneHeadRenderState s) {
        super.setupAnim(s);
        float yaw = Mth.clamp(s.yRot, -35.0F, 35.0F);
        float pitch = Mth.clamp(s.xRot, -25.0F, 25.0F);
        head.yRot = yaw * 0.35F * Mth.DEG_TO_RAD;
        head.xRot = pitch * 0.2F * Mth.DEG_TO_RAD;
        // the eyes slide toward whatever it looks at (a positive yaw swings the face toward -x)
        float ex = -Mth.clamp(yaw / 28.0F, -1.0F, 1.0F) * 1.0F;
        float ey = Mth.clamp(pitch / 25.0F, -1.0F, 1.0F) * 0.5F;
        pupilLeft.x += ex;
        pupilRight.x += ex;
        pupilLeft.y += ey;
        pupilRight.y += ey;
        if (s.chew > 0.0F) {
            float bite = 0.5F - 0.5F * Mth.cos(s.chew * 0.9F);
            jaw.xRot = 0.3F * bite;
            head.xRot += 0.04F * Mth.sin(s.chew * 0.9F);
            if (s.chew > StoneHead.CHEW_TICKS - 6) {
                jaw.xRot = 0.42F;  // and... ptoo
            }
        }
        if (s.grumble > 0.0F) {
            float left = s.grumble / StoneHead.GRUMBLE_TICKS;
            head.yRot += Mth.sin(s.grumble * 0.9F) * 0.12F * left;
            jaw.xRot = Math.max(jaw.xRot, 0.06F * left);
        }
    }
}
