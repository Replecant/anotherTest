package com.replecant.retrocosmos.dinosaur.client;

import java.util.function.Function;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;

/** Shared bits of the dinosaur models: part lookup and baby proportions. */
public abstract class DinoModel extends EntityModel<DinosaurRenderState> {
    protected static final float DEG = Mth.DEG_TO_RAD;
    protected final Function<String, ModelPart> parts;
    private final float babyHeadScale;
    private final ModelPart babyHead;

    protected DinoModel(ModelPart root, String headPart, float babyHeadScale) {
        this(root, headPart, babyHeadScale, RenderTypes::entityCutoutNoCull);
    }

    /** With a custom render type, e.g. translucent for glassy dragonfly wings. */
    protected DinoModel(ModelPart root, String headPart, float babyHeadScale, Function<Identifier, RenderType> renderType) {
        super(root, renderType);
        this.parts = root.createPartLookup();
        this.babyHead = parts.apply(headPart);
        this.babyHeadScale = babyHeadScale;
    }

    protected ModelPart part(String name) {
        ModelPart part = parts.apply(name);
        if (part == null) {
            throw new IllegalStateException("Dinosaur model part missing: " + name);
        }
        return part;
    }

    /** Babies are half size with an oversized, cute head; scaling about the ground keeps their feet down. */
    protected void applyAge(DinosaurRenderState state) {
        ModelPart root = root();
        float s = state.isBaby ? 0.5F : 1.0F;
        root.xScale = s;
        root.yScale = s;
        root.zScale = s;
        root.y = 24.0F * (1.0F - s);
        if (state.isBaby) {
            babyHead.xScale *= babyHeadScale;
            babyHead.yScale *= babyHeadScale;
            babyHead.zScale *= babyHeadScale;
        }
    }

    /** Smooth 0..1..0 pulse over a melee swing. */
    protected static float swingPulse(float attackAnim) {
        return attackAnim <= 0.0F ? 0.0F : Mth.sin(attackAnim * Mth.PI);
    }
}
