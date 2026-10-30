package com.replecant.naturequirks.hive;

import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.fluids.FluidType;

/**
 * Honey: thick and slow. Anything wading in it is held back hard - a third of its speed, a slow sink, hardly any
 * jump - and loses air like in water (no extra harm). Items float in it slowly.
 */
public class HoneyFluidType extends FluidType {
    public HoneyFluidType(Properties properties) {
        super(properties);
    }

    @Override
    public boolean move(FluidState state, LivingEntity entity, Vec3 movement, double gravity) {
        double y0 = entity.getY();
        entity.moveRelative(0.012F, movement);
        entity.move(MoverType.SELF, entity.getDeltaMovement());
        Vec3 d = entity.getDeltaMovement();
        double vy = d.y * 0.4;
        if (!entity.isNoGravity()) {
            vy -= gravity / 8.0;
        }
        entity.setDeltaMovement(d.x * 0.35, vy, d.z * 0.35);
        // let a wader climb out over the bank, slowly
        Vec3 now = entity.getDeltaMovement();
        if (entity.horizontalCollision && entity.isFree(now.x, now.y + 0.6 - entity.getY() + y0, now.z)) {
            entity.setDeltaMovement(now.x, 0.15, now.z);
        }
        return true;
    }
}
