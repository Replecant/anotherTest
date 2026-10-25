package com.replecant.retrocosmos.npc;

/** What a member of the expedition does. */
public enum CrewRole {
    /** Dr. Harold Cooper, archaeologist and antiquities buyer: trades, never leaves his office. */
    COOPER(ExpeditionNpcs.COOPER, 1, 5, 40.0, 0.0),
    /** Camp guard: patrols, stands watch, shoots what threatens the camp. */
    GUARD(ExpeditionNpcs.GUARD, 4, 10, 40.0, 4.0),
    /** Scientist: works at the camp's instruments and plants, flees to the guards. */
    SCIENTIST(ExpeditionNpcs.SCIENTIST, 4, 12, 26.0, 0.0);

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
