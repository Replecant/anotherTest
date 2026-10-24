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
 */
public record FurnitureSpec(VoxelShape shape, boolean facing, boolean wall, boolean toggleable, int lightOn,
                            float seatHeight, @Nullable SoundEvent toggleSound) {

    public boolean isSeat() {
        return seatHeight >= 0;
    }
}
