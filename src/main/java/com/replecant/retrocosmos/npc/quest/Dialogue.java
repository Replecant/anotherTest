package com.replecant.retrocosmos.npc.quest;

import java.util.List;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.ComponentSerialization;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;

/**
 * One exchange on the dialogue terminal: who speaks (name plate and role), what they say, and up to three answers.
 * {@code id} names the exchange; an answer's {@code action} is what the server does when it is picked.
 * {@code accent} tints the speaker's plate (ARGB).
 */
public record Dialogue(String id, Component speaker, Component role, Component text, List<Option> options, int accent) {
    public record Option(String action, Component label) {
        public static final StreamCodec<RegistryFriendlyByteBuf, Option> STREAM_CODEC = StreamCodec.composite(
                ByteBufCodecs.STRING_UTF8, Option::action,
                ComponentSerialization.TRUSTED_STREAM_CODEC, Option::label,
                Option::new);
    }

    public static final StreamCodec<RegistryFriendlyByteBuf, Dialogue> STREAM_CODEC = StreamCodec.composite(
            ByteBufCodecs.STRING_UTF8, Dialogue::id,
            ComponentSerialization.TRUSTED_STREAM_CODEC, Dialogue::speaker,
            ComponentSerialization.TRUSTED_STREAM_CODEC, Dialogue::role,
            ComponentSerialization.TRUSTED_STREAM_CODEC, Dialogue::text,
            Option.STREAM_CODEC.apply(ByteBufCodecs.list(3)), Dialogue::options,
            ByteBufCodecs.INT, Dialogue::accent,
            Dialogue::new);
}
