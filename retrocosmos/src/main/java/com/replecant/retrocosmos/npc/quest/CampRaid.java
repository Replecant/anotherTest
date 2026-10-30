package com.replecant.retrocosmos.npc.quest;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.replecant.retrocosmos.RetroCosmos;
import com.replecant.retrocosmos.dinosaur.robot.ModRobots;
import com.replecant.retrocosmos.npc.CrewRole;
import com.replecant.retrocosmos.npc.ExpeditionMember;
import com.replecant.retrocosmos.npc.ExpeditionNpcs;
import com.replecant.retrocosmos.npc.NpcAnchor;
import com.replecant.retrocosmos.tribe.ModTribes;
import com.replecant.retrocosmos.venus.Venus;
import com.replecant.retrocosmos.venus.VenusLanding;
import java.io.Reader;
import java.util.ArrayList;
import java.util.List;
import javax.annotation.Nullable;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.GlobalPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.Filterable;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.WrittenBookContent;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CampfireBlock;
import net.minecraft.world.level.block.LecternBlock;
import net.minecraft.world.level.block.entity.LecternBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * The raid on the expedition camp and its aftermath: the crew carried off, scorched ground, signal-fire smoke and
 * wrecked crates, Dr. Oinstein's retreating raiders, and Dr. Ross dying by the command tent; then the note he leaves
 * on a lectern; and finally, once the expedition is free, the camp put back to rights with its people home again.
 */
public final class CampRaid {
    /** How close a player at REPORT_TO_CAMP must come for the raid to have happened. */
    public static final double TRIGGER_RANGE = 48.0;
    private static final int SCORCH_RADIUS = 15;
    private static final Identifier ANCHORS = Identifier.fromNamespaceAndPath(RetroCosmos.MODID, "venus_camp/expedition_camp.json");
    private static final int FLAGS = Block.UPDATE_CLIENTS | Block.UPDATE_SUPPRESS_DROPS;

    /** Tests only: a camp somewhere other than Venus (the game test server has no Venus). */
    @Nullable
    public static GlobalPos testCamp;
    /** How many raiders the last raid left behind (for checks). */
    static int lastRaiders;

    private CampRaid() {}

    /** The expedition camp's pad (the rocket's engine block), if a camp has been built. */
    @Nullable
    public static GlobalPos camp(MinecraftServer server) {
        if (testCamp != null) {
            return testCamp;
        }
        ServerLevel venus = server.getLevel(Venus.DIMENSION);
        BlockPos pad = venus == null ? null : VenusLanding.campPad(venus);
        return pad == null ? null : GlobalPos.of(Venus.DIMENSION, pad);
    }

    @Nullable
    public static ServerLevel campLevel(MinecraftServer server) {
        GlobalPos camp = camp(server);
        return camp == null ? null : server.getLevel(camp.dimension());
    }

    public static boolean atCamp(MinecraftServer server, BlockPos pos) {
        GlobalPos camp = camp(server);
        return camp != null && camp.pos().distSqr(pos) < TRIGGER_RANGE * TRIGGER_RANGE;
    }

    // ------------------------------------------------------------------
    // Where things are in the camp
    // ------------------------------------------------------------------

    @Nullable
    static JsonObject anchors(MinecraftServer server) {
        try {
            var resource = server.getResourceManager().getResource(ANCHORS);
            if (resource.isEmpty()) {
                return null;
            }
            try (Reader reader = resource.get().openAsReader()) {
                return JsonParser.parseReader(reader).getAsJsonObject();
            }
        } catch (Exception e) {
            RetroCosmos.LOGGER.warn("Retro Cosmos quest: could not read the camp anchors: {}", e.toString());
            return null;
        }
    }

    private static BlockPos vec(JsonArray a) {
        return new BlockPos(a.get(0).getAsInt(), a.get(1).getAsInt(), a.get(2).getAsInt());
    }

    /** The template's origin, worked back from the pad (VenusLanding stores pad = pad_center + 1 up). */
    @Nullable
    static BlockPos origin(JsonObject anchors, BlockPos pad) {
        if (anchors == null || !anchors.has("pad_center")) {
            return null;
        }
        return pad.below().subtract(vec(anchors.getAsJsonArray("pad_center")));
    }

