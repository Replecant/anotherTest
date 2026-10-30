package com.replecant.retrocosmos.tribe.boss.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.tribe.boss.DrOinstein;
import com.replecant.retrocosmos.tribe.boss.HomoNovus;
import com.replecant.retrocosmos.tribe.boss.OinsteinBoss;
import com.replecant.retrocosmos.tribe.boss.OinsteinStrider;
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
import net.minecraft.world.phys.AABB;

/**
 * Renderer of Dr. Oinstein in all three shapes: the box model, a full-bright glow layer (reactor, muzzles, serum,
 * veins, brain) and, for the strider's cockpit dome and Homo Novus' brain flask, a translucent glass layer drawn last.
 */
public class BossRenderer<T extends OinsteinBoss> extends MobRenderer<T, BossRenderState, EntityModel<BossRenderState>> {
    private final Identifier texture;

    public BossRenderer(EntityRendererProvider.Context context, EntityModel<BossRenderState> model, float shadow, String name, boolean glass) {
        super(context, model, shadow);
        this.texture = tex(name, "");
        RenderType glow = RenderTypes.eyes(tex(name, "_glow"));
        addLayer(new EyesLayer<BossRenderState, EntityModel<BossRenderState>>(this) {
            @Override
            public RenderType renderType() {
                return glow;
            }
        });
        if (glass) {
            RenderType glassType = RenderTypes.entityTranslucent(tex(name, "_glass"));
            addLayer(new RenderLayer<BossRenderState, EntityModel<BossRenderState>>(this) {
                @Override
                public void submit(PoseStack poseStack, SubmitNodeCollector collector, int light, BossRenderState state, float yRot, float xRot) {
                    if (!state.isInvisibleToPlayer) {
                        // the full overload: (light, overlay, tint, sprite, OUTLINE colour) - see MutantRenderer
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
    public BossRenderState createRenderState() {
        return new BossRenderState();
    }

    @Override
    public void extractRenderState(T entity, BossRenderState state, float partialTick) {
        super.extractRenderState(entity, state, partialTick);
        state.attackAnim = entity.getAttackAnim(partialTick);
        state.aggressive = entity.isAggressive();
        if (entity instanceof OinsteinStrider strider) {
            state.charge = strider.chargeAmount(partialTick);
            state.raise = strider.raiseAmount(partialTick);
            state.impact = strider.impactAmount(partialTick);
            state.wreck = strider.wreckAmount(partialTick);
            // the walker does not keel over and flash red like a dying mob: the model plays the wreck itself
            state.deathTime = 0.0F;
            state.hasRedOverlay = state.hasRedOverlay && strider.deathTime <= 0;
        } else if (entity instanceof DrOinstein doctor) {
            state.fallen = doctor.fallenAmount(partialTick);
            state.inject = doctor.injectAmount(partialTick);
            state.shout = doctor.shoutAmount(partialTick);
            state.shake = doctor.shakeAmount(partialTick);
            state.syringe = doctor.holdsSyringe();
        } else if (entity instanceof HomoNovus novus) {
            state.crouch = novus.actionAmount(HomoNovus.CROUCH, partialTick);
            state.leap = novus.actionAmount(HomoNovus.LEAP, partialTick);
            state.slam = novus.actionAmount(HomoNovus.SLAM, partialTick);
            state.grab = novus.actionAmount(HomoNovus.GRAB, partialTick);
            state.scream = novus.actionAmount(HomoNovus.SCREAM, partialTick);
            state.rage = novus.isRaging();
        }
    }

    @Override
    public Identifier getTextureLocation(BossRenderState state) {
        return texture;
    }

    @Override
    protected AABB getBoundingBoxForCulling(T entity) {
        return super.getBoundingBoxForCulling(entity).inflate(1.5);
    }
}
