package com.replecant.retrocosmos.dinosaur.client;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.dinosaur.DinosaurAnimated;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.resources.Identifier;
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
