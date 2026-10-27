package com.replecant.retrocosmos.npc.quest;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import java.util.Optional;
import net.minecraft.core.GlobalPos;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;

/**
 * One player's progress through the Space Rangers storyline: the stage and, when known, where the HUD should point
 * (the expedition camp, the tribe, the prisoner camp, the Institute, the ranger's office). Persisted, synced to its
 * player, kept on death.
 */
public record QuestState(QuestStage stage, Optional<GlobalPos> target) {
    public static final QuestState NONE = new QuestState(QuestStage.NONE, Optional.empty());

    public static final MapCodec<QuestState> CODEC = RecordCodecBuilder.mapCodec(i -> i.group(
            Codec.STRING.xmap(k -> {
                QuestStage s = QuestStage.byKey(k);
                return s == null ? QuestStage.NONE : s;
            }, QuestStage::key).fieldOf("stage").forGetter(QuestState::stage),
            GlobalPos.CODEC.optionalFieldOf("target").forGetter(QuestState::target)
    ).apply(i, QuestState::new));

    public static final StreamCodec<RegistryFriendlyByteBuf, QuestState> STREAM_CODEC = StreamCodec.composite(
            ByteBufCodecs.VAR_INT.map(QuestStage::byId, QuestStage::ordinal), QuestState::stage,
            ByteBufCodecs.optional(GlobalPos.STREAM_CODEC), QuestState::target,
            QuestState::new);

    public QuestState withStage(QuestStage stage) {
        return new QuestState(stage, target);
    }

    public QuestState withTarget(Optional<GlobalPos> target) {
        return new QuestState(stage, target);
    }
}
