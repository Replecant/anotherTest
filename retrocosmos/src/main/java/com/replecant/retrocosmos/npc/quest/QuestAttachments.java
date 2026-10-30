package com.replecant.retrocosmos.npc.quest;

import com.replecant.retrocosmos.RetroCosmos;
import net.neoforged.neoforge.attachment.AttachmentType;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;
import net.neoforged.neoforge.registries.NeoForgeRegistries;

/** The per-player quest state attachment. */
public final class QuestAttachments {
    public static final DeferredRegister<AttachmentType<?>> ATTACHMENTS = DeferredRegister.create(NeoForgeRegistries.ATTACHMENT_TYPES, RetroCosmos.MODID);

    /** Space Rangers progress: persistent, synced to the player (for the objective HUD), kept on death. */
    public static final DeferredHolder<AttachmentType<?>, AttachmentType<QuestState>> RANGER_QUEST = ATTACHMENTS.register("ranger_quest",
            () -> AttachmentType.builder(() -> QuestState.NONE)
                    .serialize(QuestState.CODEC)
                    .sync(QuestState.STREAM_CODEC)
                    .copyOnDeath()
                    .build());

    private QuestAttachments() {}
}
