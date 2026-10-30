package com.replecant.retrocosmos.oxygen;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;

/**
 * Per-player life-support settings, stored as a synced NeoForge attachment.
 *
 * @param airless   the "airless environment" simulation is on for this player (test toggle until planets arrive)
 * @param hudHidden the suit telemetry HUD is switched off
 */
public record SuitSettings(boolean airless, boolean hudHidden) {
    public static final SuitSettings DEFAULT = new SuitSettings(false, false);

    public static final MapCodec<SuitSettings> CODEC = RecordCodecBuilder.mapCodec(i -> i.group(
            Codec.BOOL.fieldOf("airless").forGetter(SuitSettings::airless),
            Codec.BOOL.fieldOf("hud_hidden").forGetter(SuitSettings::hudHidden)
    ).apply(i, SuitSettings::new));

    public static final StreamCodec<ByteBuf, SuitSettings> STREAM_CODEC = StreamCodec.composite(
            ByteBufCodecs.BOOL, SuitSettings::airless,
            ByteBufCodecs.BOOL, SuitSettings::hudHidden,
            SuitSettings::new);

    public SuitSettings withAirless(boolean value) {
        return new SuitSettings(value, hudHidden);
    }

    public SuitSettings withHudHidden(boolean value) {
        return new SuitSettings(airless, value);
    }
}
