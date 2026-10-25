package com.replecant.retrocosmos.tribe.mutant;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.stats.Stats;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/**
 * Dr. Oinstein's ray pistol, pried from a Hominus Sapiens' fingers: right-click fires a blaster bolt. Wears out
 * with use (repair it with redstone) and needs a moment to recharge between shots.
 */
public class RayBlasterItem extends Item {
    public static final int COOLDOWN = 12;

    public RayBlasterItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (level instanceof ServerLevel) {
            BlasterBolt.fire(player, player.getLookAngle(), 0.4F);
            stack.hurtAndBreak(1, player, hand);
            player.awardStat(Stats.ITEM_USED.get(this));
        }
        player.getCooldowns().addCooldown(stack, COOLDOWN);
        return InteractionResult.SUCCESS;
    }
}
