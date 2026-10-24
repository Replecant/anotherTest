package com.replecant.retrocosmos.console;

import com.replecant.retrocosmos.flight.RocketEntity;
import com.replecant.retrocosmos.launch.LaunchSite;
import com.replecant.retrocosmos.registry.ModBlockEntities;
import com.replecant.retrocosmos.registry.ModMenus;
import java.util.List;
import javax.annotation.Nullable;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.MenuProvider;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/**
 * Mission Control console: watches the nearest launch site, runs the GO / NO-GO check and the
 * T-minus 10 countdown. All state is synced to the screen through the menu's {@link ContainerData}.
 */
public class ConsoleBlockEntity extends BlockEntity implements MenuProvider {
    public static final int COUNTDOWN_SECONDS = 10;
    private static final int RESCAN_INTERVAL = 20;
    private static final double BROADCAST_RANGE = 48.0;

    public static final int BUTTON_CHECK = 0;
    public static final int BUTTON_COUNTDOWN = 1;
    public static final int BUTTON_ABORT = 2;

    public static final int CHECK_NONE = 0, CHECK_GO = 1, CHECK_NO_GO = 2;

    private LaunchSite.Status status = LaunchSite.Status.NONE;
    private long lastScan = Long.MIN_VALUE;
    /** Astronauts within this many blocks of the rocket board it at T-0. */
    private static final int CREW_RANGE = 6;

    /** Ticks left in the countdown, or -1 when idle. */
    private int countdown = -1;
    private int lastCheck = CHECK_NONE;

