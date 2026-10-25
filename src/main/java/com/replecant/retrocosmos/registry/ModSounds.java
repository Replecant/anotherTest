package com.replecant.retrocosmos.registry;

import com.replecant.retrocosmos.RetroCosmos;
import net.minecraft.core.registries.Registries;
import net.minecraft.sounds.SoundEvent;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

/** The mod's own sounds (assets/retrocosmos/sounds.json). */
public final class ModSounds {
    public static final DeferredRegister<SoundEvent> SOUNDS = DeferredRegister.create(Registries.SOUND_EVENT, RetroCosmos.MODID);

    /** A retro ray-gun shot: blasters, Sapiens and sentries. */
    public static final DeferredHolder<SoundEvent, SoundEvent> BLASTER_SHOT = SOUNDS.register("blaster_shot",
            SoundEvent::createVariableRangeEvent);

    private ModSounds() {}
}
