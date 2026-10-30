package com.replecant.retrocosmos.npc.quest;

import com.replecant.retrocosmos.RetroCosmos;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.neoforge.network.PacketDistributor;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;
import net.neoforged.neoforge.network.handling.IPayloadContext;
import net.neoforged.neoforge.network.registration.PayloadRegistrar;

/** The dialogue terminal's two messages: the server opens an exchange, the client answers it. */
public final class QuestNetwork {
    private QuestNetwork() {}

    /** Server to client: show this exchange; {@code entityId} is the speaker (or -1 for a note). */
    public record OpenDialogue(int entityId, Dialogue dialogue) implements CustomPacketPayload {
        public static final Type<OpenDialogue> TYPE = new Type<>(Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "open_dialogue"));
        public static final StreamCodec<RegistryFriendlyByteBuf, OpenDialogue> STREAM_CODEC = StreamCodec.composite(
                ByteBufCodecs.VAR_INT, OpenDialogue::entityId,
                Dialogue.STREAM_CODEC, OpenDialogue::dialogue,
                OpenDialogue::new);

        @Override
        public Type<? extends CustomPacketPayload> type() {
            return TYPE;
        }
    }

    /** Client to server: the player picked answer {@code action} of exchange {@code dialogueId}. */
    public record Choose(int entityId, String dialogueId, String action) implements CustomPacketPayload {
        public static final Type<Choose> TYPE = new Type<>(Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "dialogue_choice"));
        public static final StreamCodec<RegistryFriendlyByteBuf, Choose> STREAM_CODEC = StreamCodec.composite(
                ByteBufCodecs.VAR_INT, Choose::entityId,
                ByteBufCodecs.STRING_UTF8, Choose::dialogueId,
                ByteBufCodecs.STRING_UTF8, Choose::action,
                Choose::new);

        @Override
        public Type<? extends CustomPacketPayload> type() {
            return TYPE;
        }

        static void handle(Choose payload, IPayloadContext context) {
            if (context.player() instanceof ServerPlayer player) {
                QuestDialogues.choose(player, payload.entityId(), payload.dialogueId(), payload.action());
            }
        }
    }

    public static void register(RegisterPayloadHandlersEvent event) {
        PayloadRegistrar registrar = event.registrar("1");
        registrar.playToClient(OpenDialogue.TYPE, OpenDialogue.STREAM_CODEC);
        registrar.playToServer(Choose.TYPE, Choose.STREAM_CODEC, Choose::handle);
    }

    static void send(ServerPlayer player, int entityId, Dialogue dialogue) {
        PacketDistributor.sendToPlayer(player, new OpenDialogue(entityId, dialogue));
    }
}
