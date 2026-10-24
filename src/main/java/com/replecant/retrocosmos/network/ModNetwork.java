package com.replecant.retrocosmos.network;

import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;
import net.neoforged.neoforge.network.registration.PayloadRegistrar;

public final class ModNetwork {
    private ModNetwork() {}

    public static void register(RegisterPayloadHandlersEvent event) {
        PayloadRegistrar registrar = event.registrar("1");
        registrar.playToServer(ReturnToEarthPayload.TYPE, ReturnToEarthPayload.STREAM_CODEC, ReturnToEarthPayload::handle);
    }
}
