package com.replecant.retrocosmos.npc.client;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.npc.CrewRole;
import com.replecant.retrocosmos.npc.ExpeditionMember;
import com.replecant.retrocosmos.npc.NpcClient;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.HumanoidMobRenderer;
import net.minecraft.resources.Identifier;

/** Renders the crew as players do: the vanilla humanoid, a 64x64 skin per role and look, plus the gear layer. */
public class CrewRenderer extends HumanoidMobRenderer<ExpeditionMember, CrewRenderState, CrewModel> {
    private static final Identifier[][] TEXTURES = new Identifier[CrewRole.values().length][];

    static {
        for (CrewRole role : CrewRole.values()) {
            TEXTURES[role.ordinal()] = new Identifier[role.variants];
            for (int v = 0; v < role.variants; v++) {
                TEXTURES[role.ordinal()][v] = Identifier.fromNamespaceAndPath(RetroCosmos.MODID,
                        "textures/entity/npc/" + role.key + "_" + v + ".png");
            }
        }
    }

    public CrewRenderer(EntityRendererProvider.Context context) {
        super(context, new CrewModel(context.bakeLayer(NpcClient.CREW)), 0.5F);
        addLayer(new CrewGearLayer(this, new CrewModel(context.bakeLayer(NpcClient.CREW_GEAR))));
    }

    @Override
    public CrewRenderState createRenderState() {
        return new CrewRenderState();
    }

    @Override
    public void extractRenderState(ExpeditionMember entity, CrewRenderState state, float partialTick) {
        super.extractRenderState(entity, state, partialTick);
        state.role = entity.role().ordinal();
        state.variant = entity.variant();
        state.action = entity.action();
        state.weapon = entity.weapon();
    }

    @Override
    public Identifier getTextureLocation(CrewRenderState state) {
        Identifier[] looks = TEXTURES[Math.floorMod(state.role, TEXTURES.length)];
        return looks[Math.floorMod(state.variant, looks.length)];
    }
}
