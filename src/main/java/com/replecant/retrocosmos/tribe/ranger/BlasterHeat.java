package com.replecant.retrocosmos.tribe.ranger;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;

/**
 * A blaster's heat. Each shot adds one unit; once the trigger has rested for {@link #GRACE} ticks the barrel sheds a
 * unit every {@link #COOL_TICKS}. At {@link #MAX} units the blaster overheats and locks up while it cools down. The heat
 * is worked out from the time of the last shot, so nothing has to tick.
 */
public record BlasterHeat(int heat, long lastShot) {
    public static final BlasterHeat COLD = new BlasterHeat(0, 0L);
    /** Rapid shots until the blaster overheats. */
    public static final int MAX = 6;
    /** Ticks without firing before the barrel starts to cool. */
    public static final int GRACE = 15;
    /** Ticks to shed one unit of heat. */
    public static final int COOL_TICKS = 10;
    /** Lock-up after overheating: the barrel cools from full in exactly this long. */
    public static final int OVERHEAT_TICKS = MAX * COOL_TICKS + GRACE;

    public static final Codec<BlasterHeat> CODEC = RecordCodecBuilder.create(i -> i.group(
            Codec.INT.fieldOf("heat").forGetter(BlasterHeat::heat),
            Codec.LONG.fieldOf("last_shot").forGetter(BlasterHeat::lastShot)
    ).apply(i, BlasterHeat::new));
    public static final StreamCodec<ByteBuf, BlasterHeat> STREAM_CODEC = StreamCodec.composite(
            ByteBufCodecs.VAR_INT, BlasterHeat::heat, ByteBufCodecs.VAR_LONG, BlasterHeat::lastShot, BlasterHeat::new);

    /** Heat left at the given game time. */
    public int at(long now) {
        long resting = now - lastShot - GRACE;
        return resting <= 0 ? heat : (int) Math.max(0, heat - resting / COOL_TICKS);
    }

    /** After one more shot at the given game time. */
    public BlasterHeat fire(long now) {
        return new BlasterHeat(Math.min(MAX, at(now) + 1), now);
    }
}
