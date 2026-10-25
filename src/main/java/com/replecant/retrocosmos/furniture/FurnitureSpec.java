package com.replecant.retrocosmos.furniture;

import javax.annotation.Nullable;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * Describes one piece of retro furniture.
 *
 * @param shape       collision/outline shape for a block facing north (rotated for other facings)
 * @param facing      whether the block has a horizontal facing
 * @param wall        whether it hangs on a wall (placed against the clicked face)
 * @param toggleable  whether right click switches it on/off ({@code lit} property)
 * @param lightOn     light level emitted while lit
 * @param seatHeight  seat surface height in pixels, or a negative value when it isn't a seat
 * @param toggleSound sound played when switched, may be null
 * @param tall        two blocks tall (lower/upper halves, like a door)
 * @param twoLong     two blocks long (foot/head parts, like a bed); the head lies behind the foot
 */
public record FurnitureSpec(VoxelShape shape, boolean facing, boolean wall, boolean toggleable, int lightOn,
                            float seatHeight, @Nullable SoundEvent toggleSound, boolean tall, boolean twoLong) {

    public FurnitureSpec(VoxelShape shape, boolean facing, boolean wall, boolean toggleable, int lightOn,
                         float seatHeight, @Nullable SoundEvent toggleSound) {
        this(shape, facing, wall, toggleable, lightOn, seatHeight, toggleSound, false, false);
    }

    public FurnitureSpec asTall() {
        return new FurnitureSpec(shape, facing, wall, toggleable, lightOn, seatHeight, toggleSound, true, false);
    }

    public FurnitureSpec asTwoLong() {
        return new FurnitureSpec(shape, true, wall, toggleable, lightOn, seatHeight, toggleSound, false, true);
    }

    public boolean isSeat() {
        return seatHeight >= 0;
    }
}
