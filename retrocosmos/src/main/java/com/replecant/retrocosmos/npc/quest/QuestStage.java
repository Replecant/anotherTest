package com.replecant.retrocosmos.npc.quest;

import java.util.Locale;

/** The Space Rangers storyline, one player at a time. */
public enum QuestStage {
    /** Not a ranger (yet). */
    NONE,
    /** Joined the Space Rangers on Freedom Station: fly to the expedition camp on Venus. */
    GO_TO_VENUS,
    /** The camp's xeno-anthropologist asked for the elder of the hominid tribe. */
    FIND_ELDER,
    /** The elder told of the evil sky-man: bring the news back to the camp. */
    REPORT_TO_CAMP,
    /** The camp was raided: find the prisoner camp and free the expedition. */
    RESCUE_EXPEDITION,
    /** Dr. Vale handed over keycard A: storm Dr. Oinstein's Institute. */
    STORM_INSTITUTE,
    /** Homo Novus is beaten: bring Professor Oinstein's ID card to the rangers. */
    RETURN_TO_RANGER,
    /** A Space Ranger. */
    COMPLETE;

    public String key() {
        return name().toLowerCase(Locale.ROOT);
    }

    public static QuestStage byId(int id) {
        QuestStage[] values = values();
        return id >= 0 && id < values.length ? values[id] : NONE;
    }

    public static QuestStage byKey(String key) {
        for (QuestStage stage : values()) {
            if (stage.key().equalsIgnoreCase(key)) {
                return stage;
            }
        }
        return null;
    }

    public boolean atLeast(QuestStage other) {
        return ordinal() >= other.ordinal();
    }

    /** Between the two stages, inclusive. */
    public boolean between(QuestStage from, QuestStage to) {
        return ordinal() >= from.ordinal() && ordinal() <= to.ordinal();
    }

    /** Has an objective line on the HUD. */
    public boolean active() {
        return this != NONE && this != COMPLETE;
    }
}
