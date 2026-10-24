package com.replecant.retrocosmos.registry;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.oxygen.SuitSettings;
import net.neoforged.neoforge.attachment.AttachmentType;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;
import net.neoforged.neoforge.registries.NeoForgeRegistries;

public final class ModAttachments {
    public static final DeferredRegister<AttachmentType<?>> ATTACHMENTS = DeferredRegister.create(NeoForgeRegistries.ATTACHMENT_TYPES, RetroCosmos.MODID);

    /** Persistent, death-surviving and client-synced life-support settings of a player. */
    public static final DeferredHolder<AttachmentType<?>, AttachmentType<SuitSettings>> SUIT_SETTINGS = ATTACHMENTS.register("suit_settings",
            () -> AttachmentType.builder(() -> SuitSettings.DEFAULT)
                    .serialize(SuitSettings.CODEC)
                    .sync(SuitSettings.STREAM_CODEC)
                    .copyOnDeath()
                    .build());

    private ModAttachments() {}
}
