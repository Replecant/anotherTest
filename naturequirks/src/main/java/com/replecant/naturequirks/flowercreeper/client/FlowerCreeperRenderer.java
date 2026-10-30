package com.replecant.naturequirks.flowercreeper.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.replecant.naturequirks.NatureQuirks;
import com.replecant.naturequirks.flowercreeper.FlowerCreeper;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;

/** Drawn like the vanilla creeper (the fuse bloats and flashes it white), plus the flowers growing on it. */
public class FlowerCreeperRenderer extends MobRenderer<FlowerCreeper, FlowerCreeperRenderState, FlowerCreeperModel> {
    public static final ModelLayerLocation LAYER = new ModelLayerLocation(
            Identifier.fromNamespaceAndPath(NatureQuirks.MODID, "flower_creeper"), "main");
    private static final Identifier TEXTURE = Identifier.fromNamespaceAndPath(NatureQuirks.MODID,
            "textures/entity/flower_creeper/flower_creeper.png");

    public FlowerCreeperRenderer(EntityRendererProvider.Context context) {
        super(context, new FlowerCreeperModel(context.bakeLayer(LAYER)), 0.5F);
        addLayer(new FlowerCreeperFlowerLayer(this));
    }

    @Override
    public FlowerCreeperRenderState createRenderState() {
        return new FlowerCreeperRenderState();
    }

    @Override
    public void extractRenderState(FlowerCreeper creeper, FlowerCreeperRenderState state, float partialTick) {
        super.extractRenderState(creeper, state, partialTick);
        state.swelling = creeper.getSwelling(partialTick);
        state.flowerSeed = creeper.getUUID().getLeastSignificantBits();
    }

    @Override
    protected void scale(FlowerCreeperRenderState state, PoseStack poseStack) {
        float f = state.swelling;
        float wobble = 1.0F + Mth.sin(f * 100.0F) * f * 0.01F;
        f = Mth.clamp(f, 0.0F, 1.0F);
        f *= f;
        f *= f;
        float wide = (1.0F + f * 0.4F) * wobble;
        float tall = (1.0F + f * 0.1F) / wobble;
        poseStack.scale(wide, tall, wide);
    }

    @Override
    protected float getWhiteOverlayProgress(FlowerCreeperRenderState state) {
        return whiteFlash(state.swelling);
    }

    static float whiteFlash(float swelling) {
        return (int) (swelling * 10.0F) % 2 == 0 ? 0.0F : Mth.clamp(swelling, 0.5F, 1.0F);
    }

    @Override
    public Identifier getTextureLocation(FlowerCreeperRenderState state) {
        return TEXTURE;
    }
}
