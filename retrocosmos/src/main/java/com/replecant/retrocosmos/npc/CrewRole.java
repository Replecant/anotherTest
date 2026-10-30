package com.replecant.retrocosmos.npc;

/** What a member of the expedition does. */
public enum CrewRole {
    /** Dr. Harold Cooper, archaeologist and antiquities buyer: trades, never leaves his office. */
    COOPER(ExpeditionNpcs.COOPER, 1, 5, 40.0, 0.0),
    /** Camp guard: patrols, stands watch, shoots what threatens the camp. */
    GUARD(ExpeditionNpcs.GUARD, 4, 10, 40.0, 4.0),
    /** Scientist: works at the camp's instruments and plants, flees to the guards. */
    SCIENTIST(ExpeditionNpcs.SCIENTIST, 4, 12, 26.0, 0.0),
    /** Betty Palmer of the Atomic Home Showroom on Freedom Station: sells furniture, never leaves her counter. */
    DECORATOR(ExpeditionNpcs.DECORATOR, 1, 4, 30.0, 0.0),
    /** Captain Jack Morrow of the Space Rangers, in their office on Freedom Station: recruits, briefs, rewards, trades. */
    RANGER(ExpeditionNpcs.RANGER, 1, 4, 40.0, 4.0),
    /** Dr. Margaret Hale, the camp's xeno-anthropologist: the expedition's contact with the hominid tribes. */
    LIAISON(ExpeditionNpcs.LIAISON, 1, 8, 26.0, 0.0),
    /** The expedition's physicians: Dr. Samuel Ross (look 0) and Dr. Norman Vale (look 1). */
    DOCTOR(ExpeditionNpcs.DOCTOR, 2, 6, 26.0, 0.0);

    public final String key;
    /** Number of skins. */
    public final int variants;
    /** How far from home they patrol / work. */
    public final int radius;
    final double health;
    final double armor;

    CrewRole(String key, int variants, int radius, double health, double armor) {
        this.key = key;
        this.variants = variants;
        this.radius = radius;
        this.health = health;
        this.armor = armor;
    }

    /** Trades through the merchant screen (and so stays put, safe on the station). */
    public boolean isMerchant() {
        return this == COOPER || this == DECORATOR || this == RANGER;
    }

    public static CrewRole byKey(String key) {
        for (CrewRole role : values()) {
            if (role.key.equals(key)) {
                return role;
            }
        }
        return SCIENTIST;
    }

    public static CrewRole byId(int id) {
        CrewRole[] values = values();
        return values[Math.floorMod(id, values.length)];
    }
}
