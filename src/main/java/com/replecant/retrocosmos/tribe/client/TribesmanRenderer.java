package com.replecant.retrocosmos.tribe.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.tribe.TribeClient;
import com.replecant.retrocosmos.tribe.TribeRole;
import com.replecant.retrocosmos.tribe.Tribesman;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.resources.Identifier;

/** Box-model renderer for the tribesfolk: one texture per role and fur colour, the chief drawn a size larger. */
public class TribesmanRenderer extends MobRenderer<Tribesman, TribesmanRenderState, TribesmanModel> {
    private static final Identifier[][] TEXTURES = new Identifier[TribeRole.values().length][Tribesman.VARIANTS];

    static {
        for (TribeRole role : TribeRole.values()) {
            for (int v = 0; v < Tribesman.VARIANTS; v++) {
                TEXTURES[role.ordinal()][v] = Identifier.fromNamespaceAndPath(RetroCosmos.MODID,
                        "textures/entity/tribe/tribesman_" + role.key + "_" + v + ".png");
            }
        }
    }

    public TribesmanRenderer(EntityRendererProvider.Context context) {
        super(context, new TribesmanModel(context.bakeLayer(TribeClient.TRIBESMAN)), 0.45F);
    }

    @Override
    public TribesmanRenderState createRenderState() {
        return new TribesmanRenderState();
    }

    @Override
    public void extractRenderState(Tribesman entity, TribesmanRenderState state, float partialTick) {
        super.extractRenderState(entity, state, partialTick);
        state.role = entity.role().ordinal();
        state.variant = entity.variant();
        state.sit = entity.sitAmount(partialTick);
        state.dance = entity.danceAmount(partialTick);
        state.captive = entity.captiveAmount(partialTick);
        state.unhappy = entity.getUnhappyCounter() > 0;
        state.aggressive = entity.isAggressive();
        state.attackAnim = entity.getAttackAnim(partialTick);
    }

    @Override
    public Identifier getTextureLocation(TribesmanRenderState state) {
        return TEXTURES[Math.floorMod(state.role, TEXTURES.length)][Math.floorMod(state.variant, Tribesman.VARIANTS)];
    }

    @Override
    protected void scale(TribesmanRenderState state, PoseStack poseStack) {
        if (state.role == TribeRole.CHIEF.ordinal() && !state.isBaby) {
            poseStack.scale(1.1F, 1.1F, 1.1F);
        }
    }
}
