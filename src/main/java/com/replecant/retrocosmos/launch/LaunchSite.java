package com.replecant.retrocosmos.launch;

import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.block.LaunchPadBlock;
import com.replecant.retrocosmos.block.RocketBlock;
import com.replecant.retrocosmos.block.ServiceTowerBlock;
import com.replecant.retrocosmos.registry.ModBlocks;
import com.replecant.retrocosmos.registry.ModItems;
import javax.annotation.Nullable;
import net.minecraft.ChatFormatting;
import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;

/**
 * Inspects a launch site: the Liberty I rocket, its 3x3 launch pad, the service tower beside it and
 * the propellant load. Shared by the rocket's own checklist and the Mission Control console.
 */
public final class LaunchSite {
    public static final int SCAN_RADIUS = 12;
    public static final int SCAN_HEIGHT = 6;
    public static final int PAD_SIZE = 9;

    /** Snapshot of a launch site. {@code base} is the bottom rocket block, or null when no rocket was found. */
    public record Status(@Nullable BlockPos base, int fuel, int oxidizer, int padCount, int towerHeight) {
        public static final Status NONE = new Status(null, 0, 0, 0, 0);

        public boolean found() {
            return base != null;
        }

        public boolean fuelOk() {
            return fuel >= RocketBlock.MAX_FUEL;
        }

        public boolean oxidizerOk() {
            return oxidizer >= RocketBlock.MAX_FUEL;
        }

        public boolean padOk() {
            return padCount >= PAD_SIZE;
        }

        public boolean towerOk() {
            return towerHeight >= ServiceTowerBlock.MIN_HEIGHT;
        }

        /** Everything on the vehicle side is GO (pad, tower, propellants). */
        public boolean vehicleGo() {
            return found() && padOk() && towerOk() && fuelOk() && oxidizerOk();
        }

        public boolean go(int suitBits) {
            return vehicleGo() && suitBits == SUIT_FULL;
        }
    }

    public static final int SUIT_HELMET = 1, SUIT_CHEST = 2, SUIT_LEGS = 4, SUIT_BOOTS = 8, SUIT_FULL = 15;

    private LaunchSite() {}

    /** Finds the rocket nearest to {@code origin} (within the scan box) and inspects its launch site. */
    public static Status scan(Level level, BlockPos origin) {
        BlockPos best = null;
        double bestDist = Double.MAX_VALUE;
        BlockPos.MutableBlockPos cursor = new BlockPos.MutableBlockPos();
        for (int dx = -SCAN_RADIUS; dx <= SCAN_RADIUS; dx++) {
            for (int dz = -SCAN_RADIUS; dz <= SCAN_RADIUS; dz++) {
                for (int dy = -SCAN_HEIGHT; dy <= SCAN_HEIGHT; dy++) {
                    cursor.set(origin.getX() + dx, origin.getY() + dy, origin.getZ() + dz);
                    BlockState state = level.getBlockState(cursor);
                    if (state.is(ModBlocks.ROCKET.get()) && state.getValue(RocketBlock.PART).offset() == 0) {
                        double d = cursor.distSqr(origin);
                        if (d < bestDist) {
                            bestDist = d;
                            best = cursor.immutable();
                        }
                    }
                }
            }
        }
        return best == null ? Status.NONE : inspect(level, best);
    }

    /** Inspects the rocket that contains the block at {@code pos} (any of its three parts). */
    public static Status inspect(Level level, BlockPos pos) {
        BlockState state = level.getBlockState(pos);
        if (!state.is(ModBlocks.ROCKET.get())) {
            return Status.NONE;
        }
        BlockPos base = pos.below(state.getValue(RocketBlock.PART).offset());
        BlockState baseState = level.getBlockState(base);
        if (!baseState.is(ModBlocks.ROCKET.get())) {
            return Status.NONE;
        }
        BlockPos padCenter = base.below();
        int padCount = level.getBlockState(padCenter).is(ModBlocks.LAUNCH_PAD.get()) ? LaunchPadBlock.countPad(level, padCenter) : 0;
        return new Status(base, baseState.getValue(RocketBlock.FUEL), baseState.getValue(RocketBlock.OXIDIZER),
                padCount, towerHeight(level, padCenter));
    }

