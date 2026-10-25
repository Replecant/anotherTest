package com.replecant.retrocosmos.tribe;

import com.replecant.retrocosmos.RetroCosmos;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.function.Supplier;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.trading.ItemCost;
import net.minecraft.world.item.trading.MerchantOffer;
import net.minecraft.world.level.ItemLike;

/**
 * What the tribes trade. They prize Earth goods - cooked meat, bread, glass, iron, torches, clever sky-man gadgets -
 * and pay in Venus goods: amber, raptor teeth, dinosaur hide, fern fiber, glowcap tea, masks, charms and spears.
 * Each tribesman offers a random handful of its role's trades; the chief offers all of his.
 */
public final class TribeTrades {
    private TribeTrades() {}

    private record Trade(Supplier<ItemCost> a, Supplier<Optional<ItemCost>> b, Supplier<ItemStack> result, int uses, int xp) {
        MerchantOffer offer() {
            return new MerchantOffer(a.get(), b.get(), result.get(), uses, xp, 0.05F);
        }
    }

    private static Trade buy(ItemLike want, int count, Supplier<? extends ItemLike> give, int giveCount, int uses) {
        return new Trade(() -> new ItemCost(want, count), Optional::empty, () -> new ItemStack(give.get(), giveCount), uses, 2);
    }

    private static Trade buy2(Supplier<? extends ItemLike> want, int count, Supplier<? extends ItemLike> want2, int count2,
                              Supplier<? extends ItemLike> give, int giveCount, int uses) {
        return new Trade(() -> new ItemCost(want.get(), count), () -> Optional.of(new ItemCost(want2.get(), count2)),
                () -> new ItemStack(give.get(), giveCount), uses, 5);
    }

    private static Trade sell(int amber, Supplier<? extends ItemLike> give, int giveCount, int uses) {
        return new Trade(() -> new ItemCost(ModTribes.VENUS_AMBER.get(), amber), Optional::empty,
                () -> new ItemStack(give.get(), giveCount), uses, 4);
    }

    /** Items of other parts of the mod that may or may not exist (looked up by id, so nothing breaks if not). */
    private static Optional<Item> optional(String path) {
        return BuiltInRegistries.ITEM.getOptional(Identifier.fromNamespaceAndPath(RetroCosmos.MODID, path))
                .filter(item -> item != Items.AIR);
    }

    private static List<Trade> pool(TribeRole role) {
        List<Trade> list = new ArrayList<>();
        switch (role) {
            case HUNTER -> {
                list.add(buy(Items.COOKED_BEEF, 4, ModTribes.RAPTOR_TOOTH, 3, 8));
                list.add(buy(Items.COOKED_PORKCHOP, 4, ModTribes.RAPTOR_TOOTH, 3, 8));
                list.add(buy(Items.TORCH, 8, ModTribes.DINO_HIDE, 1, 8));
                list.add(buy(Items.ARROW, 12, ModTribes.DINO_HIDE, 1, 8));
                list.add(buy(Items.SHEARS, 1, ModTribes.DINO_HIDE, 3, 2));
                list.add(buy(Items.IRON_INGOT, 3, ModTribes.BONE_SPEAR, 1, 3));
                list.add(sell(3, ModTribes.BONE_SPEAR, 1, 3));
            }
            case GATHERER -> {
                list.add(buy(Items.BREAD, 3, ModTribes.FERN_FIBER, 6, 12));
                list.add(buy(Items.COOKIE, 4, ModTribes.FERN_FIBER, 5, 12));
                list.add(buy(Items.SUGAR, 5, ModTribes.GLOWCAP_TEA, 2, 8));
                list.add(buy(Items.APPLE, 3, ModTribes.GLOWCAP_TEA, 1, 8));
                list.add(buy(Items.GLASS, 4, ModTribes.VENUS_AMBER, 2, 8));
                list.add(buy(Items.GLASS_BOTTLE, 3, ModTribes.VENUS_AMBER, 1, 8));
                list.add(buy(Items.STRING, 8, ModTribes.VENUS_AMBER, 1, 8));
                optional("venus_glowcap").ifPresent(glowcap -> list.add(sell(1, () -> glowcap, 4, 8)));
            }
            case SHAMAN -> {
                list.add(buy2(ModTribes.VENUS_AMBER, 3, ModTribes.DINO_HIDE, 1, ModTribes.TRIBAL_MASK, 1, 3));
                list.add(sell(6, ModTribes.SHAMAN_CHARM, 1, 4));
                list.add(buy(Items.COMPASS, 1, ModTribes.VENUS_AMBER, 5, 2));
                list.add(buy(Items.CLOCK, 1, ModTribes.VENUS_AMBER, 6, 2));
                list.add(buy(Items.GLOWSTONE_DUST, 4, ModTribes.SHAMAN_CHARM, 1, 3));
                list.add(buy(Items.REDSTONE, 4, ModTribes.VENUS_AMBER, 1, 8));
                list.add(buy(Items.GOLD_NUGGET, 6, ModTribes.GLOWCAP_TEA, 2, 8));
            }
            case CHIEF -> {
                list.add(buy(Items.GOLD_INGOT, 2, ModTribes.VENUS_AMBER, 3, 6));
                list.add(buy(Items.DIAMOND, 1, ModTribes.VENUS_AMBER, 6, 3));
                list.add(buy(Items.SPYGLASS, 1, ModTribes.VENUS_AMBER, 8, 2));
                list.add(buy(Items.IRON_SWORD, 1, ModTribes.VENUS_AMBER, 4, 2));
                list.add(sell(10, ModTribes.TRIBAL_MASK, 1, 2));
                list.add(sell(4, ModTribes.DINO_HIDE, 3, 6));
            }
        }
        return list;
    }

    /** Ancient artifacts from the Venusian ruins, if that part of the mod is present: the shaman and chief covet them. */
    private static List<Trade> artifacts(TribeRole role) {
        List<Trade> list = new ArrayList<>();
        if (role == TribeRole.SHAMAN || role == TribeRole.CHIEF) {
            optional("venusian_idol").ifPresent(idol -> list.add(relic(idol, 1, ModTribes.VENUS_AMBER, 12)));
            optional("glyph_tablet").ifPresent(tablet -> list.add(relic(tablet, 1, ModTribes.SHAMAN_CHARM, 2)));
        }
        if (role == TribeRole.SHAMAN) {
            optional("ancient_amulet").ifPresent(amulet -> list.add(relic(amulet, 1, ModTribes.VENUS_AMBER, 24)));
        }
        if (role == TribeRole.CHIEF) {
            optional("sun_disk_fragment").ifPresent(disk -> list.add(relic(disk, 2, ModTribes.VENUS_AMBER, 5)));
        }
        return list;
    }

    private static Trade relic(Item want, int count, Supplier<? extends ItemLike> give, int giveCount) {
        return new Trade(() -> new ItemCost(want, count), Optional::empty, () -> new ItemStack(give.get(), giveCount), 2, 10);
    }

    /** A fresh set of offers for a tribesman of this role. */
    public static List<MerchantOffer> create(TribeRole role, RandomSource random) {
        List<Trade> pool = pool(role);
        int keep = role == TribeRole.CHIEF ? pool.size() : Math.min(pool.size(), 4 + random.nextInt(2));
        List<MerchantOffer> offers = new ArrayList<>();
        while (offers.size() < keep && !pool.isEmpty()) {
            offers.add(pool.remove(random.nextInt(pool.size())).offer());
        }
        artifacts(role).forEach(t -> offers.add(t.offer()));
        return offers;
    }
}
