package com.replecant.naturequirks.stonehead;

import com.replecant.naturequirks.NatureQuirks;
import java.util.List;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.stats.Stats;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.storage.loot.LootParams;
import net.minecraft.world.level.storage.loot.LootTable;
import net.minecraft.world.level.storage.loot.parameters.LootContextParamSets;
import net.minecraft.world.level.storage.loot.parameters.LootContextParams;
import net.minecraft.world.phys.Vec3;

/**
 * Geode: a rough lump of rock a stone head spat out, with crystals glinting in a crack. Use it to crack it open for
 * what's inside (loot table naturequirks:gameplay/geode). A geode chewed from a delicacy glitters and carries luck,
 * which means more finds and better odds for the rare ones.
 */
public class GeodeItem extends Item {
    public static final ResourceKey<LootTable> LOOT = ResourceKey.create(Registries.LOOT_TABLE,
            Identifier.fromNamespaceAndPath(NatureQuirks.MODID, "gameplay/geode"));

    public GeodeItem(Properties properties) {
        super(properties);
    }

    /** A geode carrying this much loot luck (0 = plain). */
    public static ItemStack create(int luck) {
        ItemStack stack = new ItemStack(StoneHeads.GEODE.get());
        if (luck > 0) {
            stack.set(StoneHeads.GEODE_LUCK.get(), luck);
            stack.set(DataComponents.RARITY, Rarity.UNCOMMON);
            stack.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(List.of(), List.of(true), List.of(), List.of()));
        }
        return stack;
    }

    public static int luck(ItemStack stack) {
        return stack.getOrDefault(StoneHeads.GEODE_LUCK.get(), 0);
    }

    @Override
    public Component getName(ItemStack stack) {
        return luck(stack) > 0 ? Component.translatable("item.naturequirks.geode.rich") : super.getName(stack);
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        player.getCooldowns().addCooldown(stack, 6);
        if (level instanceof ServerLevel server) {
            Vec3 at = player.getEyePosition().add(player.getLookAngle().scale(0.6)).add(0.0, -0.35, 0.0);
            for (ItemStack found : crack(server, player, at, luck(stack))) {
                if (!player.getInventory().add(found)) {
                    player.drop(found, false);
                }
            }
            server.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.PLAYERS, 1.0F, 0.9F);
            server.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.STONE_BREAK, SoundSource.PLAYERS, 0.8F, 1.2F);
            server.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.CALCITE.defaultBlockState()), at.x, at.y, at.z,
                    14, 0.15, 0.15, 0.15, 0.1);
            server.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.AMETHYST_BLOCK.defaultBlockState()), at.x, at.y, at.z,
                    10, 0.12, 0.12, 0.12, 0.1);
            player.awardStat(Stats.ITEM_USED.get(this));
            stack.consume(1, player);
        }
        return InteractionResult.SUCCESS;
    }

    /** Rolls what's inside a geode: the gameplay/geode table, with the geode's luck plus the opener's. */
    public static List<ItemStack> crack(ServerLevel level, Entity opener, Vec3 at, int luck) {
        float openerLuck = opener instanceof Player p ? p.getLuck() : 0.0F;
        LootParams params = new LootParams.Builder(level)
                .withParameter(LootContextParams.ORIGIN, at)
                .withParameter(LootContextParams.THIS_ENTITY, opener)
                .withLuck(luck + openerLuck)
                .create(LootContextParamSets.GIFT);
        return level.getServer().reloadableRegistries().getLootTable(LOOT).getRandomItems(params);
    }
}
