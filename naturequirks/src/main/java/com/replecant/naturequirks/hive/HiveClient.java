package com.replecant.naturequirks.hive;

import com.replecant.naturequirks.NatureQuirks;
import net.minecraft.client.Camera;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.ItemBlockRenderTypes;
import net.minecraft.client.renderer.chunk.ChunkSectionLayer;
import net.minecraft.client.renderer.fog.FogData;
import net.minecraft.client.renderer.fog.environment.FogEnvironment;
import net.minecraft.resources.Identifier;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.fml.event.lifecycle.FMLClientSetupEvent;
import net.neoforged.neoforge.client.extensions.common.IClientFluidTypeExtensions;
import net.neoforged.neoforge.client.extensions.common.RegisterClientExtensionsEvent;
import org.joml.Vector4f;

/** Client side of the hives: honey's textures, its amber fog when submerged, translucent honey. */
@EventBusSubscriber(modid = NatureQuirks.MODID, value = Dist.CLIENT)
public final class HiveClient {
    private static final Identifier STILL = Identifier.fromNamespaceAndPath(NatureQuirks.MODID, "block/honey_still");
    private static final Identifier FLOW = Identifier.fromNamespaceAndPath(NatureQuirks.MODID, "block/honey_flow");

    private HiveClient() {}

    @SubscribeEvent
    public static void extensions(RegisterClientExtensionsEvent event) {
        event.registerFluidType(new IClientFluidTypeExtensions() {
            @Override
            public Identifier getStillTexture() {
                return STILL;
            }

            @Override
            public Identifier getFlowingTexture() {
                return FLOW;
            }

            @Override
            public Vector4f modifyFogColor(Camera camera, float partialTick, ClientLevel level, int renderDistance, float darken,
                                           Vector4f fluidFogColor) {
                return new Vector4f(0.86F, 0.52F, 0.08F, 1.0F);
            }

            @Override
            public void modifyFogRender(Camera camera, FogEnvironment environment, float renderDistance, float partialTick, FogData fog) {
                fog.environmentalStart = 0.0F;
                fog.environmentalEnd = 3.0F;
            }
        }, ModHive.HONEY_TYPE.get());
    }

    @SubscribeEvent
    public static void setup(FMLClientSetupEvent event) {
        event.enqueueWork(() -> {
            ItemBlockRenderTypes.setRenderLayer(ModHive.HONEY.get(), ChunkSectionLayer.TRANSLUCENT);
            ItemBlockRenderTypes.setRenderLayer(ModHive.FLOWING_HONEY.get(), ChunkSectionLayer.TRANSLUCENT);
        });
    }
}
