package com.replecant.retrocosmos.npc.client;

import com.replecant.retrocosmos.npc.quest.QuestNetwork;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.client.event.RegisterGuiLayersEvent;
import net.neoforged.neoforge.client.network.event.RegisterClientPayloadHandlersEvent;

/** Client half of the Space Rangers storyline: the dialogue terminal and the objective HUD. */
public final class QuestClient {
    private QuestClient() {}

    public static void init(IEventBus modEventBus) {
        modEventBus.addListener(QuestClient::registerPayloads);
        modEventBus.addListener(QuestClient::registerLayers);
    }

    private static void registerPayloads(RegisterClientPayloadHandlersEvent event) {
        event.register(QuestNetwork.OpenDialogue.TYPE, (payload, context) -> context.enqueueWork(() -> DialogueScreen.open(payload.entityId(), payload.dialogue())));
    }

    private static void registerLayers(RegisterGuiLayersEvent event) {
        event.registerAboveAll(QuestHudLayer.ID, new QuestHudLayer());
    }
}
