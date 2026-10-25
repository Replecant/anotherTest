package com.replecant.retrocosmos.dinosaur.robot;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.tribe.Tribesman;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.tags.TagKey;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;

/** Who is on Dr. Oinstein's side (entity type tag retrocosmos:oinstein_forces), and who his machines hunt. */
public final class OinsteinForces {
    public static final TagKey<EntityType<?>> TAG = TagKey.create(Registries.ENTITY_TYPE,
            Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "oinstein_forces"));

    private OinsteinForces() {}

    public static boolean isMember(Entity entity) {
        return entity != null && entity.getType().is(TAG);
    }

    /** Players and free tribesmen of Venus - never his own creatures, nor the captives in his cages. */
    public static boolean isQuarry(LivingEntity entity) {
        return !isMember(entity) && (entity instanceof Player || entity instanceof Tribesman tribesman && !tribesman.isCaptive());
    }
}
