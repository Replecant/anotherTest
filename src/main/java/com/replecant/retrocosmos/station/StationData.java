package com.replecant.retrocosmos.station;

import com.mojang.serialization.Codec;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.saveddata.SavedDataType;

/** Remembers, per orbit dimension, whether Freedom Station has already been built. */
public class StationData extends SavedData {
    public static final Codec<StationData> CODEC = Codec.BOOL.fieldOf("placed").codec().xmap(StationData::new, d -> d.placed);
    public static final SavedDataType<StationData> TYPE = new SavedDataType<>("retrocosmos_freedom_station", StationData::new, CODEC);

    private boolean placed;

    public StationData() {
        this(false);
    }

    private StationData(boolean placed) {
        this.placed = placed;
    }

    public boolean placed() {
        return placed;
    }

    public void markPlaced() {
        placed = true;
        setDirty();
    }
}
