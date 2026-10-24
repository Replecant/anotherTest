package com.replecant.retrocosmos.machine;

import com.replecant.retrocosmos.registry.ModItems;
import net.minecraft.world.Container;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.FurnaceFuelSlot;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.inventory.SimpleContainerData;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;

/** Menu for {@link ProcessingBlockEntity}: input, empty canister, furnace fuel, output + player inventory. */
public class ProcessingMenu extends AbstractContainerMenu {
    private static final int INV_START = ProcessingBlockEntity.SLOT_COUNT;
    private static final int INV_END = INV_START + 27;
    private static final int HOTBAR_END = INV_END + 9;

    private final Container container;
    private final ContainerData data;
    private final MachineKind kind;

    /** Client-side constructor. */
    public ProcessingMenu(MenuType<?> type, int id, Inventory inventory, MachineKind kind) {
        this(type, id, inventory, new SimpleContainer(ProcessingBlockEntity.SLOT_COUNT),
                new SimpleContainerData(ProcessingBlockEntity.DATA_COUNT), kind);
    }

    public ProcessingMenu(MenuType<?> type, int id, Inventory inventory, Container container, ContainerData data, MachineKind kind) {
        super(type, id);
        checkContainerSize(container, ProcessingBlockEntity.SLOT_COUNT);
        checkContainerDataCount(data, ProcessingBlockEntity.DATA_COUNT);
        this.container = container;
        this.data = data;
        this.kind = kind;
        addSlot(new Slot(container, ProcessingBlockEntity.SLOT_INPUT, 56, 17) {
            @Override
            public boolean mayPlace(ItemStack stack) {
                return stack.is(kind.input);
            }
        });
        addSlot(new Slot(container, ProcessingBlockEntity.SLOT_CANISTER, 32, 35) {
            @Override
            public boolean mayPlace(ItemStack stack) {
                return stack.is(ModItems.EMPTY_FUEL_CANISTER.get());
            }
        });
        addSlot(new Slot(container, ProcessingBlockEntity.SLOT_FUEL, 56, 53) {
            @Override
            public boolean mayPlace(ItemStack stack) {
                return isFuel(inventory.player, stack);
            }
        });
        addSlot(new Slot(container, ProcessingBlockEntity.SLOT_OUTPUT, 116, 35) {
            @Override
            public boolean mayPlace(ItemStack stack) {
                return false;
            }
        });
        addStandardInventorySlots(inventory, 8, 84);
        addDataSlots(data);
    }

    private static boolean isFuel(Player player, ItemStack stack) {
        return player.level().fuelValues().isFuel(stack) && !FurnaceFuelSlot.isBucket(stack);
    }

    public MachineKind kind() {
        return kind;
    }

    public int progressScaled(int width) {
        int max = data.get(ProcessingBlockEntity.DATA_MAX_PROGRESS);
        return max == 0 ? 0 : data.get(ProcessingBlockEntity.DATA_PROGRESS) * width / max;
    }

    public int burnScaled(int height) {
        int max = data.get(ProcessingBlockEntity.DATA_MAX_BURN);
        if (max == 0) {
            max = 200;
        }
        return data.get(ProcessingBlockEntity.DATA_BURN) * height / max;
    }

    public boolean isLit() {
        return data.get(ProcessingBlockEntity.DATA_BURN) > 0;
    }

    @Override
    public boolean stillValid(Player player) {
        return container.stillValid(player);
    }

    @Override
    public ItemStack quickMoveStack(Player player, int index) {
        ItemStack result = ItemStack.EMPTY;
        Slot slot = slots.get(index);
        if (slot.hasItem()) {
            ItemStack stack = slot.getItem();
            result = stack.copy();
            if (index < INV_START) {
                if (!moveItemStackTo(stack, INV_START, HOTBAR_END, true)) {
                    return ItemStack.EMPTY;
                }
                slot.onQuickCraft(stack, result);
            } else {
                boolean moved;
                if (stack.is(kind.input)) {
                    moved = moveItemStackTo(stack, ProcessingBlockEntity.SLOT_INPUT, ProcessingBlockEntity.SLOT_INPUT + 1, false);
                } else if (stack.is(ModItems.EMPTY_FUEL_CANISTER.get())) {
                    moved = moveItemStackTo(stack, ProcessingBlockEntity.SLOT_CANISTER, ProcessingBlockEntity.SLOT_CANISTER + 1, false);
                } else if (isFuel(player, stack)) {
                    moved = moveItemStackTo(stack, ProcessingBlockEntity.SLOT_FUEL, ProcessingBlockEntity.SLOT_FUEL + 1, false);
                } else if (index < INV_END) {
                    moved = moveItemStackTo(stack, INV_END, HOTBAR_END, false);
                } else {
                    moved = moveItemStackTo(stack, INV_START, INV_END, false);
                }
                if (!moved) {
                    return ItemStack.EMPTY;
                }
            }
            if (stack.isEmpty()) {
                slot.setByPlayer(ItemStack.EMPTY);
            } else {
                slot.setChanged();
            }
            if (stack.getCount() == result.getCount()) {
                return ItemStack.EMPTY;
            }
            slot.onTake(player, stack);
        }
        return result;
    }
}
