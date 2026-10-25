package com.replecant.retrocosmos.npc;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.gameevent.GameEvent;

/** Places a member of the expedition (of one role) whose post is where they were placed. */
public class CrewSpawnEggItem extends Item {
    private final CrewRole role;

    public CrewSpawnEggItem(CrewRole role, Properties properties) {
        super(properties);
        this.role = role;
    }

    public CrewRole role() {
        return role;
    }

    @Override
    public InteractionResult useOn(UseOnContext context) {
        Level level = context.getLevel();
        if (!(level instanceof ServerLevel server)) {
            return InteractionResult.SUCCESS;
        }
        BlockPos clicked = context.getClickedPos();
        BlockPos pos = level.getBlockState(clicked).getCollisionShape(level, clicked).isEmpty()
                ? clicked : clicked.relative(context.getClickedFace());
        Player player = context.getPlayer();
        float yaw = player != null ? player.getYRot() + 180.0F : 0.0F;
        ExpeditionMember member = ExpeditionNpcs.create(server, pos, yaw, role, pos, EntitySpawnReason.SPAWN_ITEM_USE);
        if (member != null) {
            context.getItemInHand().consume(1, player);
            level.gameEvent(player, GameEvent.ENTITY_PLACE, pos);
        }
        return InteractionResult.SUCCESS;
    }
}
