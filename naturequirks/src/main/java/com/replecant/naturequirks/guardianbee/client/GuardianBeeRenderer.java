package com.replecant.naturequirks.guardianbee.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.replecant.naturequirks.NatureQuirks;
import com.replecant.naturequirks.guardianbee.GuardianBee;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.resources.Identifier;

/** Drawn 1.4x the size of a vanilla bee; the eyes glare red while it's on the attack. */
public class GuardianBeeRenderer extends MobRenderer<GuardianBee, GuardianBeeRenderState, GuardianBeeModel> {
    public static final ModelLayerLocation LAYER = new ModelLayerLocation(
            Identifier.fromNamespaceAndPath(NatureQuirks.MODID, "guardian_bee"), "main");
    public static final float SCALE = 1.4F;
    private static final Identifier CALM = Identifier.fromNamespaceAndPath(NatureQuirks.MODID, "textures/entity/guardian_bee/guardian_bee.png");
    private static final Identifier ANGRY = Identifier.fromNamespaceAndPath(NatureQuirks.MODID, "textures/entity/guardian_bee/guardian_bee_angry.png");

    public GuardianBeeRenderer(EntityRendererProvider.Context context) {
        super(context, new GuardianBeeModel(context.bakeLayer(LAYER)), 0.4F * SCALE);
    }

    @Override
    public GuardianBeeRenderState createRenderState() {
        return new GuardianBeeRenderState();
    }

    @Override
    public void extractRenderState(GuardianBee bee, GuardianBeeRenderState state, float partialTick) {
        super.extractRenderState(bee, state, partialTick);
        state.isAngry = bee.isAggressive();
        state.isOnGround = bee.onGround() && bee.getDeltaMovement().lengthSqr() < 1.0E-7;
    }

    @Override
    protected void scale(GuardianBeeRenderState state, PoseStack poseStack) {
        poseStack.scale(SCALE, SCALE, SCALE);
    }

    @Override
    public Identifier getTextureLocation(GuardianBeeRenderState state) {
        return state.isAngry ? ANGRY : CALM;
    }
}
