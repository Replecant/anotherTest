package com.replecant.retrocosmos.tribe.mutant;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.tribe.Tribesman;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.TagKey;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.player.Player;

/**
 * Dr. Oinstein's forces: the mutant hominids and the atomic robots, all in the entity type tag
 * {@code #retrocosmos:oinstein_forces}. They never fight each other, hunt players and tribesfolk, and rally to
 * each other when one of them is attacked.
 */
public final class OinsteinForces {
    public static final TagKey<EntityType<?>> TAG = TagKey.create(Registries.ENTITY_TYPE,
            Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "oinstein_forces"));

    private OinsteinForces() {}

    public static boolean isForce(Entity entity) {
        return entity != null && entity.getType().is(TAG);
    }

    /** One of the forces or the doctor himself (the boss is not in the tag, but nothing of his hurts him or his). */
    public static boolean isAlly(Entity entity) {
        return isForce(entity) || entity instanceof com.replecant.retrocosmos.tribe.boss.OinsteinBoss;
    }

    /** Whom the forces go after: players (not creative/spectator) and free tribesfolk. Never their own kind. */
    public static boolean isEnemy(LivingEntity target) {
        if (target == null || isAlly(target) || !target.isAlive()) {
            return false;
        }
        if (target instanceof Player player) {
            return !player.isCreative() && !player.isSpectator();
        }
        return target instanceof Tribesman t && !t.isCaptive();
    }

    /** Calls every idle Oinstein mob within range onto the attacker. */
    public static void rally(ServerLevel level, Mob caller, LivingEntity attacker, double range) {
        if (!isEnemy(attacker) && !(attacker instanceof Player)) {
            return;
        }
        for (Mob mob : level.getEntitiesOfClass(Mob.class, caller.getBoundingBox().inflate(range, 8.0, range),
                m -> m != caller && m.isAlive() && isForce(m) && m.getTarget() == null)) {
            mob.setTarget(attacker);
        }
    }
}
