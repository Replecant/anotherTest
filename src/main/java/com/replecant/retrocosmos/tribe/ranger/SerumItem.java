package com.replecant.retrocosmos.tribe.ranger;

import java.util.function.Consumer;
import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.ColorParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.level.Level;

/**
 * A syringe of one of Dr. Oinstein's serums. Used like a potion (the consumable component applies the effects and
 * hands back the glass bottle); on top of that a puff of green fumes and, scheduled in the player's persistent data,
 * the side effect once the main effect wears off ({@link SerumEvents}).
 */
public class SerumItem extends Item {
    public static final String AFTER_KEY = "retrocosmos.serum_after";
    public static final String AFTER_AT_KEY = "retrocosmos.serum_after_at";
    private final Serum serum;

    public SerumItem(Properties properties, Serum serum) {
        super(properties);
        this.serum = serum;
    }

    public Serum serum() {
        return serum;
    }

    @Override
    public ItemStack finishUsingItem(ItemStack stack, Level level, LivingEntity entity) {
        ItemStack result = super.finishUsingItem(stack, level, entity);
        if (level instanceof ServerLevel server) {
            server.sendParticles(ColorParticleOption.create(ParticleTypes.ENTITY_EFFECT, 0xFF000000 | serum.color),
                    entity.getX(), entity.getY() + entity.getBbHeight() * 0.6, entity.getZ(), 24, 0.35, 0.45, 0.35, 1.0);
            server.sendParticles(ParticleTypes.HAPPY_VILLAGER, entity.getX(), entity.getY() + entity.getBbHeight() * 0.8, entity.getZ(),
                    6, 0.3, 0.3, 0.3, 0.0);
            entity.playSound(SoundEvents.BEE_STING, 0.6F, 1.6F);
            if (entity instanceof Player player) {
                schedule(player, serum, server.getGameTime());
            }
        }
        return result;
    }

    /** The newest serum's side effect replaces any one still pending. */
    public static void schedule(Player player, Serum serum, long now) {
        var data = player.getPersistentData();
        data.putString(AFTER_KEY, serum.id);
        data.putLong(AFTER_AT_KEY, now + serum.afterDelay);
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display, Consumer<Component> tooltip, TooltipFlag flag) {
        for (Serum.Effect e : serum.effects) {
            tooltip.accept(describe(e).withStyle(ChatFormatting.BLUE));
        }
        tooltip.accept(Component.translatable("item.retrocosmos.serum.after", describe(serum.after)).withStyle(ChatFormatting.RED));
        tooltip.accept(Component.translatable("item.retrocosmos." + serum.itemName() + ".desc").withStyle(ChatFormatting.DARK_GRAY, ChatFormatting.ITALIC));
    }

    private static MutableComponent describe(Serum.Effect e) {
        MutableComponent name = Component.translatable(e.effect().value().getDescriptionId());
        if (e.amplifier() > 0) {
            name = name.append(" ").append(Component.translatable("enchantment.level." + (e.amplifier() + 1)));
        }
        int seconds = e.ticks() / 20;
        return Component.translatable("item.retrocosmos.serum.effect", name, String.format("%d:%02d", seconds / 60, seconds % 60));
    }

    public static MobEffectInstance afterEffect(Serum serum) {
        return serum.after.instance();
    }
}
