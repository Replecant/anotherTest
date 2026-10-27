package com.replecant.retrocosmos.npc;

import com.replecant.retrocosmos.RetroCosmos;
import java.util.Set;
import javax.annotation.Nullable;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;

/** The kinds of things the crew busy themselves with, and how a block is recognised as one. */
public enum WorkKind {
    /** Radar scopes, computer banks, control panels, gauges: twiddle knobs and punch keys. */
    CONSOLE(ExpeditionMember.ACT_TYPING, 1.0),
    /** Lab sinks, brewing stands, cauldrons: pipettes and test tubes. */
    LAB(ExpeditionMember.ACT_TYPING, 0.9),
    /** Plants, planters, composters: take samples. */
    PLANT(ExpeditionMember.ACT_INSPECT, 0.4),
    /** Telescopes: look through them. */
    SCOPE(ExpeditionMember.ACT_TYPING, 1.3),
    /** Workbenches, lecterns, chart tables: write it all down. */
    DESK(ExpeditionMember.ACT_NOTES, 0.9),
    /** Relics, shelves, urns, stelae: Dr. Cooper dusts and admires them. */
    DISPLAY(ExpeditionMember.ACT_INSPECT, 0.8),
    /** Any other piece of mod furniture: the showroom saleswoman dusts and straightens it. */
    SHOWROOM(ExpeditionMember.ACT_INSPECT, 0.6);

    /** Arm pose while doing it (an ExpeditionMember.ACT_* constant). */
    public final int action;
    /** Height above the block's base to look at. */
    public final double lookHeight;

    WorkKind(int action, double lookHeight) {
        this.action = action;
        this.lookHeight = lookHeight;
    }

    private static final Set<String> CONSOLES = Set.of("radar_scope", "computer_bank", "control_panel", "oxygen_tank_rack",
            "atomic_tv", "tube_radio", "reactor_core", "fuel_refinery", "console");
    private static final Set<String> DESKS = Set.of("retro_workbench", "star_chart", "boomerang_table");
    private static final Set<String> VENUS_PLANTS = Set.of("venus_sedge", "venus_horsetail", "venus_cycad", "venus_fire_lily",
            "venus_tree_fern", "venus_giant_fern", "venus_glowcap", "venus_glowstalk", "venus_hanging_vines");
    private static final Set<String> RELIC_WORDS = Set.of("glyph", "idol", "stele", "urn", "altar", "sun_disc", "relic", "statue",
            "display", "showcase", "vitrine", "space_globe");

    /** What kind of work this block offers, or null. */
    @Nullable
    public static WorkKind of(BlockState state) {
        if (state.isAir()) {
            return null;
        }
        Identifier id = BuiltInRegistries.BLOCK.getKey(state.getBlock());
        String path = id.getPath();
        if (id.getNamespace().equals(RetroCosmos.MODID)) {
            if (CONSOLES.contains(path) || path.endsWith("_console") || path.endsWith("_panel") && path.contains("control")) {
                return CONSOLE;
            }
            if (path.equals("lab_sink") || path.contains("lab_")) {
                return LAB;
            }
            if (path.equals("telescope")) {
                return SCOPE;
            }
            if (DESKS.contains(path)) {
                return DESK;
            }
            if (path.equals("hydroponic_planter") || VENUS_PLANTS.contains(path)) {
                return PLANT;
            }
            for (String word : RELIC_WORDS) {
                if (path.contains(word)) {
                    return DISPLAY;
                }
            }
            return state.getBlock() instanceof com.replecant.retrocosmos.furniture.FurnitureBlock ? SHOWROOM : null;
        }
        if (state.is(Blocks.BREWING_STAND) || state.is(BlockTags.CAULDRONS)) {
            return LAB;
        }
        if (state.is(Blocks.LECTERN) || state.is(Blocks.CARTOGRAPHY_TABLE) || state.is(Blocks.CRAFTING_TABLE)) {
            return DESK;
        }
        if (state.is(Blocks.COMPOSTER) || state.is(BlockTags.FLOWERS) || state.is(BlockTags.SAPLINGS)) {
            return PLANT;
        }
        if (state.is(Blocks.BOOKSHELF) || state.is(Blocks.CHISELED_BOOKSHELF) || state.is(Blocks.DECORATED_POT)
                || state.is(Blocks.SUSPICIOUS_SAND) || state.is(Blocks.SUSPICIOUS_GRAVEL)) {
            return DISPLAY;
        }
        return null;
    }

    /** Whether someone of this role takes an interest in this kind of thing. */
    public boolean interests(CrewRole role) {
        return switch (role) {
            case COOPER -> this == DISPLAY || this == DESK || this == SCOPE;
            case SCIENTIST -> this != DISPLAY && this != SHOWROOM;
            case GUARD -> false;
            case RANGER -> this == DESK || this == CONSOLE || this == SCOPE;
            case LIAISON -> this == DESK || this == PLANT || this == DISPLAY || this == SCOPE;
            case DOCTOR -> this == LAB || this == DESK || this == PLANT;
            case DECORATOR -> this == SHOWROOM || this == CONSOLE || this == DESK || this == DISPLAY || this == PLANT
                    || this == SCOPE;
        };
    }
}
