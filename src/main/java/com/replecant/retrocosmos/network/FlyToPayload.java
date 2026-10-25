package com.replecant.retrocosmos.network;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.flight.RocketEntity;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.Identifier;
import net.neoforged.neoforge.network.handling.IPayloadContext;

/** Sent by the system map when the crew picks a destination (Earth or Freedom Station). */
public record FlyToPayload(String destination) implements CustomPacketPayload {
    public static final Type<FlyToPayload> TYPE = new Type<>(Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "fly_to"));
    public static final StreamCodec<ByteBuf, FlyToPayload> STREAM_CODEC = ByteBufCodecs.STRING_UTF8.map(FlyToPayload::new, FlyToPayload::destination);

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }

    public static void handle(FlyToPayload payload, IPayloadContext context) {
        if (context.player().getVehicle() instanceof RocketEntity rocket) {
            rocket.travelTo(payload.destination());
        }
    }
}
