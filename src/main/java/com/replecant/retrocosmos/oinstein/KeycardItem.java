package com.replecant.retrocosmos.oinstein;

import java.util.Optional;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

/**
 * A punched security card of the Oinstein Institute (levels A, B, C). It opens the barrier guarded by a
 * {@link KeycardReaderBlock} of the same level and is never used up.
 */
public class KeycardItem extends Item {
    private final KeycardReaderBlock.Clearance clearance;

    public KeycardItem(Properties properties, KeycardReaderBlock.Clearance clearance) {
        super(properties);
        this.clearance = clearance;
    }

    public KeycardReaderBlock.Clearance clearance() {
        return clearance;
    }

    public static Optional<KeycardReaderBlock.Clearance> clearanceOf(ItemStack stack) {
        return stack.getItem() instanceof KeycardItem card ? Optional.of(card.clearance) : Optional.empty();
    }
}