    /** A named spot from the anchors' "quest_points" (structure-local), or {@code fallback} from the pad. */
    static BlockPos point(ServerLevel level, @Nullable JsonObject anchors, BlockPos pad, String name, BlockPos fallback) {
        BlockPos origin = origin(anchors, pad);
        if (origin != null && anchors.has("quest_points") && anchors.getAsJsonObject("quest_points").has(name)) {
            return origin.offset(vec(anchors.getAsJsonObject("quest_points").getAsJsonArray(name)));
        }
        BlockPos stand = standable(level, pad.offset(fallback), 4);
        return stand != null ? stand : pad.offset(fallback);
    }

    @Nullable
    static BlockPos standable(ServerLevel level, BlockPos around, int dy) {
        for (int ring = 0; ring <= 3; ring++) {
            for (int dx = -ring; dx <= ring; dx++) {
                for (int dz = -ring; dz <= ring; dz++) {
                    if (Math.max(Math.abs(dx), Math.abs(dz)) != ring) {
                        continue;
                    }
                    for (int i = 0; i <= dy * 2; i++) {
                        int off = (i % 2 == 0) ? i / 2 : -(i + 1) / 2;
                        BlockPos p = around.offset(dx, off, dz);
                        if (canStand(level, p)) {
                            return p;
                        }
                    }
                }
            }
        }
        return null;
    }

    static boolean canStand(ServerLevel level, BlockPos feet) {
        BlockPos below = feet.below();
        return level.getBlockState(below).isFaceSturdy(level, below, Direction.UP)
                && level.getBlockState(feet).getCollisionShape(level, feet).isEmpty()
                && level.getBlockState(feet.above()).getCollisionShape(level, feet.above()).isEmpty()
                && level.getFluidState(feet).isEmpty();
    }

    private static BlockPos commandTent(ServerLevel level, @Nullable JsonObject anchors, BlockPos pad) {
        return point(level, anchors, pad, "command_tent", new BlockPos(0, 0, 7));
    }

    // ------------------------------------------------------------------
    // The raid
    // ------------------------------------------------------------------

