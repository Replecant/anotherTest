package com.replecant.retrocosmos.tribe.ranger;

import com.replecant.retrocosmos.tribe.mutant.BlasterBolt;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.level.Level;

/** The Space Rangers' blue blaster bolt: a little faster and harder-hitting than Dr. Oinstein's green one. */
public class RangerBolt extends BlasterBolt {
    public static final float DAMAGE = 7.0F;
    public static final float SPEED = 2.6F;

    public RangerBolt(EntityType<? extends RangerBolt> type, Level level) {
        super(type, level);
    }

    @Override
    public float damage() {
        return DAMAGE;
    }

    @Override
    public float speed() {
        return SPEED;
    }
}
