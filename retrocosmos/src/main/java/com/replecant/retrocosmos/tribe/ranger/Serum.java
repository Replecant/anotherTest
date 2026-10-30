package com.replecant.retrocosmos.tribe.ranger;

import java.util.List;
import net.minecraft.core.Holder;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;

/**
 * Dr. Oinstein's serums, distilled from his notes: a strong effect for a while, and once it wears off a short,
 * nasty side effect. Durations in ticks.
 */
public enum Serum {
    VIGOR("vigor", 0x8CFF5A, 3600, List.of(eff(MobEffects.STRENGTH, 3600, 1), eff(MobEffects.RESISTANCE, 3600, 0)),
            eff(MobEffects.HUNGER, 400, 1)),
    SWIFTNESS("swiftness", 0x5AE6FF, 2400, List.of(eff(MobEffects.SPEED, 2400, 1), eff(MobEffects.JUMP_BOOST, 2400, 1)),
            eff(MobEffects.SLOWNESS, 200, 1)),
    CEREBRAL("cerebral", 0xFF8CC8, 3600, List.of(eff(MobEffects.NIGHT_VISION, 6000, 0), eff(MobEffects.HASTE, 3600, 1)),
            eff(MobEffects.NAUSEA, 200, 0)),
    REGENERATION("regeneration", 0xFF5A6E, 600, List.of(eff(MobEffects.REGENERATION, 600, 1)),
            eff(MobEffects.HUNGER, 300, 0)),
    HIDE("hide", 0xD2A05A, 3600, List.of(eff(MobEffects.FIRE_RESISTANCE, 3600, 0), eff(MobEffects.RESISTANCE, 3600, 0)),
            eff(MobEffects.WEAKNESS, 400, 0));

    public final String id;
    public final int color;
    /** Ticks after the injection when the side effect hits. */
    public final int afterDelay;
    public final List<Effect> effects;
    public final Effect after;

    Serum(String id, int color, int afterDelay, List<Effect> effects, Effect after) {
        this.id = id;
        this.color = color;
        this.afterDelay = afterDelay;
        this.effects = effects;
        this.after = after;
    }

    public String itemName() {
        return "serum_" + id;
    }

    public List<MobEffectInstance> instances() {
        return effects.stream().map(Effect::instance).toList();
    }

    public static Serum byId(String id) {
        for (Serum s : values()) {
            if (s.id.equals(id)) {
                return s;
            }
        }
        return null;
    }

    private static Effect eff(Holder<MobEffect> effect, int ticks, int amplifier) {
        return new Effect(effect, ticks, amplifier);
    }

    public record Effect(Holder<MobEffect> effect, int ticks, int amplifier) {
        public MobEffectInstance instance() {
            return new MobEffectInstance(effect, ticks, amplifier);
        }
    }
}
