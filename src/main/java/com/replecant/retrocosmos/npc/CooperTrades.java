package com.replecant.retrocosmos.npc;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.registry.ModItems;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.function.Supplier;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.trading.ItemCost;
import net.minecraft.world.item.trading.MerchantOffer;

/**
 * Dr. Cooper's ledger. He BUYS relics of every civilisation the expedition meets (the ancient Venusian ruins pay
 * best, tribal curiosities less) for Space Credits, and SELLS expedition supplies for them. Blueprints go in
 * {@link #BLUEPRINTS} once they exist; bump {@link #VERSION} whenever the ledger changes so existing Coopers
 * rewrite their offers.
 *
 * <p>Items of other parts of the mod are looked up by id, so a missing one just drops out of the ledger.
 */
public final class CooperTrades {
    /** Saved with every Cooper; a Cooper whose ledger is older gets fresh offers. */
    public static final int VERSION = 3;

    private CooperTrades() {}

    /** One line of the ledger: {@code wantCount x want (+ want2) -> giveCount x give}, at most {@code uses} per restock. */
    public record Deal(String want, int wantCount, String want2, int want2Count, String give, int giveCount, int uses, int xp) {
        Optional<MerchantOffer> offer() {
            Optional<Item> a = item(want);
            Optional<Item> r = item(give);
            if (a.isEmpty() || r.isEmpty()) {
                return Optional.empty();
            }
            Optional<ItemCost> b = Optional.empty();
            if (want2 != null) {
                Optional<Item> second = item(want2);
                if (second.isEmpty()) {
                    return Optional.empty();
                }
                b = Optional.of(new ItemCost(second.get(), want2Count));
            }
            return Optional.of(new MerchantOffer(new ItemCost(a.get(), wantCount), b, new ItemStack(r.get(), giveCount), uses, xp, 0.0F));
        }
    }

    private static final String CREDIT = "retrocosmos:space_credit";

    /** "I'll give you N credits for that." */
    static Deal buys(String relic, int count, int credits, int uses) {
        return new Deal(relic, count, null, 0, CREDIT, credits, uses, 4);
    }

    /** "That will be N credits." */
    static Deal sells(int credits, String goods, int count, int uses) {
        return new Deal(CREDIT, credits, null, 0, goods, count, uses, 1);
    }

    /** Ancient relics of the Venusian ruin builders - the heart of the collection. */
    public static final List<Deal> RELICS = List.of(
            buys("retrocosmos:venusian_idol", 1, 12, 6),
            buys("retrocosmos:glyph_tablet", 1, 5, 12),
            buys("retrocosmos:sun_disk_fragment", 2, 3, 16),
            buys("retrocosmos:ancient_amulet", 1, 32, 3));

    /** Curiosities of the living Venus tribes and their hunting grounds. */
    public static final List<Deal> CURIOS = List.of(
            buys("retrocosmos:tribal_mask", 1, 3, 4),
            buys("retrocosmos:shaman_charm", 1, 2, 4),
            buys("retrocosmos:bone_spear", 1, 2, 6),
            buys("retrocosmos:raptor_tooth", 4, 1, 16),
            buys("retrocosmos:dino_hide", 3, 1, 16),
            buys("retrocosmos:venus_amber", 3, 1, 16),
            buys("retrocosmos:tyrannosaurus_fang", 1, 24, 4),
            buys("retrocosmos:plesiosaur_tooth", 1, 6, 6),
            buys("retrocosmos:deinosuchus_tooth", 1, 6, 6),
            buys("retrocosmos:ankylosaurus_plate", 1, 5, 6));

    /** Expedition supplies for sale. */
    public static final List<Deal> SUPPLIES = List.of(
            sells(3, ModItems.ROCKET_FUEL_CANISTER.getId().toString(), 1, 16),
            sells(3, ModItems.LIQUID_OXYGEN_CANISTER.getId().toString(), 1, 16),
            sells(2, "retrocosmos:glowcap_tea", 2, 8),
            sells(1, "minecraft:torch", 16, 16),
            sells(1, "minecraft:bread", 4, 16),
            sells(6, "minecraft:spyglass", 1, 2),
            sells(4, "minecraft:compass", 1, 2));

    /** Blueprints Dr. Cooper will sell one day (rocket parts, base modules...). Empty for now. */
    public static final List<Deal> BLUEPRINTS = List.of();

    /** Relics whose first delivery gets its own excited line (chat.retrocosmos.npc.cooper.first.<path>). */
    public static final Set<String> EXCITING = Set.of("venusian_idol", "glyph_tablet", "sun_disk_fragment", "ancient_amulet",
            "tribal_mask", "bone_spear", "raptor_tooth", "dino_hide", "venus_amber", "shaman_charm", "tyrannosaurus_fang",
            "plesiosaur_tooth", "deinosuchus_tooth", "ankylosaurus_plate");

    private static Optional<Item> item(String id) {
        Identifier key = Identifier.parse(id);
        return BuiltInRegistries.ITEM.getOptional(key).filter(item -> item != Items.AIR);
    }

    /** Is this the expedition's currency? */
    public static boolean isCredit(ItemStack stack) {
        return stack.is(ExpeditionNpcs.SPACE_CREDIT.get());
    }

    /** The whole ledger, in display order: relics, curios, supplies, blueprints. */
    public static List<MerchantOffer> create() {
        List<MerchantOffer> offers = new ArrayList<>();
        for (List<Deal> group : List.of(RELICS, CURIOS, SUPPLIES, BLUEPRINTS)) {
            for (Deal deal : group) {
                deal.offer().ifPresentOrElse(offers::add,
                        () -> RetroCosmos.LOGGER.debug("Dr. Cooper skips a deal for a missing item: {}", deal));
            }
        }
        return offers;
    }

    static Supplier<String> describe(MerchantOffer o) {
        return () -> o.getCostA().getCount() + "x" + BuiltInRegistries.ITEM.getKey(o.getCostA().getItem())
                + (o.getCostB().isEmpty() ? "" : "+" + o.getCostB().getCount() + "x" + BuiltInRegistries.ITEM.getKey(o.getCostB().getItem()))
                + " -> " + o.getResult().getCount() + "x" + BuiltInRegistries.ITEM.getKey(o.getResult().getItem());
    }
}