    /** Tallest column of service tower blocks standing in the ring right outside the 3x3 pad. */
    private static int towerHeight(Level level, BlockPos padCenter) {
        int best = 0;
        for (int dx = -2; dx <= 2; dx++) {
            for (int dz = -2; dz <= 2; dz++) {
                if (Math.abs(dx) != 2 && Math.abs(dz) != 2) {
                    continue;
                }
                int height = 0;
                BlockPos p = padCenter.offset(dx, 0, dz);
                while (height < 16 && level.getBlockState(p).is(ModBlocks.SERVICE_TOWER.get())) {
                    height++;
                    p = p.above();
                }
                best = Math.max(best, height);
            }
        }
        return best;
    }

    public static int suitBits(Player player) {
        int bits = 0;
        if (player.getItemBySlot(EquipmentSlot.HEAD).is(ModItems.SPACE_HELMET.get())) bits |= SUIT_HELMET;
        if (player.getItemBySlot(EquipmentSlot.CHEST).is(ModItems.SPACE_SUIT.get())) bits |= SUIT_CHEST;
        if (player.getItemBySlot(EquipmentSlot.LEGS).is(ModItems.SPACE_LEGGINGS.get())) bits |= SUIT_LEGS;
        if (player.getItemBySlot(EquipmentSlot.FEET).is(ModItems.SPACE_BOOTS.get())) bits |= SUIT_BOOTS;
        return bits;
    }

    /** Prints the Mission Control style pre-flight checklist into the player's chat. */
    public static void sendChecklist(Player player, Status st) {
        int suit = suitBits(player);
        player.displayClientMessage(Component.translatable("message.retrocosmos.checklist.title")
                .withStyle(ChatFormatting.AQUA, ChatFormatting.BOLD), false);
        player.displayClientMessage(check(st.found(), Component.translatable("message.retrocosmos.checklist.vehicle")), false);
        player.displayClientMessage(check(st.padOk(), Component.translatable("message.retrocosmos.checklist.pad", st.padCount(), PAD_SIZE)), false);
        player.displayClientMessage(check(st.towerOk(), Component.translatable("message.retrocosmos.checklist.tower", st.towerHeight(), ServiceTowerBlock.MIN_HEIGHT)), false);
        player.displayClientMessage(check(st.fuelOk(), Component.translatable("message.retrocosmos.checklist.fuel", st.fuel(), RocketBlock.MAX_FUEL)), false);
        player.displayClientMessage(check(st.oxidizerOk(), Component.translatable("message.retrocosmos.checklist.oxidizer", st.oxidizer(), RocketBlock.MAX_FUEL)), false);
        player.displayClientMessage(check(suit == SUIT_FULL, Component.translatable("message.retrocosmos.checklist.suit")), false);
        if (st.go(suit)) {
            player.displayClientMessage(Component.translatable("message.retrocosmos.checklist.ready").withStyle(ChatFormatting.GREEN), false);
        } else {
            player.displayClientMessage(Component.translatable("message.retrocosmos.checklist.not_ready").withStyle(ChatFormatting.RED), false);
        }
    }

    private static Component check(boolean ok, Component text) {
        return Component.literal(ok ? " [GO] " : " [NO-GO] ")
                .withStyle(ok ? ChatFormatting.GREEN : ChatFormatting.RED)
                .append(text.copy().withStyle(ChatFormatting.WHITE));
    }

    public static void award(ServerPlayer player, String advancement, String criterion) {
        MinecraftServer server = player.level().getServer();
        if (server == null) {
            return;
        }
        AdvancementHolder holder = server.getAdvancements()
                .get(Identifier.fromNamespaceAndPath(RetroCosmos.MODID, advancement));
        if (holder != null) {
            player.getAdvancements().award(holder, criterion);
        }
    }
}
