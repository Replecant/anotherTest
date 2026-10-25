package com.replecant.retrocosmos.tribe;

/** What a tribesman does in the camp. The ordinal is synced to clients and picks the texture and props. */
public enum TribeRole {
    /** Spear-carrying raptor hunter: fights anything that threatens the camp, trades teeth and hides. */
    HUNTER("hunter", 26.0, 5.0, 0.0, 0.33),
    /** Basket-carrying forager: trades fern fiber, glowcap tea and amber; avoids fights. */
    GATHERER("gatherer", 20.0, 3.0, 0.0, 0.32),
    /** Masked witch doctor with a glowcap staff: masks, charms and the spirits' amber. */
    SHAMAN("shaman", 22.0, 3.0, 1.0, 0.30),
    /** The big one with the feather crown, the raptor-hide cape and the club. One per camp. */
    CHIEF("chief", 38.0, 7.0, 4.0, 0.31);

    private static final TribeRole[] VALUES = values();

    public final String key;
    public final double health;
    public final double damage;
    public final double armor;
    public final double speed;

    TribeRole(String key, double health, double damage, double armor, double speed) {
        this.key = key;
        this.health = health;
        this.damage = damage;
        this.armor = armor;
        this.speed = speed;
    }

    /** Hunters and the chief go after raptors on their own; the others only when the camp is attacked. */
    public boolean isWarrior() {
        return this == HUNTER || this == CHIEF;
    }

    public static TribeRole byId(int id) {
        return id >= 0 && id < VALUES.length ? VALUES[id] : HUNTER;
    }

    public static TribeRole byKey(String key) {
        for (TribeRole role : VALUES) {
            if (role.key.equals(key)) {
                return role;
            }
        }
        return HUNTER;
    }
}
