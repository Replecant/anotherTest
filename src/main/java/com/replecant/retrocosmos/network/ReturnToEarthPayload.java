package com.replecant.retrocosmos.network;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.flight.RocketEntity;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.Identifier;
import net.neoforged.neoforge.network.handling.IPayloadContext;

/** Sent by the system map when the crew chooses to return to Earth. */
public record ReturnToEarthPayload() implements CustomPacketPayload {
    public static final ReturnToEarthPayload INSTANCE = new ReturnToEarthPayload();
    public static final Type<ReturnToEarthPayload> TYPE = new Type<>(Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "return_to_earth"));
    public static final StreamCodec<ByteBuf, ReturnToEarthPayload> STREAM_CODEC = StreamCodec.unit(INSTANCE);

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }

    public static void handle(ReturnToEarthPayload payload, IPayloadContext context) {
        if (context.player().getVehicle() instanceof RocketEntity rocket) {
            rocket.beginDescent();
        }
    }
}
