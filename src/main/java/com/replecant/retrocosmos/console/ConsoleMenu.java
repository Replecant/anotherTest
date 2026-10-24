package com.replecant.retrocosmos.console;

import com.replecant.retrocosmos.registry.ModBlocks;
import javax.annotation.Nullable;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.inventory.SimpleContainerData;
import net.minecraft.world.item.ItemStack;

/** Slot-less menu for the Mission Control console; only carries the status readouts and the buttons. */
public class ConsoleMenu extends AbstractContainerMenu {
    public static final int DATA_FOUND = 0;
    public static final int DATA_DX = 1;
    public static final int DATA_DY = 2;
    public static final int DATA_DZ = 3;
    public static final int DATA_FUEL = 4;
    public static final int DATA_OXIDIZER = 5;
    public static final int DATA_PAD = 6;
    public static final int DATA_TOWER = 7;
    public static final int DATA_SUIT = 8;
    public static final int DATA_COUNTDOWN = 9;
    public static final int DATA_LAST_CHECK = 10;
    public static final int DATA_COUNT = 11;

    @Nullable
    private final ConsoleBlockEntity console;
    private final ContainerData data;
    private final ContainerLevelAccess access;

    /** Client-side constructor. */
    public ConsoleMenu(MenuType<?> type, int id, Inventory inventory) {
        this(type, id, inventory, null, new SimpleContainerData(DATA_COUNT), ContainerLevelAccess.NULL);
    }

    public ConsoleMenu(MenuType<?> type, int id, Inventory inventory, @Nullable ConsoleBlockEntity console,
                       ContainerData data, ContainerLevelAccess access) {
        super(type, id);
        checkContainerDataCount(data, DATA_COUNT);
        this.console = console;
        this.data = data;
        this.access = access;
        addDataSlots(data);
    }

    public int get(int index) {
        return data.get(index);
    }

    @Override
    public boolean clickMenuButton(Player player, int button) {
        if (console != null && player instanceof ServerPlayer serverPlayer) {
            console.handleButton(serverPlayer, button);
        }
        return true;
    }

    @Override
    public ItemStack quickMoveStack(Player player, int index) {
        return ItemStack.EMPTY;
    }

    @Override
    public boolean stillValid(Player player) {
        return stillValid(access, player, ModBlocks.MISSION_CONTROL_CONSOLE.get());
    }
}
