package com.replecant.retrocosmos.machine;

import com.replecant.retrocosmos.registry.ModItems;
import com.replecant.retrocosmos.registry.ModMenus;
import net.minecraft.core.BlockPos;
import net.minecraft.core.NonNullList;
import net.minecraft.network.chat.Component;
import net.minecraft.world.ContainerHelper;
import net.minecraft.world.Containers;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.FurnaceFuelSlot;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BaseContainerBlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/**
 * Furnace-like propellant machine: burns ordinary furnace fuel, consumes one input item and one empty
 * canister per cycle and fills a propellant canister. Which propellant is decided by {@link MachineKind}.
 */
public class ProcessingBlockEntity extends BaseContainerBlockEntity {
    public static final int SLOT_INPUT = 0;
    public static final int SLOT_CANISTER = 1;
    public static final int SLOT_FUEL = 2;
    public static final int SLOT_OUTPUT = 3;
    public static final int SLOT_COUNT = 4;

    public static final int DATA_PROGRESS = 0;
    public static final int DATA_MAX_PROGRESS = 1;
    public static final int DATA_BURN = 2;
    public static final int DATA_MAX_BURN = 3;
    public static final int DATA_COUNT = 4;

    private final MachineKind kind;
    private NonNullList<ItemStack> items = NonNullList.withSize(SLOT_COUNT, ItemStack.EMPTY);
    private int progress;
    private int burn;
    private int maxBurn;

    private final ContainerData data = new ContainerData() {
        @Override
        public int get(int index) {
            return switch (index) {
                case DATA_PROGRESS -> progress;
                case DATA_MAX_PROGRESS -> kind.processTime;
                case DATA_BURN -> burn;
                case DATA_MAX_BURN -> maxBurn;
                default -> 0;
            };
        }

        @Override
        public void set(int index, int value) {
            switch (index) {
                case DATA_PROGRESS -> progress = value;
                case DATA_BURN -> burn = value;
                case DATA_MAX_BURN -> maxBurn = value;
                default -> { }
            }
        }

        @Override
        public int getCount() {
            return DATA_COUNT;
        }
    };

    public ProcessingBlockEntity(BlockEntityType<?> type, BlockPos pos, BlockState state, MachineKind kind) {
        super(type, pos, state);
        this.kind = kind;
    }

    public MachineKind kind() {
        return kind;
    }

    @Override
    protected Component getDefaultName() {
        return Component.translatable(kind.langKey());
    }

    @Override
    protected NonNullList<ItemStack> getItems() {
        return items;
    }

    @Override
    protected void setItems(NonNullList<ItemStack> items) {
        this.items = items;
    }

    @Override
    public int getContainerSize() {
        return SLOT_COUNT;
    }

    @Override
    protected AbstractContainerMenu createMenu(int id, Inventory inventory) {
        return new ProcessingMenu(kind == MachineKind.REFINERY ? ModMenus.FUEL_REFINERY.get() : ModMenus.AIR_LIQUEFIER.get(),
                id, inventory, this, data, kind);
    }

    @Override
    public boolean canPlaceItem(int slot, ItemStack stack) {
        return switch (slot) {
            case SLOT_INPUT -> stack.is(kind.input);
            case SLOT_CANISTER -> stack.is(ModItems.EMPTY_FUEL_CANISTER.get());
            case SLOT_FUEL -> level != null && level.fuelValues().isFuel(stack) && !FurnaceFuelSlot.isBucket(stack);
            default -> false;
        };
    }

    @Override
    protected void loadAdditional(ValueInput input) {
        super.loadAdditional(input);
        items = NonNullList.withSize(SLOT_COUNT, ItemStack.EMPTY);
        ContainerHelper.loadAllItems(input, items);
        progress = input.getIntOr("progress", 0);
        burn = input.getIntOr("burn", 0);
        maxBurn = input.getIntOr("max_burn", 0);
    }

    @Override
    protected void saveAdditional(ValueOutput output) {
        super.saveAdditional(output);
        ContainerHelper.saveAllItems(output, items);
        output.putInt("progress", progress);
        output.putInt("burn", burn);
        output.putInt("max_burn", maxBurn);
    }

    @Override
    public void preRemoveSideEffects(BlockPos pos, BlockState state) {
        super.preRemoveSideEffects(pos, state);
        if (level != null) {
            Containers.dropContents(level, pos, this);
        }
    }

    private boolean canProcess() {
        if (!items.get(SLOT_INPUT).is(kind.input) || !items.get(SLOT_CANISTER).is(ModItems.EMPTY_FUEL_CANISTER.get())) {
            return false;
        }
        ItemStack out = items.get(SLOT_OUTPUT);
        return out.isEmpty() || (out.is(kind.output.get()) && out.getCount() < out.getMaxStackSize());
    }

    private void finishCycle() {
        items.get(SLOT_INPUT).shrink(1);
        items.get(SLOT_CANISTER).shrink(1);
        ItemStack out = items.get(SLOT_OUTPUT);
        if (out.isEmpty()) {
            items.set(SLOT_OUTPUT, new ItemStack(kind.output.get()));
        } else {
            out.grow(1);
        }
    }

    public static void serverTick(Level level, BlockPos pos, BlockState state, ProcessingBlockEntity be) {
        boolean changed = false;
        if (be.burn > 0) {
            be.burn--;
            changed = true;
        }
        boolean canProcess = be.canProcess();
        if (be.burn <= 0 && canProcess) {
            ItemStack fuel = be.items.get(SLOT_FUEL);
            int duration = level.fuelValues().burnDuration(fuel);
            if (duration > 0) {
                be.burn = duration;
                be.maxBurn = duration;
                fuel.shrink(1);
                changed = true;
            }
        }
        if (be.burn > 0 && canProcess) {
            be.progress++;
            if (be.progress >= be.kind.processTime) {
                be.progress = 0;
                be.finishCycle();
            }
            changed = true;
        } else if (be.progress > 0) {
            be.progress = Math.max(0, be.progress - 2);
            changed = true;
        }
        boolean lit = be.burn > 0;
        if (lit != state.getValue(ProcessingBlock.LIT)) {
            state = state.setValue(ProcessingBlock.LIT, lit);
            level.setBlock(pos, state, Block.UPDATE_ALL);
            changed = true;
        }
        if (changed) {
            setChanged(level, pos, state);
        }
    }
}
