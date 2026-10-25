package com.replecant.retrocosmos.flight;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.BlockPos;

/** The launch pad on Homestead a player last flew from; flights "home" land there. */
public record HomePad(BlockPos pos, boolean known) {
    public static final HomePad UNKNOWN = new HomePad(BlockPos.ZERO, false);
    public static final Codec<HomePad> CODEC = RecordCodecBuilder.create(i -> i.group(
            BlockPos.CODEC.fieldOf("pos").forGetter(HomePad::pos),
            Codec.BOOL.fieldOf("known").forGetter(HomePad::known)
    ).apply(i, HomePad::new));
}
