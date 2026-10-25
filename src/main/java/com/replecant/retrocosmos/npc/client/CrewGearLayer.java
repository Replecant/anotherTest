package com.replecant.retrocosmos.npc.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.npc.CrewRole;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.resources.Identifier;

/** The 3D accessories (fedora brim, satchel, helmet visor, radio pack, holster, ray pistol, stun baton). */
public class CrewGearLayer extends RenderLayer<CrewRenderState, CrewModel> {
    private static final Identifier TEXTURE = Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "textures/entity/npc/gear.png");
    private final CrewModel model;

    public CrewGearLayer(RenderLayerParent<CrewRenderState, CrewModel> parent, CrewModel model) {
        super(parent);
        this.model = model;
    }

    @Override
    public void submit(PoseStack poseStack, SubmitNodeCollector collector, int light, CrewRenderState state, float yRot, float xRot) {
        if (state.isInvisible || state.role == CrewRole.SCIENTIST.ordinal()) {
            return;
        }
        model.setupAnim(state);
        renderColoredCutoutModel(model, TEXTURE, poseStack, collector, light, state, -1, 1);
    }
}