    /** The first REPORT_TO_CAMP player to come back finds the camp raided (once per world). */
    static void attack(ServerLevel level, BlockPos pad, ServerPlayer witness) {
        QuestWorld world = QuestWorld.get(level.getServer());
        if (world.campAttacked) {
            return;
        }
        RandomSource rng = level.getRandom();
        JsonObject anchors = anchors(level.getServer());
        // the crew is gone: carried off to the prisoner camp
        int taken = 0;
        for (ExpeditionMember m : level.getEntitiesOfClass(ExpeditionMember.class, new AABB(pad).inflate(40.0, 16.0, 40.0),
                m -> !m.isCaptive() && !m.isDying() && !m.role().isMerchant())) {
            m.discard();
            taken++;
        }
        // scorched earth, smoke from smouldering wreckage, smashed crates
        world.scorch.clear();
        List<BlockPos> burnt = new ArrayList<>();
        for (int tries = 0; tries < 120 && burnt.size() < 40; tries++) {
            int dx = rng.nextInt(SCORCH_RADIUS * 2 + 1) - SCORCH_RADIUS;
            int dz = rng.nextInt(SCORCH_RADIUS * 2 + 1) - SCORCH_RADIUS;
            if (Math.abs(dx) <= 2 && Math.abs(dz) <= 2) {
                continue;  // the pad itself
            }
            BlockPos top = level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, pad.offset(dx, 0, dz)).below();
            BlockState state = level.getBlockState(top);
            if (Math.abs(top.getY() - pad.getY()) > 6 || !ground(state) || burnt.contains(top)) {
                continue;
            }
            int roll = rng.nextInt(4);
            BlockState scorch = (roll < 2 ? Blocks.BLACK_CONCRETE : roll == 2 ? Blocks.GRAY_CONCRETE : Blocks.COAL_BLOCK).defaultBlockState();
            change(level, world, top, scorch);
            burnt.add(top);
        }
        int fires = 0, wreck = 0;
        for (BlockPos b : burnt) {
            BlockPos above = b.above();
            if (!level.getBlockState(above).isAir()) {
                continue;
            }
            if (fires < 3 && rng.nextInt(3) == 0) {
                change(level, world, above, Blocks.CAMPFIRE.defaultBlockState().setValue(CampfireBlock.SIGNAL_FIRE, true)
                        .setValue(CampfireBlock.LIT, true));
                fires++;
            } else if (wreck < 5 && rng.nextInt(3) == 0) {
                BlockState debris = rng.nextBoolean() ? Blocks.SPRUCE_SLAB.defaultBlockState() : Blocks.BARREL.defaultBlockState();
                change(level, world, above, debris);
                wreck++;
            }
        }
        // the raiders, already falling back into the jungle away from the witness
        Vec3 away = Vec3.atCenterOf(pad).subtract(witness.position()).multiply(1, 0, 1);
        away = away.lengthSqr() < 1.0 ? new Vec3(1, 0, 0) : away.normalize();
        BlockPos rally = level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                BlockPos.containing(Vec3.atCenterOf(pad).add(away.scale(22))));
        int raiders = 0;
        lastRaiders = 0;
        for (EntityType<?> type : List.<EntityType<?>>of(ModTribes.HOMINID_NOVUS.get(), ModTribes.HOMINID_NOVUS.get(), ModRobots.ATOMIC_SENTRY.get())) {
            BlockPos at = standable(level, rally.offset(rng.nextInt(5) - 2, 0, rng.nextInt(5) - 2), 4);
            if (at != null && type.spawn(level, at, EntitySpawnReason.EVENT) != null) {
                raiders++;
                lastRaiders++;
            }
        }
        // Dr. Ross, wounded, by the command tent
        BlockPos tent = commandTent(level, anchors, pad);
        ExpeditionMember ross = ExpeditionNpcs.create(level, tent, 0.0F, CrewRole.DOCTOR, tent, EntitySpawnReason.EVENT);
        if (ross != null) {
            ross.forceIdentity(0, 0);
            ross.setDying(true);
        }
        world.campAttacked = true;
        world.campRestored = false;
        world.rossGone = false;
        world.attackedAt = level.getGameTime();
        world.setDirty();
        for (ServerPlayer p : level.getPlayers(p -> p.distanceToSqr(Vec3.atCenterOf(pad)) < 96 * 96)) {
            p.displayClientMessage(Component.translatable("chat.retrocosmos.quest.camp_raided").withStyle(ChatFormatting.RED), false);
        }
        level.playSound(null, pad, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 1.5F, 0.6F);
        RetroCosmos.LOGGER.info("Retro Cosmos quest: the expedition camp at {} was raided ({} crew taken, {} scorched, {} raiders, Ross={})",
                pad, taken, burnt.size(), raiders, ross != null);
    }

    private static boolean ground(BlockState state) {
        if (state.is(BlockTags.DIRT) || state.is(BlockTags.SAND) || state.is(BlockTags.PLANKS) || state.is(Blocks.STONE)
                || state.is(Blocks.GRAVEL) || state.is(Blocks.COBBLESTONE) || state.is(Blocks.MUD)) {
            return true;
        }
        Identifier id = BuiltInRegistries.BLOCK.getKey(state.getBlock());
        String path = id.getPath();
        return id.getNamespace().equals(RetroCosmos.MODID) && (path.equals("venus_soil") || path.equals("venus_moss")
                || path.equals("venus_mud") || path.equals("venus_stone") || path.equals("venus_cobblestone") || path.equals("venus_planks"));
    }

    /** Changes a block and remembers what it was, so the camp can be put back. */
    private static void change(ServerLevel level, QuestWorld world, BlockPos pos, BlockState to) {
        world.scorch.add(new QuestWorld.Scorch(pos.immutable(), level.getBlockState(pos)));
        level.setBlock(pos, to, FLAGS);
    }

    /** Dr. Ross has said his piece and passed on: his last words stay behind on a lectern. */
    public static void onDoctorPassed(ServerLevel level, ExpeditionMember ross) {
        QuestWorld world = QuestWorld.get(level.getServer());
        world.rossGone = true;
        BlockPos at = ross.blockPosition();
        GlobalPos camp = camp(level.getServer());
        JsonObject anchors = anchors(level.getServer());
        BlockPos origin = camp == null ? null : origin(anchors, camp.pos());
        if (origin != null && anchors.has("quest_points") && anchors.getAsJsonObject("quest_points").has("lectern")) {
            at = origin.offset(vec(anchors.getAsJsonObject("quest_points").getAsJsonArray("lectern")));
        }
        if (!level.getBlockState(at).canBeReplaced() || !level.getBlockState(at.below()).isFaceSturdy(level, at.below(), Direction.UP)) {
            BlockPos s = standable(level, at, 2);
            at = s != null ? s : at;
        }
        change(level, world, at, Blocks.LECTERN.defaultBlockState().setValue(LecternBlock.HAS_BOOK, true));
        if (level.getBlockEntity(at) instanceof LecternBlockEntity lectern) {
            lectern.setBook(lastWords(world.prisonCamp));
        }
        world.lectern = at.immutable();
        world.setDirty();
        RetroCosmos.LOGGER.info("Retro Cosmos quest: Dr. Ross passed away; his note lies on a lectern at {}", at);
    }

    /** "The last words of Dr. Samuel Ross" - where the expedition was taken. */
    static ItemStack lastWords(@Nullable BlockPos prisonCamp) {
        ItemStack book = new ItemStack(Items.WRITTEN_BOOK);
        Component page1 = Component.translatable("book.retrocosmos.last_words.page1");
        Component page2 = prisonCamp != null
                ? Component.translatable("book.retrocosmos.last_words.page2", QuestDialogues.coords(prisonCamp))
                : Component.translatable("book.retrocosmos.last_words.page2.lost");
        book.set(DataComponents.WRITTEN_BOOK_CONTENT, new WrittenBookContent(
                Filterable.passThrough("Dr. S. Ross"), "Dr. Samuel Ross", 0,
                List.of(Filterable.passThrough(page1), Filterable.passThrough(page2)), true));
        return book;
    }

    // ------------------------------------------------------------------
    // Home again
    // ------------------------------------------------------------------

    /** The expedition is free: tidy the camp, bring its people back, Dr. Vale with them. */
    static void restore(ServerLevel level, BlockPos pad) {
        QuestWorld world = QuestWorld.get(level.getServer());
        List<QuestWorld.Scorch> undo = new ArrayList<>(world.scorch);
        for (int i = undo.size() - 1; i >= 0; i--) {
            QuestWorld.Scorch s = undo.get(i);
            level.removeBlockEntity(s.pos());
            level.setBlock(s.pos(), s.original(), FLAGS);
        }
        world.scorch.clear();
        world.lectern = null;
        level.getEntitiesOfClass(ExpeditionMember.class, new AABB(pad).inflate(48.0), ExpeditionMember::isDying).forEach(m -> m.discard());
        JsonObject anchors = anchors(level.getServer());
        BlockPos origin = origin(anchors, pad);
        if (origin != null) {
            NpcAnchor.spawnAll(level, NpcAnchor.read(anchors, origin));
        }
        ensureLiaison(level, pad);
        boolean vale = !level.getEntitiesOfClass(ExpeditionMember.class, new AABB(pad).inflate(64.0),
                m -> m.role() == CrewRole.DOCTOR && m.variant() == 1 && !m.isCaptive() && !m.isLeaving()).isEmpty();
        if (!vale) {
            BlockPos tent = commandTent(level, anchors, pad);
            ExpeditionMember doc = ExpeditionNpcs.create(level, tent, 0.0F, CrewRole.DOCTOR, tent, EntitySpawnReason.EVENT);
            if (doc != null) {
                doc.forceIdentity(1, 0);
            }
        }
        world.campRestored = true;
        world.setDirty();
        for (ServerPlayer p : level.getPlayers(p -> p.distanceToSqr(Vec3.atCenterOf(pad)) < 96 * 96)) {
            p.displayClientMessage(Component.translatable("chat.retrocosmos.quest.camp_restored").withStyle(ChatFormatting.GREEN), false);
        }
        RetroCosmos.LOGGER.info("Retro Cosmos quest: the expedition is back at its camp ({} blocks tidied)", undo.size());
    }

    /** Dr. Hale belongs in every camp that is not in ruins - including camps built before she joined. */
    static void ensureLiaison(ServerLevel level, BlockPos pad) {
        if (!level.getEntitiesOfClass(ExpeditionMember.class, new AABB(pad).inflate(64.0, 24.0, 64.0),
                m -> m.role() == CrewRole.LIAISON).isEmpty()) {
            return;
        }
        JsonObject anchors = anchors(level.getServer());
        BlockPos origin = origin(anchors, pad);
        if (origin != null && anchors.has("npcs")) {
            for (NpcAnchor anchor : NpcAnchor.read(anchors, origin)) {
                if (anchor.role().equals(ExpeditionNpcs.LIAISON)) {
                    ExpeditionNpcs.spawn(level, anchor.pos(), anchor.yaw(), anchor.role(), anchor.home());
                    return;
                }
            }
        }
        BlockPos at = point(level, anchors, pad, "liaison", new BlockPos(-6, 0, 5));
        ExpeditionNpcs.spawn(level, at, 180.0F, ExpeditionNpcs.LIAISON, at);
    }
}
