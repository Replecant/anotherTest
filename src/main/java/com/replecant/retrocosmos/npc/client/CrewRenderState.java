package com.replecant.retrocosmos.npc.client;

import net.minecraft.client.renderer.entity.state.HumanoidRenderState;

/** What the crew model needs to know about the entity this frame. */
public class CrewRenderState extends HumanoidRenderState {
    /** {@link com.replecant.retrocosmos.npc.CrewRole} ordinal. */
    public int role;
    public int variant;
    /** ExpeditionMember.ACT_* pose. */
    public int action;
    /** ExpeditionMember.WEAPON_* in hand. */
    public int weapon;
}
