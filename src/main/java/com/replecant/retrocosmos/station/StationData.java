package com.replecant.retrocosmos.station;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.saveddata.SavedDataType;

/** Remembers, per orbit dimension, whether (and which version of) Freedom Station has been built. */
public class StationData extends SavedData {
    public static final Codec<StationData> CODEC = RecordCodecBuilder.create(i -> i.group(
            Codec.BOOL.fieldOf("placed").forGetter(d -> d.placed),
            Codec.INT.optionalFieldOf("version", 1).forGetter(d -> d.version)
    ).apply(i, StationData::new));
    public static final SavedDataType<StationData> TYPE = new SavedDataType<>("retrocosmos_freedom_station", StationData::new, CODEC);

    private boolean placed;
    private int version;

    public StationData() {
        this(false, 0);
    }

    private StationData(boolean placed, int version) {
        this.placed = placed;
        this.version = version;
    }

    public boolean placed() {
        return placed;
    }

    public int version() {
        return version;
    }

    public void markPlaced(int version) {
        this.placed = true;
        this.version = version;
        setDirty();
    }
}
