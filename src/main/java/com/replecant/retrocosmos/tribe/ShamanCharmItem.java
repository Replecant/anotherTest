package com.replecant.retrocosmos.tribe;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.stats.Stats;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/**
 * A shaman's spirit charm: bone, feathers and a chip of amber on a fern cord. Crushing it in your fist calls the
 * spirits - a burst of healing and a protective glow - and the charm is spent.
 */
public class ShamanCharmItem extends Item {
    public ShamanCharmItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (level instanceof ServerLevel server) {
            player.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 20 * 10, 1));
            player.addEffect(new MobEffectInstance(MobEffects.ABSORPTION, 20 * 60, 1));
            server.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.EVOKER_CAST_SPELL, SoundSource.PLAYERS,
                    0.8F, 1.4F);
            server.sendParticles(ParticleTypes.TOTEM_OF_UNDYING, player.getX(), player.getY() + 1.0, player.getZ(), 40,
                    0.4, 0.6, 0.4, 0.25);
            player.awardStat(Stats.ITEM_USED.get(this));
            stack.consume(1, player);
        }
        return InteractionResult.SUCCESS;
    }
}
