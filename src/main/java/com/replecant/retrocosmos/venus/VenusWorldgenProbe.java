package com.replecant.retrocosmos.venus;

import com.replecant.retrocosmos.RetroCosmos;
import java.io.ByteArrayOutputStream;
import java.util.ArrayList;
import java.util.Base64;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.zip.GZIPOutputStream;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.QuartPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.Property;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.RandomState;
import net.minecraft.world.phys.AABB;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

/** PROBE ONLY (never committed): generates Venus chunks on a dedicated server and dumps them to the log. */
@EventBusSubscriber(modid = RetroCosmos.MODID)
public final class VenusWorldgenProbe {
    private VenusWorldgenProbe() {}

    @SubscribeEvent
    public static void onStarted(ServerStartedEvent event) {
        MinecraftServer server = event.getServer();
        RetroCosmos.LOGGER.info("VENUS PROBE levels={}", server.levelKeys());
        ServerLevel venus = server.getLevel(Venus.DIMENSION);
        if (venus == null) {
            return;
        }
        try {
            run(venus);
        } catch (Throwable t) {
            RetroCosmos.LOGGER.error("VENUS PROBE FAIL", t);
        }
        server.halt(false);
    }

    private static String biomeName(Holder<Biome> b) {
        String s = b.getRegisteredName(); return s.substring(s.indexOf(':') + 1);
    }

    private static void run(ServerLevel venus) throws Exception {
        ChunkGenerator gen = venus.getChunkSource().getGenerator();
        RandomState rs = venus.getChunkSource().randomState();
        int n = 64, step = 96;
        Map<String, Character> letters = new LinkedHashMap<>();
        Map<String, int[]> nearest = new HashMap<>();
        Map<String, Integer> counts = new TreeMap<>();
        Map<String, long[]> heights = new HashMap<>();
        List<long[]> climate = new ArrayList<>();
        for (int j = 0; j < n; j++) {
            StringBuilder row = new StringBuilder();
            for (int i = 0; i < n; i++) {
                int x = (i - n / 2) * step, z = (j - n / 2) * step;
                int h = gen.getBaseHeight(x, z, Heightmap.Types.WORLD_SURFACE_WG, venus, rs);
                Holder<Biome> b = gen.getBiomeSource().getNoiseBiome(QuartPos.fromBlock(x), QuartPos.fromBlock(h - 1),
                        QuartPos.fromBlock(z), rs.sampler());
                String name = biomeName(b);
                var tp = rs.sampler().sample(QuartPos.fromBlock(x), QuartPos.fromBlock(h - 1), QuartPos.fromBlock(z));
                climate.add(new long[] {tp.temperature(), tp.humidity(), tp.continentalness(), tp.erosion(), tp.weirdness()});
                char c = letters.computeIfAbsent(name, k -> (char) ('A' + letters.size()));
                row.append(c);
                counts.merge(name, 1, Integer::sum);
                long[] hs = heights.computeIfAbsent(name, k -> new long[] {0, 0, 9999, -9999});
                hs[0] += h; hs[1]++; hs[2] = Math.min(hs[2], h); hs[3] = Math.max(hs[3], h);
                long d = (long) x * x + (long) z * z;
                int[] best = nearest.get(name);
                if (best == null || d < (long) best[0] * best[0] + (long) best[1] * best[1]) {
                    // prefer a spot deep inside the biome: require the 4 neighbours (64 blocks away) to match too
                    boolean inside = true;
                    for (int[] o : new int[][] {{64, 0}, {-64, 0}, {0, 64}, {0, -64}}) {
                        int hh = gen.getBaseHeight(x + o[0], z + o[1], Heightmap.Types.WORLD_SURFACE_WG, venus, rs);
                        String nb = biomeName(gen.getBiomeSource().getNoiseBiome(QuartPos.fromBlock(x + o[0]),
                                QuartPos.fromBlock(hh - 1), QuartPos.fromBlock(z + o[1]), rs.sampler()));
                        inside &= nb.equals(name);
                    }
                    if (inside || best == null) {
                        nearest.put(name, new int[] {x, z, inside ? 1 : 0});
                    }
                }
            }
            RetroCosmos.LOGGER.info("VENUS MAP|{}", row);
        }
        RetroCosmos.LOGGER.info("VENUS LEGEND {}", letters);
        String[] axes = {"temperature", "humidity", "continentalness", "erosion", "weirdness"};
        for (int a = 0; a < 5; a++) {
            final int ax = a;
            List<Long> vals = new ArrayList<>();
            climate.forEach(v -> vals.add(v[ax]));
            java.util.Collections.sort(vals);
            StringBuilder dec = new StringBuilder();
            for (int d = 0; d <= 10; d++) {
                dec.append(vals.get(Math.min(vals.size() - 1, d * vals.size() / 10)) / 10000.0).append(' ');
            }
            RetroCosmos.LOGGER.info("VENUS CLIMATE {} deciles {}", axes[a], dec);
        }
        for (var e : counts.entrySet()) {
            long[] hs = heights.get(e.getKey());
            RetroCosmos.LOGGER.info("VENUS BIOME {} cells={} avgY={} minY={} maxY={} sample={}", e.getKey(), e.getValue(),
                    hs[0] / Math.max(1, hs[1]), hs[2], hs[3], java.util.Arrays.toString(nearest.get(e.getKey())));
        }
        for (var e : nearest.entrySet()) {
            dumpRegion(venus, e.getKey(), e.getValue()[0], e.getValue()[1], 48);
        }
        for (String b : new String[] {"venus_jungle", "venus_cycad_plains", "venus_volcanic_highlands", "venus_steaming_sea"}) {
            int[] at = nearest.get(b);
            if (at != null) {
                countOres(venus, b, at[0] >> 4, at[1] >> 4, 6);
            }
        }
        countOres(venus.getServer().overworld(), "OVERWORLD", 0, 0, 6);
    }

