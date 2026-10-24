package com.replecant.retrocosmos.block;

import net.minecraft.util.StringRepresentable;

/** The nine blocks of the Liberty I, from the engine section at the bottom to the needle on top. */
public enum RocketPart implements StringRepresentable {
    ENGINE("engine"),
    FIN_ROOT("fin_root"),
    TANK_LOWER("tank_lower"),
    TANK_MID("tank_mid"),
    TANK_UPPER("tank_upper"),
    CABIN("cabin"),
    SHOULDER("shoulder"),
    CONE("cone"),
    NEEDLE("needle");

    public static final int HEIGHT = values().length;
    private final String name;

    RocketPart(String name) {
        this.name = name;
    }

    /** How many blocks above the base (engine) this part is. */
    public int offset() {
        return ordinal();
    }

    public boolean isBase() {
        return this == ENGINE;
    }

    public boolean isTop() {
        return this == NEEDLE;
    }

    public static RocketPart byOffset(int offset) {
        return values()[offset];
    }

    @Override
    public String getSerializedName() {
        return name;
    }
}
