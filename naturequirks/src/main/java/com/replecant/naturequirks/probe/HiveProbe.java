package com.replecant.naturequirks.probe;

import com.mojang.datafixers.util.Pair;
import com.replecant.naturequirks.NatureQuirks;
import com.replecant.naturequirks.hive.HiveEvents;
import com.replecant.naturequirks.hive.HiveHeartBlockEntity;
import com.replecant.naturequirks.hive.ModHive;
import java.util.Map;
import java.util.TreeMap;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderSet;
import net.minecraft.core.SectionPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.animal.bee.Bee;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BeehiveBlockEntity;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.RandomizableContainerBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructureStart;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.common.util.FakePlayerFactory;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/** PROBE ONLY (never committed): giant hive worldgen audit and the honey / cake / alarm tests. */
@EventBusSubscriber(modid = NatureQuirks.MODID)
public final class HiveProbe {
    private HiveProbe() {}

    @SubscribeEvent
    public static void onStarted(ServerStartedEvent event) {
        if (System.getenv("NQ_PROBE") == null) {
            return;
        }
        MinecraftServer server = event.getServer();
        ServerLevel level = server.overworld();
        BlockPos firstHeart = null;
        for (int[] o : new int[][] {{0, 0}, {2500, 0}, {0, 2500}, {-2500, -2500}}) {
            try {
                BlockPos h = hive(level, o);
                if (firstHeart == null) {
                    firstHeart = h;
                }
            } catch (Throwable t) {
                NatureQuirks.LOGGER.error("HIVE PROBE FAIL", t);
            }
        }
        heart = firstHeart;
        ticks = 0;
    }

    private static BlockPos heart;
    private static int ticks = -1;

    /** The tests run once the level has ticked (block entities of fresh chunks are only loaded on a tick). */
    @SubscribeEvent
    public static void onTick(net.neoforged.neoforge.event.tick.ServerTickEvent.Post event) {
        if (ticks < 0 || ++ticks != 40) {
            return;
        }
        ServerLevel level = event.getServer().overworld();
        try {
            tests(level, heart);
        } catch (Throwable t) {
            NatureQuirks.LOGGER.error("HIVE PROBE TESTS FAIL", t);
        }
        NatureQuirks.LOGGER.info("HIVE PROBE DONE");
        event.getServer().halt(false);
    }

    private static BlockPos hive(ServerLevel level, int[] origin) {
        Holder<Structure> holder = level.registryAccess().lookupOrThrow(Registries.STRUCTURE).getOrThrow(
                ResourceKey.create(Registries.STRUCTURE, Identifier.fromNamespaceAndPath(NatureQuirks.MODID, "giant_hive")));
        Pair<BlockPos, Holder<Structure>> found = level.getChunkSource().getGenerator().findNearestMapStructure(level,
                HolderSet.direct(holder), new BlockPos(origin[0], 64, origin[1]), 100, false);
        if (found == null) {
            NatureQuirks.LOGGER.info("HIVE AUDIT none near {},{}", origin[0], origin[1]);
            return null;
        }
        BlockPos pos = found.getFirst();
        StructureStart start = level.structureManager().getStartForStructure(SectionPos.of(pos), holder.value(), level.getChunk(pos));
        if (start == null || !start.isValid()) {
            NatureQuirks.LOGGER.info("HIVE AUDIT at {} no valid start", pos);
            return null;
        }
        BoundingBox box = start.getPieces().get(0).getBoundingBox();
        for (int x = (box.minX() >> 4) - 1; x <= (box.maxX() >> 4) + 1; x++) {
            for (int z = (box.minZ() >> 4) - 1; z <= (box.maxZ() >> 4) + 1; z++) {
                level.getChunk(x, z);
                level.setChunkForced(x, z, true);
            }
        }
        int columns = 0, wet = 0, honey = 0, honeyFlow = 0, nests = 0, nestBees = 0, chests = 0, comb = 0;
        BlockPos heart = null;
        Map<String, Integer> lootTables = new TreeMap<>();
        BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
        for (int x = box.minX(); x <= box.maxX(); x++) {
            for (int z = box.minZ(); z <= box.maxZ(); z++) {
                columns++;
                int top = level.getHeight(Heightmap.Types.WORLD_SURFACE, x, z);
                if (level.getFluidState(p.set(x, top - 1, z)).is(net.minecraft.tags.FluidTags.WATER)) {
                    wet++;
                }
                for (int y = box.minY(); y <= box.maxY(); y++) {
                    BlockState s = level.getBlockState(p.set(x, y, z));
                    if (s.getFluidState().is(ModHive.HONEY.get())) {
                        honey++;
                    } else if (s.getFluidState().is(ModHive.FLOWING_HONEY.get())) {
                        honeyFlow++;
                    }
                    if (s.is(ModHive.HIVE_HEART.get())) {
                        heart = p.immutable();
                    }
                    if (s.is(ModHive.WILD_COMB.get()) || s.is(ModHive.DRIPPING_COMB.get())) {
                        comb++;
                    }
                    BlockEntity be = level.getBlockEntity(p);
                    if (be instanceof BeehiveBlockEntity hive) {
                        nests++;
                        nestBees += hive.getOccupantCount();
                    } else if (be instanceof RandomizableContainerBlockEntity rc && rc.getLootTable() != null) {
                        chests++;
                        lootTables.merge(rc.getLootTable().identifier().getPath(), 1, Integer::sum);
                    }
                }
            }
        }
        int bees = level.getEntitiesOfClass(Bee.class, AABB.of(box).inflate(16)).size();
        int under = 0;   // the ground under the start piece's footprint: water right below the hive?
        NatureQuirks.LOGGER.info("HIVE AUDIT {} at {} box={} piece={} rot={}: surface water {}/{}, comb {}, honey sources {} flowing {}, "
                        + "heart {} (be {}), nests {} with {} bees, bees flying {}, chests {} {}", start.getPieces().get(0).toString()
                        .replaceAll(".*location=([^,\\]]+).*", "$1"), pos, box, start.getPieces().size(), start.getPieces().get(0).getRotation(),
                wet, columns, comb, honey, honeyFlow, heart, heart == null ? "-" : level.getBlockEntity(heart), nests, nestBees, bees, chests,
                lootTables);
        return heart;
    }