    public ConsoleBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlockEntities.MISSION_CONTROL_CONSOLE.get(), pos, state);
    }

    public LaunchSite.Status status() {
        if (level != null && level.getGameTime() - lastScan >= RESCAN_INTERVAL) {
            rescan();
        }
        return status;
    }

    private void rescan() {
        if (level != null) {
            status = LaunchSite.scan(level, worldPosition);
            lastScan = level.getGameTime();
        }
    }

    public int countdown() {
        return countdown;
    }

    public int lastCheck() {
        return lastCheck;
    }

    @Override
    public Component getDisplayName() {
        return Component.translatable("block.retrocosmos.mission_control_console");
    }

    @Nullable
    @Override
    public AbstractContainerMenu createMenu(int id, Inventory inventory, Player player) {
        return new ConsoleMenu(ModMenus.MISSION_CONTROL_CONSOLE.get(), id, inventory, this,
                new ServerData(this, player), ContainerLevelAccess.create(level, worldPosition));
    }

    @Override
    protected void loadAdditional(ValueInput input) {
        super.loadAdditional(input);
        countdown = input.getIntOr("countdown", -1);
        lastCheck = input.getIntOr("last_check", CHECK_NONE);
    }

    @Override
    protected void saveAdditional(ValueOutput output) {
        super.saveAdditional(output);
        output.putInt("countdown", countdown);
        output.putInt("last_check", lastCheck);
    }

    // ------------------------------------------------------------------
    // Buttons (arrive through AbstractContainerMenu#clickMenuButton)
    // ------------------------------------------------------------------

    public void handleButton(ServerPlayer player, int button) {
        if (level == null) {
            return;
        }
        switch (button) {
            case BUTTON_CHECK -> {
                rescan();
                boolean go = status.go(LaunchSite.suitBits(player));
                lastCheck = go ? CHECK_GO : CHECK_NO_GO;
                LaunchSite.sendChecklist(player, status);
                level.playSound(null, worldPosition, go ? SoundEvents.NOTE_BLOCK_PLING.value() : SoundEvents.NOTE_BLOCK_BASS.value(),
                        SoundSource.BLOCKS, 1.0F, go ? 1.5F : 0.5F);
                if (go) {
                    LaunchSite.award(player, "stage1/ready_for_launch", "checklist_passed");
                }
                if (status.padOk()) {
                    LaunchSite.award(player, "stage1/launch_complex", "pad_complete");
                }
                setChanged();
            }
            case BUTTON_COUNTDOWN -> {
                if (countdown >= 0) {
                    return;
                }
                rescan();
                if (!status.go(LaunchSite.suitBits(player))) {
                    lastCheck = CHECK_NO_GO;
                    player.displayClientMessage(Component.translatable("message.retrocosmos.console.no_go").withStyle(ChatFormatting.RED), false);
                    level.playSound(null, worldPosition, SoundEvents.NOTE_BLOCK_BASS.value(), SoundSource.BLOCKS, 1.0F, 0.5F);
                    return;
                }
                lastCheck = CHECK_GO;
                countdown = COUNTDOWN_SECONDS * 20;
                broadcast(Component.translatable("message.retrocosmos.console.countdown_started").withStyle(ChatFormatting.AQUA, ChatFormatting.BOLD));
                setChanged();
            }
            case BUTTON_ABORT -> {
                if (countdown >= 0) {
                    abort(Component.translatable("message.retrocosmos.console.abort_manual"));
                }
            }
            default -> { }
        }
    }

    private void abort(Component reason) {
        countdown = -1;
        lastCheck = CHECK_NO_GO;
        broadcast(Component.translatable("message.retrocosmos.console.hold").withStyle(ChatFormatting.RED, ChatFormatting.BOLD));
        broadcast(reason.copy().withStyle(ChatFormatting.RED));
        if (level != null) {
            level.playSound(null, worldPosition, SoundEvents.NOTE_BLOCK_BASS.value(), SoundSource.BLOCKS, 1.0F, 0.4F);
        }
        setChanged();
    }

    private List<ServerPlayer> nearbyPlayers() {
        if (!(level instanceof ServerLevel serverLevel)) {
            return List.of();
        }
        return serverLevel.players().stream()
                .filter(p -> p.distanceToSqr(worldPosition.getX() + 0.5, worldPosition.getY() + 0.5, worldPosition.getZ() + 0.5) <= BROADCAST_RANGE * BROADCAST_RANGE)
                .toList();
    }

    private void broadcast(Component message) {
        for (ServerPlayer player : nearbyPlayers()) {
            player.displayClientMessage(message, false);
        }
    }

    // ------------------------------------------------------------------
    // Countdown
    // ------------------------------------------------------------------

    public static void serverTick(Level level, BlockPos pos, BlockState state, ConsoleBlockEntity console) {
        if (console.countdown < 0) {
            return;
        }
        if (console.countdown % 20 == 0) {
            int seconds = console.countdown / 20;
            console.rescan();
            if (!console.status.vehicleGo()) {
                console.abort(Component.translatable("message.retrocosmos.console.abort_vehicle"));
                return;
            }
            if (seconds > 0) {
                console.broadcast(Component.translatable("message.retrocosmos.console.t_minus", seconds).withStyle(ChatFormatting.YELLOW));
                level.playSound(null, pos, SoundEvents.NOTE_BLOCK_PLING.value(), SoundSource.BLOCKS, 1.0F, seconds <= 3 ? 1.8F : 1.2F);
                if (seconds == 3 && console.status.base() != null) {
                    console.broadcast(Component.translatable("message.retrocosmos.console.ignition").withStyle(ChatFormatting.GOLD));
                    level.playSound(null, console.status.base(), SoundEvents.FIRECHARGE_USE, SoundSource.BLOCKS, 1.5F, 0.6F);
                }
                if (seconds <= 3 && console.status.base() != null && level instanceof ServerLevel serverLevel) {
                    BlockPos base = console.status.base();
                    serverLevel.sendParticles(ParticleTypes.FLAME, base.getX() + 0.5, base.getY() + 0.1, base.getZ() + 0.5, 30, 0.3, 0.1, 0.3, 0.05);
                    serverLevel.sendParticles(ParticleTypes.LARGE_SMOKE, base.getX() + 0.5, base.getY() + 0.1, base.getZ() + 0.5, 40, 1.2, 0.2, 1.2, 0.02);
                }
            } else {
                console.liftoff(level);
                return;
            }
        }
        console.countdown--;
        if (console.countdown < 0) {
            console.countdown = -1;
        }
    }

    private void liftoff(Level level) {
        countdown = -1;
        lastCheck = CHECK_GO;
        BlockPos base = status.base() != null ? status.base() : worldPosition;
        level.playSound(null, worldPosition, SoundEvents.BEACON_ACTIVATE, SoundSource.BLOCKS, 1.0F, 1.2F);
        if (level instanceof ServerLevel serverLevel && status.base() != null) {
            // astronauts in full suits standing on or next to the pad ride along
            List<ServerPlayer> crew = serverLevel.players().stream()
                    .filter(p -> !p.isPassenger() && LaunchSite.suitBits(p) == LaunchSite.SUIT_FULL)
                    .filter(p -> p.distanceToSqr(base.getX() + 0.5, base.getY() + 0.5, base.getZ() + 0.5) <= CREW_RANGE * CREW_RANGE)
                    .limit(2)
                    .toList();
            RocketEntity.launchFrom(serverLevel, base, crew, false);
        }
        for (ServerPlayer player : nearbyPlayers()) {
            LaunchSite.award(player, "stage1/countdown", "liftoff");
        }
        setChanged();
    }

    /** Server-side view of the console for one viewer; the suit bits are the viewer's own. */
    private record ServerData(ConsoleBlockEntity console, Player viewer) implements ContainerData {
        @Override
        public int get(int index) {
            LaunchSite.Status s = console.status();
            BlockPos base = s.base();
            return switch (index) {
                case ConsoleMenu.DATA_FOUND -> s.found() ? 1 : 0;
                case ConsoleMenu.DATA_DX -> base == null ? 0 : base.getX() - console.worldPosition.getX();
                case ConsoleMenu.DATA_DY -> base == null ? 0 : base.getY() - console.worldPosition.getY();
                case ConsoleMenu.DATA_DZ -> base == null ? 0 : base.getZ() - console.worldPosition.getZ();
                case ConsoleMenu.DATA_FUEL -> s.fuel();
                case ConsoleMenu.DATA_OXIDIZER -> s.oxidizer();
                case ConsoleMenu.DATA_PAD -> s.padCount();
                case ConsoleMenu.DATA_TOWER -> s.towerHeight();
                case ConsoleMenu.DATA_SUIT -> LaunchSite.suitBits(viewer);
                case ConsoleMenu.DATA_COUNTDOWN -> console.countdown;
                case ConsoleMenu.DATA_LAST_CHECK -> console.lastCheck;
                default -> 0;
            };
        }

        @Override
        public void set(int index, int value) {
        }

        @Override
        public int getCount() {
            return ConsoleMenu.DATA_COUNT;
        }
    }
}
