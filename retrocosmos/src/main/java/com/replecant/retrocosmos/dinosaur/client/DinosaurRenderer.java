package com.replecant.retrocosmos.dinosaur.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.dinosaur.DinosaurAnimated;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.phys.AABB;

/** One renderer for all Venus dinosaurs: a box model, its texture, and the animation channels copied over. */
public class DinosaurRenderer<T extends Mob & DinosaurAnimated> extends MobRenderer<T, DinosaurRenderState, EntityModel<DinosaurRenderState>> {
    private final Identifier texture;
    /** Necks and tails reach well outside the hitbox; grow the culling box so they don't pop out of view. */
    private final double cullGrow;

    public DinosaurRenderer(EntityRendererProvider.Context context, EntityModel<DinosaurRenderState> model, float shadowRadius,
                            String name, double cullGrow) {
        super(context, model, shadowRadius);
        this.texture = Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "textures/entity/dinosaur/" + name + ".png");
        this.cullGrow = cullGrow;
    }

    @Override
    public DinosaurRenderState createRenderState() {
        return new DinosaurRenderState();
    }

    @Override
    public void extractRenderState(T entity, DinosaurRenderState state, float partialTick) {
        super.extractRenderState(entity, state, partialTick);
        state.attackAnim = entity.getAttackAnim(partialTick);
        state.aggressive = entity.isAggressive();
        state.leap = entity.leapAmount(partialTick);
        state.graze = entity.grazeAmount(partialTick);
        state.charge = entity.chargeAmount(partialTick);
        state.windup = entity.isWindingUp();
        state.swell = entity.swellAmount(partialTick);
        state.perch = entity.perchAmount(partialTick);
        state.dive = entity.diveAmount(partialTick);
        state.flightPitch = entity.flightPitch(partialTick);
        state.roar = entity.roarAmount(partialTick);
        state.sweep = entity.sweepAmount(partialTick);
        state.peek = entity.peekAmount(partialTick);
        state.swing = entity.swingAmount(partialTick);
        state.lunge = entity.lungeAmount(partialTick);
    }

    /** The creeper's fuse: it bloats and wobbles like the vanilla creeper before bursting. */
    @Override
    protected void scale(DinosaurRenderState state, PoseStack poseStack) {
        float f = state.swell;
        if (f > 0.0F) {
            float wobble = 1.0F + Mth.sin(f * 100.0F) * f * 0.01F;
            f = Mth.clamp(f, 0.0F, 1.0F);
            f *= f;
            f *= f;
            float wide = (1.0F + f * 0.4F) * wobble;
            float tall = (1.0F + f * 0.1F) / wobble;
            poseStack.scale(wide, tall, wide);
        }
    }

    @Override
    protected float getWhiteOverlayProgress(DinosaurRenderState state) {
        float f = state.swell;
        return f <= 0.0F || (int) (f * 10.0F) % 2 == 0 ? 0.0F : Mth.clamp(f, 0.5F, 1.0F);
    }

    @Override
    public Identifier getTextureLocation(DinosaurRenderState state) {
        return texture;
    }

    @Override
    protected AABB getBoundingBoxForCulling(T entity) {
        return super.getBoundingBoxForCulling(entity).inflate(cullGrow);
    }
}
