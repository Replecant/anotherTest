package com.replecant.retrocosmos.dinosaur.robot.client;

import com.replecant.retrocosmos.dinosaur.client.DinoModel;
import com.replecant.retrocosmos.dinosaur.client.DinosaurRenderState;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * Atomic Sentry: the saucer turns its eye where it looks, wobbles as it hovers, the two atom orbits spin round it
 * (faster when alarmed) and the eye flares up while it has a target.
 */
public class AtomicSentryModel extends DinoModel {
    private final ModelPart body;
    private final ModelPart barrel;
    private final ModelPart antenna;
    private final ModelPart core;
    private final ModelPart flare;
    private final ModelPart ringA;
    private final ModelPart ringB;

    public AtomicSentryModel(ModelPart root) {
        super(root, "body", 1.0F);
        body = part("body");
        barrel = part("barrel");
        antenna = part("antenna");
        core = part("core");
        flare = part("eye_flare");
        ringA = part("ring_a");
        ringB = part("ring_b");
    }

    @Override
    public void setupAnim(DinosaurRenderState s) {
        super.setupAnim(s);
        float t = s.ageInTicks;
        float alarm = s.aggressive ? 1.0F : 0.0F;
        body.yRot += s.yRot * DEG;
        body.zRot += Mth.sin(t * 0.07F) * 0.05F;
        body.xRot += Mth.cos(t * 0.06F) * 0.04F;
        barrel.xRot += s.xRot * DEG * 0.7F;
        antenna.zRot += Mth.sin(t * 0.3F) * 0.08F;
        float pulse = 1.0F + Mth.sin(t * (0.15F + alarm * 0.5F)) * 0.12F;
        core.xScale *= pulse;
        core.yScale *= pulse;
        core.zScale *= pulse;
        float spin = t * (0.12F + alarm * 0.25F);
        ringA.yRot += spin;
        ringB.yRot -= spin * 1.3F;
        flare.visible = s.aggressive;
        applyAge(s);
    }
}
