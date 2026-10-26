package com.replecant.retrocosmos.npc;

import com.replecant.retrocosmos.npc.CooperTrades.Deal;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.world.item.trading.MerchantOffer;

/**
 * The catalogue of Betty Palmer's Atomic Home Showroom on Freedom Station: every piece of retro-futurist furniture and
 * decor in the mod, sold for Space Credits, grouped like the pages of a 1950s mail-order catalogue. Functional
 * rocketry (pads, towers, refineries), keycard / laser security and anything unbreakable are not for sale.
 *
 * <p>Bump {@link #VERSION} whenever the catalogue changes so existing showrooms rewrite their offers. Ids are looked up
 * by name, so a piece that no longer exists simply drops out.
 */
public final class DecoratorTrades {
    /** Saved with every decorator; an older catalogue gets fresh offers. */
    public static final int VERSION = 1;
    /** Plenty per restock: it is a shop, not a bazaar. */
    private static final int STOCK = 64;

    private DecoratorTrades() {}

    private static Deal sell(int credits, String piece, int count) {
        return CooperTrades.sells(credits, "retrocosmos:" + piece, count, STOCK);
    }

    /** Chairs, sofas and beds. */
    public static final List<Deal> SEATING = List.of(
            sell(2, "diner_stool", 1),
            sell(4, "egg_chair", 1),
            sell(4, "captain_chair", 1),
            sell(6, "googie_sofa", 1),
            sell(6, "crew_bunk", 1));

    /** Tables and benches. */
    public static final List<Deal> TABLES = List.of(
            sell(3, "boomerang_table", 1),
            sell(5, "retro_workbench", 1));

    /** Lamps, lights and signs. */
    public static final List<Deal> LIGHTING = List.of(
            sell(2, "rocket_table_lamp", 2),
            sell(3, "atomic_floor_lamp", 1),
            sell(2, "ceiling_light", 2),
            sell(2, "wall_sconce", 2),
            sell(8, "sputnik_chandelier", 1),
            sell(4, "neon_rocket_sign", 1));

    /** Lockers, crates and cabinets. */
    public static final List<Deal> STORAGE = List.of(
            sell(3, "cargo_crate", 1),
            sell(4, "supply_cabinet", 1),
            sell(5, "crew_locker", 1),
            sell(6, "tape_archive", 1),
            sell(4, "oxygen_tank_rack", 1));

    /** The modern kitchen, diner and hydroponic garden. */
    public static final List<Deal> KITCHEN = List.of(
            sell(6, "galley_stove", 1),
            sell(4, "lab_sink", 1),
            sell(8, "vending_machine", 1),
            sell(4, "hydroponic_planter", 1));

    /** Televisions, radios and the space-age electronics. */
    public static final List<Deal> ELECTRONICS = List.of(
            sell(4, "tube_radio", 1),
            sell(8, "atomic_tv", 1),
            sell(5, "control_panel", 1),
            sell(7, "radar_scope", 1),
            sell(8, "computer_bank", 1),
            sell(6, "telescope", 1),
            sell(16, "reactor_core", 1));

    /** Clocks, posters, globes, panels, tiles, windows and doors. */
    public static final List<Deal> DECOR = List.of(
            sell(3, "starburst_clock", 1),
            sell(5, "space_globe", 1),
            sell(2, "star_chart", 1),
            sell(1, "poster_liftoff", 1),
            sell(1, "poster_vesper", 1),
            sell(1, "poster_space_pop", 1),
            sell(1, "poster_suit_check", 1),
            sell(1, "poster_homestead", 1),
            sell(1, "poster_freedom", 1),
            sell(2, "checkered_tile", 16),
            sell(2, "turquoise_panel", 16),
            sell(2, "cream_panel", 16),
            sell(2, "chrome_trim", 8),
            sell(2, "hull_panel", 16),
            sell(2, "hull_panel_striped", 16),
            sell(2, "floor_grate", 8),
            sell(2, "porthole_window", 4),
            sell(2, "hull_window", 4),
            sell(3, "station_door", 1),
            sell(4, "airlock_door", 1));

    /** The catalogue, page by page. */
    public static final List<List<Deal>> CATALOGUE = List.of(SEATING, TABLES, LIGHTING, STORAGE, KITCHEN, ELECTRONICS, DECOR);

    /** Every offer, in catalogue order. */
    public static List<MerchantOffer> create() {
        List<MerchantOffer> offers = new ArrayList<>();
        for (List<Deal> page : CATALOGUE) {
            for (Deal deal : page) {
                deal.offer().ifPresent(offers::add);
            }
        }
        return offers;
    }

    /** Catalogue entries whose item does not exist (for checks; should be empty). */
    public static List<String> unavailable() {
        List<String> out = new ArrayList<>();
        for (List<Deal> page : CATALOGUE) {
            for (Deal deal : page) {
                if (deal.offer().isEmpty()) {
                    out.add(deal.give());
                }
            }
        }
        return out;
    }

    /** Number of entries in the catalogue. */
    public static int size() {
        return CATALOGUE.stream().mapToInt(List::size).sum();
    }
}