    private static void countOres(ServerLevel level, String label, int ccx, int ccz, int n) {
        Map<String, Integer> counts = new TreeMap<>();
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        for (int cx = ccx - n / 2; cx < ccx + n / 2; cx++) {
            for (int cz = ccz - n / 2; cz < ccz + n / 2; cz++) {
                var chunk = level.getChunk(cx, cz);
                for (int x = 0; x < 16; x++) {
                    for (int z = 0; z < 16; z++) {
                        for (int y = level.getMinY(); y < level.getMaxY(); y++) {
                            BlockState s = chunk.getBlockState(pos.set((cx << 4) + x, y, (cz << 4) + z));
                            String id = BuiltInRegistries.BLOCK.getKey(s.getBlock()).getPath();
                            if (id.endsWith("_ore") || id.endsWith("oil_shale") || id.equals("venus_tar")
                                    || id.equals("venus_sand")) {
                                counts.merge(id.replace("deepslate_", ""), 1, Integer::sum);
                            }
                        }
                    }
                }
            }
        }
        RetroCosmos.LOGGER.info("VENUS ORES {} chunks={} {}", label, n * n, counts);
    }

    private static String stateKey(BlockState s) {
        StringBuilder sb = new StringBuilder(BuiltInRegistries.BLOCK.getKey(s.getBlock()).toString());
        for (Property<?> p : s.getProperties()) {
            String name = p.getName();
            if (name.equals("half") || name.equals("tip") || name.equals("axis") || name.equals("type")) {
                sb.append(',').append(name).append('=').append(s.getValue(p).toString().toLowerCase());
            }
        }
        return sb.toString();
    }

    private static void dumpRegion(ServerLevel level, String biome, int cx, int cz, int size) throws Exception {
        long t0 = System.currentTimeMillis();
        int x0 = cx - size / 2, z0 = cz - size / 2;
        for (int x = x0 >> 4; x <= (x0 + size - 1) >> 4; x++) {
            for (int z = z0 >> 4; z <= (z0 + size - 1) >> 4; z++) {
                level.getChunk(x, z);
            }
        }
        long t1 = System.currentTimeMillis();
        Map<String, Integer> palette = new LinkedHashMap<>();
        Map<String, Integer> stats = new TreeMap<>();
        StringBuilder sb = new StringBuilder();
        List<Integer> floors = new ArrayList<>();
        for (int x = x0; x < x0 + size; x++) {
            for (int z = z0; z < z0 + size; z++) {
                floors.add(level.getHeight(Heightmap.Types.OCEAN_FLOOR, x, z));
            }
        }
        java.util.Collections.sort(floors);
        int yBase = floors.get(floors.size() / 10) - 8;
        sb.append(x0).append(' ').append(z0).append(' ').append(size).append(' ').append(yBase).append('\n');
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        for (int x = x0; x < x0 + size; x++) {
            for (int z = z0; z < z0 + size; z++) {
                int top = level.getHeight(Heightmap.Types.WORLD_SURFACE, x, z);
                List<String> col = new ArrayList<>();
                for (int y = yBase; y < top; y++) {
                    BlockState s = level.getBlockState(pos.set(x, y, z));
                    String key = stateKey(s);
                    int id = palette.computeIfAbsent(key, k -> palette.size());
                    col.add(Integer.toString(id, 36));
                    if (!s.isAir()) {
                        stats.merge(BuiltInRegistries.BLOCK.getKey(s.getBlock()).getPath(), 1, Integer::sum);
                    }
                }
                sb.append(String.join(".", col)).append('\n');
            }
        }
        Map<String, Integer> mobs = new TreeMap<>();
        for (Entity e : level.getEntities((Entity) null, new AABB(x0, -64, z0, x0 + size, 320, z0 + size), e -> true)) {
            mobs.merge(BuiltInRegistries.ENTITY_TYPE.getKey(e.getType()).toString(), 1, Integer::sum);
        }
        StringBuilder pal = new StringBuilder();
        palette.keySet().forEach(k -> pal.append(k).append(';'));
        String payload = pal + "\n" + sb;
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        try (GZIPOutputStream gz = new GZIPOutputStream(bos)) {
            gz.write(payload.getBytes(java.nio.charset.StandardCharsets.UTF_8));
        }
        RetroCosmos.LOGGER.info("VENUS REGION {} at {},{} gen={}ms blocks={} mobs={}", biome, cx, cz, t1 - t0, stats, mobs);
        RetroCosmos.LOGGER.info("VENUS DATA {}|{}", biome, Base64.getEncoder().encodeToString(bos.toByteArray()));
    }
}
