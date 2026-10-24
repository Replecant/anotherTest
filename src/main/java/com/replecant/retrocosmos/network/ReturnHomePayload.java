package com.replecant.retrocosmos.network;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.flight.RocketEntity;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.Identifier;
import net.neoforged.neoforge.network.handling.IPayloadContext;

/** Sent by the system map when the crew chooses to return home. */
public record ReturnHomePayload() implements CustomPacketPayload {
    public static final ReturnHomePayload INSTANCE = new ReturnHomePayload();
    public static final Type<ReturnHomePayload> TYPE = new Type<>(Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "return_home"));
    public static final StreamCodec<ByteBuf, ReturnHomePayload> STREAM_CODEC = StreamCodec.unit(INSTANCE);

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }

    public static void handle(ReturnHomePayload payload, IPayloadContext context) {
        if (context.player().getVehicle() instanceof RocketEntity rocket) {
            rocket.beginDescent();
        }
    }
}
