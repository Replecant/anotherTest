package com.replecant.retrocosmos.block;

import net.minecraft.util.StringRepresentable;

public enum RocketPart implements StringRepresentable {
    BOTTOM("bottom"),
    MIDDLE("middle"),
    TOP("top");

    private final String name;

    RocketPart(String name) {
        this.name = name;
    }

    /** How many blocks above the base (bottom) this part is. */
    public int offset() {
        return ordinal();
    }

    @Override
    public String getSerializedName() {
        return name;
    }
}
