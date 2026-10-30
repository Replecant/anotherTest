package com.replecant.retrocosmos.machine;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.registry.ModItems;
import java.util.function.Supplier;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.Item;

/**
 * The two propellant machines share one block entity / menu / screen and differ only in these parameters.
 * <ul>
 *     <li>Fuel Refinery: oil shale + empty canister -> RP-1 kerosene canister.</li>
 *     <li>Air Liquefier: ice (coolant) + empty canister -> liquid oxygen canister.</li>
 * </ul>
 */
public enum MachineKind {
    REFINERY("fuel_refinery", "refinery_input", () -> ModItems.ROCKET_FUEL_CANISTER.get(), 260, 0),
    LIQUEFIER("air_liquefier", "liquefier_input", () -> ModItems.LIQUID_OXYGEN_CANISTER.get(), 200, 1);

    public final String id;
    public final TagKey<Item> input;
    public final Supplier<Item> output;
    public final int processTime;
    /** Row of the machine-specific decorations in the shared GUI texture. */
    public final int guiVariant;

    MachineKind(String id, String inputTag, Supplier<Item> output, int processTime, int guiVariant) {
        this.id = id;
        this.input = TagKey.create(Registries.ITEM, Identifier.fromNamespaceAndPath(RetroCosmos.MODID, inputTag));
        this.output = output;
        this.processTime = processTime;
        this.guiVariant = guiVariant;
    }

    public String langKey() {
        return "block." + RetroCosmos.MODID + "." + id;
    }
}
