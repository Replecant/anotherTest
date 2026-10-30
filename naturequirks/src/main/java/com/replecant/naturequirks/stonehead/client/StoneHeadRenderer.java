package com.replecant.naturequirks.stonehead.client;

import com.replecant.naturequirks.NatureQuirks;
import com.replecant.naturequirks.stonehead.StoneHead;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.resources.Identifier;

public class StoneHeadRenderer extends MobRenderer<StoneHead, StoneHeadRenderState, StoneHeadModel> {
    public static final ModelLayerLocation LAYER = new ModelLayerLocation(
            Identifier.fromNamespaceAndPath(NatureQuirks.MODID, "stone_head"), "main");
    private static final Identifier TEXTURE = Identifier.fromNamespaceAndPath(NatureQuirks.MODID,
            "textures/entity/stone_head/stone_head.png");

    public StoneHeadRenderer(EntityRendererProvider.Context context) {
        super(context, new StoneHeadModel(context.bakeLayer(LAYER)), 0.9F);
    }

    @Override
    public StoneHeadRenderState createRenderState() {
        return new StoneHeadRenderState();
    }

    @Override
    public void extractRenderState(StoneHead head, StoneHeadRenderState state, float partialTick) {
        super.extractRenderState(head, state, partialTick);
        state.chew = head.chewTime(partialTick);
        state.grumble = head.grumbleTime(partialTick);
    }

    @Override
    public Identifier getTextureLocation(StoneHeadRenderState state) {
        return TEXTURE;
    }
}
