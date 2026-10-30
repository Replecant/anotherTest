package com.replecant.retrocosmos.tribe.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.tribe.mutant.HominidNovus;
import com.replecant.retrocosmos.tribe.mutant.HominusSapiens;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.LivingEntityRenderer;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.layers.EyesLayer;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.phys.AABB;

/**
 * Renderer for Dr. Oinstein's mutants: the box model, a full-bright glow overlay (eyes, brain, blaster coil, the
 * novus' blinking collar lamp) and, for the Sapiens, its translucent brain dome drawn last so the brain shows through.
 */
public class MutantRenderer<T extends Monster> extends MobRenderer<T, MutantRenderState, EntityModel<MutantRenderState>> {
    private final Identifier texture;

    public MutantRenderer(EntityRendererProvider.Context context, EntityModel<MutantRenderState> model, float shadow, String name,
                          boolean lamp, boolean glass) {
        super(context, model, shadow);
        this.texture = tex(name, "");
        RenderType glow = RenderTypes.eyes(tex(name, "_glow"));
        addLayer(new EyesLayer<MutantRenderState, EntityModel<MutantRenderState>>(this) {
            @Override
            public RenderType renderType() {
                return glow;
            }
        });
        if (lamp) {
            RenderType lampType = RenderTypes.eyes(tex(name, "_lamp"));
            addLayer(new EyesLayer<MutantRenderState, EntityModel<MutantRenderState>>(this) {
                @Override
                public RenderType renderType() {
                    return lampType;
                }

                @Override
                public void submit(PoseStack poseStack, SubmitNodeCollector collector, int light, MutantRenderState state, float yRot, float xRot) {
                    if (state.lampOn) {
                        super.submit(poseStack, collector, light, state, yRot, xRot);
                    }
                }
            });
        }
        if (glass) {
            RenderType glassType = RenderTypes.entityTranslucent(tex(name, "_glass"));
            addLayer(new RenderLayer<MutantRenderState, EntityModel<MutantRenderState>>(this) {
                @Override
                public void submit(PoseStack poseStack, SubmitNodeCollector collector, int light, MutantRenderState state, float yRot, float xRot) {
                    if (!state.isInvisibleToPlayer) {
                        // the full overload, as vanilla's EyesLayer calls it: (light, overlay, tint colour, sprite, outline colour).
                        // NB the short overload's last int is the OUTLINE colour - passing -1 there drew a white glowing silhouette.
                        collector.order(2).submitModel(getParentModel(), state, poseStack, glassType, light,
                                LivingEntityRenderer.getOverlayCoords(state, 0.0F), -1, null, state.outlineColor, null);
                    }
                }
            });
        }
    }

    private static Identifier tex(String name, String suffix) {
        return Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "textures/entity/tribe/" + name + suffix + ".png");
    }

    @Override
    public MutantRenderState createRenderState() {
        return new MutantRenderState();
    }

    @Override
    public void extractRenderState(T entity, MutantRenderState state, float partialTick) {
        super.extractRenderState(entity, state, partialTick);
        state.attackAnim = entity.getAttackAnim(partialTick);
        state.aggressive = entity.isAggressive();
        if (entity instanceof HominidNovus novus) {
            state.rear = novus.rearAmount(partialTick);
            state.impact = novus.impactAmount(partialTick);
            state.charging = novus.isCharging();
            // a slow red blink; fast and frantic while it is angry
            int period = novus.getTarget() != null || state.aggressive ? 8 : 30;
            state.lampOn = (novus.tickCount + novus.getId()) % period < period / 3;
        } else if (entity instanceof HominusSapiens sapiens) {
            state.aim = sapiens.aimAmount(partialTick);
        }
    }

    @Override
    public Identifier getTextureLocation(MutantRenderState state) {
        return texture;
    }

    @Override
    protected AABB getBoundingBoxForCulling(T entity) {
        return super.getBoundingBoxForCulling(entity).inflate(0.8);
    }
}
