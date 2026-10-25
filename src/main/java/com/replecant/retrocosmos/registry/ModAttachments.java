package com.replecant.retrocosmos.registry;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.flight.HomePad;
import net.minecraft.network.codec.ByteBufCodecs;
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

    /** Where the player last launched from on Homestead. */
    public static final DeferredHolder<AttachmentType<?>, AttachmentType<HomePad>> HOME_PAD = ATTACHMENTS.register("home_pad",
            () -> AttachmentType.builder(() -> HomePad.UNKNOWN)
                    .serialize(HomePad.CODEC.fieldOf("home_pad"))
                    .copyOnDeath()
                    .build());

    /** Whether the player is currently surrounded by vacuum (computed by the server, synced for the HUD). */
    public static final DeferredHolder<AttachmentType<?>, AttachmentType<Boolean>> IN_VACUUM = ATTACHMENTS.register("in_vacuum",
            () -> AttachmentType.builder(() -> Boolean.FALSE)
                    .sync(ByteBufCodecs.BOOL)
                    .build());

    private ModAttachments() {}
}