    private static void tests(ServerLevel level, BlockPos heart) {
        FakePlayer fake = FakePlayerFactory.getMinecraft(level);
        // 1. the alarm: break comb next to the heart in survival
        if (heart != null) {
            BlockPos comb = null;
            for (BlockPos q : BlockPos.betweenClosed(heart.offset(-4, -3, -4), heart.offset(4, 3, 4))) {
                if (level.getBlockState(q).is(HiveEvents.HIVE_MATERIAL)) {
                    comb = q.immutable();
                    break;
                }
            }
            int before = HiveHeartBlockEntity.alarms, spawnedBefore = HiveHeartBlockEntity.spawned;
            boolean broken = comb != null && fake.gameMode.destroyBlock(comb);
            var guardian = BuiltInRegistries.ENTITY_TYPE.getOptional(HiveHeartBlockEntity.GUARDIAN);
            NatureQuirks.LOGGER.info("HIVE TEST alarm: broke {} at {} -> alarms {} -> {}, guardians spawned {} (type registered: {}), "
                            + "hearts near: {}", comb == null ? "-" : "comb", comb, before, HiveHeartBlockEntity.alarms,
                    HiveHeartBlockEntity.spawned - spawnedBefore, guardian.isPresent(), HiveHeartBlockEntity.heartsNear(level, heart, 16));
            // the cap: hammer it (cooldown aside) and count
            for (int i = 0; i < 6; i++) {
                level.getBlockEntity(heart, ModHive.HIVE_HEART_BE.get()).ifPresent(be -> be.summon(level, fake));
            }
            NatureQuirks.LOGGER.info("HIVE TEST cooldown: 6 more calls in the same tick -> spawned total {}", HiveHeartBlockEntity.spawned);
        }
        // 2. honey: a source; a bottle fills with honey; four bottles + bucket recipes are data
        BlockPos base = new BlockPos(8, 200, 8);
        level.setBlock(base.below(), Blocks.GLASS.defaultBlockState(), 3);
        level.setBlock(base, ModHive.HONEY_BLOCK.get().defaultBlockState(), 3);
        boolean isSource = level.getFluidState(base).isSource() && level.getFluidState(base).is(ModHive.HONEY.get());
        ItemStack bottle = new ItemStack(Items.GLASS_BOTTLE, 4);
        fake.setItemInHand(InteractionHand.MAIN_HAND, bottle);
        int honeyBottles = 0;
        for (int i = 0; i < 4 && level.getFluidState(base).isSource(); i++) {
            if (HiveEvents.bottle(level, base, fake, InteractionHand.MAIN_HAND, fake.getMainHandItem())) {
                honeyBottles = fake.getInventory().countItem(Items.HONEY_BOTTLE) + (fake.getMainHandItem().is(Items.HONEY_BOTTLE) ? 1 : 0);
            }
        }
        NatureQuirks.LOGGER.info("HIVE TEST bottle: honey source placed {} -> honey bottles {} (hand {}), source left {}", isSource,
                honeyBottles, fake.getMainHandItem(), level.getFluidState(base).isSource());
        // 3. the bucket picks honey up
        level.setBlock(base, ModHive.HONEY_BLOCK.get().defaultBlockState(), 3);
        ItemStack picked = ((net.minecraft.world.level.block.LiquidBlock) ModHive.HONEY_BLOCK.get()).pickupBlock(fake, level, base,
                level.getBlockState(base));
        NatureQuirks.LOGGER.info("HIVE TEST bucket pickup: {}", picked);
        // 4. the cake: seven slices
        BlockPos cake = base.east(3);
        level.setBlock(cake.below(), Blocks.STONE.defaultBlockState(), 3);
        level.setBlock(cake, ModHive.HONEY_CAKE.get().defaultBlockState(), 3);
        int eaten = 0;
        for (int i = 0; i < 10 && level.getBlockState(cake).is(ModHive.HONEY_CAKE.get()); i++) {
            fake.getFoodData().setFoodLevel(0);
            BlockState st = level.getBlockState(cake);
            var r = st.useWithoutItem(level, fake, new BlockHitResult(Vec3.atCenterOf(cake), net.minecraft.core.Direction.UP, cake, false));
            if (r.consumesAction()) {
                eaten++;
            }
        }
        NatureQuirks.LOGGER.info("HIVE TEST cake: slices eaten {} block now {}, food {} regen {}", eaten,
                BuiltInRegistries.BLOCK.getKey(level.getBlockState(cake).getBlock()), fake.getFoodData().getFoodLevel(),
                fake.hasEffect(net.minecraft.world.effect.MobEffects.REGENERATION));
        // 5. honey slows a wader (motion after a step in honey vs in air)
        Entity zombie = net.minecraft.world.entity.EntityType.ZOMBIE.create(level, net.minecraft.world.entity.EntitySpawnReason.COMMAND);
        NatureQuirks.LOGGER.info("HIVE TEST fluid type: {} motionScale-ish canSwim {} canDrown {}", ModHive.HONEY_TYPE.get(),
                zombie != null && ModHive.HONEY_TYPE.get().canSwim(zombie), zombie != null && ModHive.HONEY_TYPE.get().canDrownIn((net.minecraft.world.entity.LivingEntity) zombie));
    }
}
