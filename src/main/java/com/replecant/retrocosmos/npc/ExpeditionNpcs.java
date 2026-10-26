package com.replecant.retrocosmos.npc;

import com.replecant.retrocosmos.registry.ModEntities;
import com.replecant.retrocosmos.registry.ModItems;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.function.Function;
import java.util.function.UnaryOperator;
import javax.annotation.Nullable;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.item.Item;
import net.minecraft.world.phys.AABB;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.event.BuildCreativeModeTabContentsEvent;
import net.neoforged.neoforge.event.entity.EntityAttributeCreationEvent;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;

/**
 * The human crew of the Earth expedition: Dr. Cooper the archaeologist on Freedom Station, and the guards and
 * scientists of the expedition camp on Venus.
 */
public final class ExpeditionNpcs {
    public static final String COOPER = "cooper";
    public static final String GUARD = "guard";
    public static final String SCIENTIST = "scientist";
    public static final String DECORATOR = "decorator";

    private static final List<DeferredItem<? extends Item>> ITEMS = new ArrayList<>();

    /** A member of the expedition; the role (Cooper, guard, scientist) is synced data, see {@link CrewRole}. */
    public static final DeferredHolder<EntityType<?>, EntityType<ExpeditionMember>> EXPEDITION_MEMBER = ModEntities.ENTITIES.register(
            "expedition_member",
            id -> EntityType.Builder.of(ExpeditionMember::new, MobCategory.MISC)
                    .sized(0.6F, 1.8F)
                    .eyeHeight(1.62F)
                    .clientTrackingRange(10)
                    .noLootTable()
                    .build(ResourceKey.create(Registries.ENTITY_TYPE, id)));

    /** The expedition's scrip: Dr. Cooper pays for relics with it and sells supplies for it. */
    public static final DeferredItem<Item> SPACE_CREDIT = item("space_credit", Item::new, UnaryOperator.identity());

    public static final DeferredItem<CrewSpawnEggItem> COOPER_SPAWN_EGG = item("cooper_spawn_egg",
            p -> new CrewSpawnEggItem(CrewRole.COOPER, p), UnaryOperator.identity());
    public static final DeferredItem<CrewSpawnEggItem> GUARD_SPAWN_EGG = item("guard_spawn_egg",
            p -> new CrewSpawnEggItem(CrewRole.GUARD, p), UnaryOperator.identity());
    public static final DeferredItem<CrewSpawnEggItem> SCIENTIST_SPAWN_EGG = item("scientist_spawn_egg",
            p -> new CrewSpawnEggItem(CrewRole.SCIENTIST, p), UnaryOperator.identity());
    public static final DeferredItem<CrewSpawnEggItem> DECORATOR_SPAWN_EGG = item("decorator_spawn_egg",
            p -> new CrewSpawnEggItem(CrewRole.DECORATOR, p), UnaryOperator.identity());

    private ExpeditionNpcs() {}

    /** Called from the mod constructor before the deferred registers are attached. */
    public static void init(IEventBus modEventBus) {
        modEventBus.addListener(ExpeditionNpcs::createAttributes);
        modEventBus.addListener(ExpeditionNpcs::addToVanillaTabs);
    }

    /**
     * Spawns a persistent crew member standing at {@code pos} (the block they stand in), looking toward {@code yaw}.
     * {@code home} is the post they return to (guards patrol around it, scientists work around it).
     * Does nothing if a crew member of that role already stands at that post (rebuilding a structure twice does not
     * double the crew).
     */
    public static void spawn(ServerLevel level, BlockPos pos, float yaw, String role, BlockPos home) {
        CrewRole crewRole = CrewRole.byKey(role);
        BlockPos post = home != null ? home : pos;
        boolean present = !level.getEntitiesOfClass(ExpeditionMember.class, new AABB(pos).inflate(3.0),
                m -> m.role() == crewRole && post.equals(m.home())).isEmpty();
        if (!present) {
            create(level, pos, yaw, crewRole, post, EntitySpawnReason.STRUCTURE);
        }
    }

    /** Creates and adds a crew member; returns it, or null if it could not be created. */
    @Nullable
    public static ExpeditionMember create(ServerLevel level, BlockPos pos, float yaw, CrewRole role, BlockPos home,
                                          EntitySpawnReason reason) {
        ExpeditionMember member = EXPEDITION_MEMBER.get().create(level, reason);
        if (member == null) {
            return null;
        }
        member.snapTo(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5, yaw, 0.0F);
        member.setYHeadRot(yaw);
        member.setYBodyRot(yaw);
        member.setRole(role);
        member.setHome(home);
        member.finalizeSpawn(level, level.getCurrentDifficultyAt(pos), reason, null);  // also picks a look and a name
        level.addFreshEntity(member);
        return member;
    }

    /** Items for the creative tabs (spawn eggs, credits...), in order. */
    public static List<DeferredItem<? extends Item>> items() {
        return Collections.unmodifiableList(ITEMS);
    }

    private static <I extends Item> DeferredItem<I> item(String name, Function<Item.Properties, I> factory,
                                                        UnaryOperator<Item.Properties> props) {
        DeferredItem<I> item = ModItems.ITEMS.register(name, id -> factory.apply(props.apply(
                new Item.Properties().setId(ResourceKey.create(Registries.ITEM, id)))));
        ITEMS.add(item);
        return item;
    }

    private static void addToVanillaTabs(BuildCreativeModeTabContentsEvent event) {
        if (event.getTabKey() == CreativeModeTabs.SPAWN_EGGS) {
            event.accept(COOPER_SPAWN_EGG.get());
            event.accept(GUARD_SPAWN_EGG.get());
            event.accept(SCIENTIST_SPAWN_EGG.get());
            event.accept(DECORATOR_SPAWN_EGG.get());
        }
    }

    private static void createAttributes(EntityAttributeCreationEvent event) {
        event.put(EXPEDITION_MEMBER.get(), ExpeditionMember.createAttributes().build());
    }
}
