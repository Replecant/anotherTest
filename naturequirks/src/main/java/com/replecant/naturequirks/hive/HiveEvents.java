package com.replecant.naturequirks.hive;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.TagKey;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.animal.bee.Bee;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ItemUtils;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.gameevent.GameEvent;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;
import net.neoforged.neoforge.event.level.BlockEvent;

/** Game-bus hooks of the hives: the alarm when the hive is broken or its bees are struck, and bottling honey. */
public final class HiveEvents {
    /** Blocks whose breaking near a Hive Heart raises the alarm (data: #naturequirks:hive_material). */
    public static final TagKey<Block> HIVE_MATERIAL = TagKey.create(Registries.BLOCK,
            Identifier.fromNamespaceAndPath("naturequirks", "hive_material"));
    /** Chance that filling a bottle uses up the honey source (on average four bottles per source, like a bucket). */
    public static final int BOTTLES_PER_SOURCE = 4;

    private HiveEvents() {}

    @SubscribeEvent
    public static void onBreak(BlockEvent.BreakEvent event) {
        Player player = event.getPlayer();
        if (event.getLevel() instanceof ServerLevel level && player != null && !player.isCreative() && !player.isSpectator()
                && event.getState().is(HIVE_MATERIAL)) {
            HiveHeartBlockEntity.alarm(level, event.getPos(), player);
        }
    }

    @SubscribeEvent
    public static void onHurt(LivingIncomingDamageEvent event) {
        Entity victim = event.getEntity();
        if (victim.level() instanceof ServerLevel level && event.getSource().getEntity() instanceof Player player
                && !player.isCreative() && (victim instanceof Bee || HiveHeartBlockEntity.GUARDIAN.equals(net.minecraft.core.registries.BuiltInRegistries.ENTITY_TYPE.getKey(victim.getType())))) {
            HiveHeartBlockEntity.alarm(level, victim.blockPosition(), player);
        }
    }

    /** A glass bottle on a honey source fills with honey (the source runs dry after about four bottles). */
    @SubscribeEvent
    public static void onUseItem(PlayerInteractEvent.RightClickItem event) {
        ItemStack stack = event.getItemStack();
        if (!stack.is(Items.GLASS_BOTTLE)) {
            return;
        }
        Player player = event.getEntity();
        Level level = event.getLevel();
        BlockHitResult hit = Item.getPlayerPOVHitResult(level, player, ClipContext.Fluid.SOURCE_ONLY);
        if (hit.getType() != HitResult.Type.BLOCK) {
            return;
        }
        BlockPos pos = hit.getBlockPos();
        if (!bottle(level, pos, player, event.getHand(), stack)) {
            return;
        }
        event.setCanceled(true);
        event.setCancellationResult(InteractionResult.SUCCESS);
    }

    /** Fills one bottle from the honey source at {@code pos}; false if there is no honey source there. */
    public static boolean bottle(Level level, BlockPos pos, Player player, net.minecraft.world.InteractionHand hand, ItemStack stack) {
        FluidState fluid = level.getFluidState(pos);
        if (!fluid.is(ModHive.HONEY.get()) || !fluid.isSource()) {
            return false;
        }
        if (!level.isClientSide()) {
            level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.BOTTLE_FILL, SoundSource.NEUTRAL, 1.0F, 0.8F);
            player.setItemInHand(hand, ItemUtils.createFilledResult(stack, player, new ItemStack(Items.HONEY_BOTTLE)));
            if (level.getRandom().nextInt(BOTTLES_PER_SOURCE) == 0) {
                level.setBlock(pos, Blocks.AIR.defaultBlockState(), Block.UPDATE_ALL);
            }
            level.gameEvent(player, GameEvent.FLUID_PICKUP, pos);
        }
        return true;
    }
}
