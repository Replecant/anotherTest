"""Stage 2 (flight + system map): advancements and lang. Art lives in space_art.py."""
import os

from gen_resources import DATA, MOD, write_json


def advancement(name, icon, parent, criterion, frame="task", background=None):
    display = {"icon": {"id": f"{MOD}:{icon}"},
               "title": {"translate": f"advancements.{MOD}.stage2.{name}.title"},
               "description": {"translate": f"advancements.{MOD}.stage2.{name}.description"},
               "frame": frame, "show_toast": True, "announce_to_chat": True, "hidden": False}
    if background:
        display["background"] = background
    adv = {"display": display, "criteria": {criterion: {"trigger": "minecraft:impossible"}}}
    if parent:
        adv["parent"] = f"{MOD}:stage2/{parent}"
    write_json(os.path.join(DATA, "advancement", "stage2", name + ".json"), adv)


def orbit_dimension():
    """The "orbit" dimension where Freedom Station hangs: a void with a black sky, no weather, no mobs."""
    write_json(os.path.join(DATA, "dimension_type", "orbit.json"), {
        "ambient_light": 0.1,
        "attributes": {
            "minecraft:gameplay/bed_rule": {"can_set_spawn": "never", "can_sleep": "never", "explodes": False,
                                            "error_message": {"translate": "message.retrocosmos.station.no_sleep"}},
            "minecraft:gameplay/respawn_anchor_works": False,
            "minecraft:visual/fog_color": "#000000",
            "minecraft:visual/sky_color": "#000000",
            # a starfield all around, a hard white sun and no sunrise glow
            "minecraft:visual/star_brightness": 1.0,
            "minecraft:visual/sun_angle": 40.0,
            "minecraft:visual/moon_angle": 200.0,
            "minecraft:visual/sunrise_sunset_color": "#00000000",
            "minecraft:visual/sky_light_factor": 1.0,
        },
        "coordinate_scale": 1.0,
        "has_ceiling": False,
        "has_fixed_time": True,
        "has_skylight": True,
        "height": 256,
        "infiniburn": "#minecraft:infiniburn_end",
        "logical_height": 256,
        "min_y": 0,
        "monster_spawn_block_light_limit": 0,
        "monster_spawn_light_level": 0,
        "skybox": "overworld",
    })
    write_json(os.path.join(DATA, "worldgen", "biome", "orbit.json"), {
        "attributes": {"minecraft:visual/sky_color": "#000000", "minecraft:visual/fog_color": "#000000"},
        "carvers": [],
        "downfall": 0.0,
        "effects": {"water_color": "#3f76e4"},
        "features": [],
        "has_precipitation": False,
        "spawn_costs": {},
        "spawners": {k: [] for k in ("ambient", "axolotls", "creature", "misc", "monster", "underground_water_creature",
                                     "water_ambient", "water_creature")},
        "temperature": 0.5,
    })
    write_json(os.path.join(DATA, "dimension", "freedom_station.json"), {
        "type": f"{MOD}:orbit",
        "generator": {"type": "minecraft:flat", "settings": {
            "biome": f"{MOD}:orbit", "features": False, "lakes": False,
            "layers": [{"block": "minecraft:air", "height": 1}], "structure_overrides": []}},
    })


def generate():
    orbit_dimension()
    advancement("root", "rocket", None, "liftoff", background="minecraft:gui/advancements/backgrounds/end")
    advancement("orbit", "guidance_computer", "root", "orbit", frame="goal")
    advancement("splashdown", "heat_shield", "orbit", "landed", frame="challenge")
    advancement("freedom_station", "mission_control_console", "orbit", "docked", frame="goal")
    advancement("venus", "rocket", "orbit", "landed", frame="goal")


BODY_EN = {
    "mercury": ("Mercury", ["0.39 AU", "0.38 g", "Day 176 d", "-180..430 C"]),
    "venus": ("Venus", ["0.72 AU", "0.90 g", "Steam jungles", "Dinosaurs!"]),
    "earth": ("Earth", ["1.00 AU", "1.00 g", "Air 21% O2", "Pad LC-1"]),
    "mars": ("Mars", ["1.52 AU", "0.38 g", "Thin CO2", "-60 C"]),
    "jupiter": ("Jupiter", ["5.20 AU", "2.53 g", "Gas giant", "Great Red Spot"]),
    "saturn": ("Saturn", ["9.58 AU", "1.07 g", "Ring system", "Gas giant"]),
    "freedom_station": ("Stn. Freedom", ["Orbit: Earth", "Crew: none", "Docking: open", "Supplies: yes"]),
}
BODY_RU = {
    "mercury": ("Меркурий", ["0,39 а.е.", "0,38 g", "Сутки 176 д", "-180..430 C"]),
    "venus": ("Венера", ["0,72 а.е.", "0,90 g", "Джунгли, пар", "Динозавры!"]),
    "earth": ("Земля", ["1,00 а.е.", "1,00 g", "Воздух 21% O2", "Комплекс №1"]),
    "mars": ("Марс", ["1,52 а.е.", "0,38 g", "Слабый CO2", "-60 C"]),
    "jupiter": ("Юпитер", ["5,20 а.е.", "2,53 g", "Газ. гигант", "Большое пятно"]),
    "saturn": ("Сатурн", ["9,58 а.е.", "1,07 g", "Кольца", "Газ. гигант"]),
    "freedom_station": ("Ст. «Свобода»", ["Орбита Земли", "Экипаж: нет", "Стыковка: да", "Есть припасы"]),
}

EN = {
    "entity.retrocosmos.rocket": "Liberty I",
    "entity.retrocosmos.seat": "Seat",
    "message.retrocosmos.flight.boarded": "You climb into the Liberty I. T-10 and counting... sneak to scrub the launch.",
    "message.retrocosmos.flight.scrubbed": "Launch scrubbed: the crew left the vehicle.",
    "message.retrocosmos.flight.orbit": "Orbit achieved! Mission Control is patching the orbital chart through.",
    "message.retrocosmos.flight.deorbit": "Deorbit burn. Liberty I is coming home.",
    "message.retrocosmos.flight.landed": "Touchdown on Launch Complex 1. Welcome home, astronaut!",
    "message.retrocosmos.flight.strapped_in": "You're strapped in - no getting out until touchdown.",
    "gui.retrocosmos.flight.title": "LIBERTY I - %s",
    "gui.retrocosmos.flight.phase.pad": "ON THE PAD",
    "gui.retrocosmos.flight.phase.ascent": "ASCENT",
    "gui.retrocosmos.flight.phase.orbit": "ORBIT",
    "gui.retrocosmos.flight.phase.descent": "DESCENT",
    "gui.retrocosmos.flight.alt": "ALT %s m",
    "gui.retrocosmos.flight.vel": "VEL %s m/s",
    "gui.retrocosmos.flight.fuel": "FUEL %s%%",
    "gui.retrocosmos.map.title": "SOLAR SYSTEM - ORBITAL CHART",
    "gui.retrocosmos.map.status.home": "HOME - GO",
    "gui.retrocosmos.map.status.locked": "LOCKED",
    "gui.retrocosmos.map.belt": "Asteroid Belt",
    "gui.retrocosmos.map.status.venus": "LANDING - GO",
    "gui.retrocosmos.map.venus_hint": "Breathable air under the clouds. Beware of dinosaurs!",
    "gui.retrocosmos.map.land": "LAND",
    "message.retrocosmos.flight.approach_venus": "Entering the clouds of Venus... hold on, it's going to be bumpy.",
    "message.retrocosmos.flight.landed_venus": "Touchdown on Venus! The expedition camp is yours - fuel in the supply cabinet. Mind the dinosaurs.",
    "command.retrocosmos.tp.venus": "Teleported %s to the Venus expedition camp",
    "command.retrocosmos.tp.no_venus": "Venus is unavailable",
    "advancements.retrocosmos.stage2.venus.title": "The Lost World",
    "advancements.retrocosmos.stage2.venus.description": "Land in the steaming jungles of Venus",
    "itemGroup.retrocosmos.venus": "Retro Cosmos: Venus",
    "command.retrocosmos.tp.station": "Teleported %s to Freedom Station",
    "message.retrocosmos.station.protected": "Station property - hands off the hull!",
    "command.retrocosmos.tp.home": "Teleported %s home to Earth",
    "command.retrocosmos.tp.no_station": "Freedom Station is unavailable",
    "command.retrocosmos.station.rebuilt": "Freedom Station rebuilt from the current design",
    "command.retrocosmos.venus.camp_moved": "Venus expedition camp moved to %s %s %s",
    "command.retrocosmos.venus.no_camp": "No Venus expedition camp has been built yet",
    "gui.retrocosmos.map.status.station": "DOCKING - GO",
    "gui.retrocosmos.map.station_hint": "Uncrewed station. Fuel and oxygen in the supply room.",
    "gui.retrocosmos.map.dock": "DOCK",
    "message.retrocosmos.flight.approach_station": "Transfer burn complete. Approaching Freedom Station...",
    "message.retrocosmos.flight.docked": "Docked at Freedom Station. Nobody home - the supply room is next to the bay.",
    "message.retrocosmos.flight.no_trajectory": "Mission Control: no trajectory to that destination.",
    "message.retrocosmos.station.no_sleep": "Station bunks aren't rated for sleep in zero-g yet",
    "advancements.retrocosmos.stage2.freedom_station.title": "Freedom Station",
    "advancements.retrocosmos.stage2.freedom_station.description": "Dock at the uncrewed orbital station «Freedom»",
    "gui.retrocosmos.map.locked_hint": "Trajectory not computed yet. Coming in the next stages.",
    "gui.retrocosmos.map.home_hint": "Ready for the deorbit burn.",
    "gui.retrocosmos.map.return": "RETURN HOME",
    "advancements.retrocosmos.stage2.root.title": "Retro Cosmos: Flight",
    "advancements.retrocosmos.stage2.root.description": "Lift off aboard the Liberty I",
    "advancements.retrocosmos.stage2.orbit.title": "Friendship in Orbit",
    "advancements.retrocosmos.stage2.orbit.description": "Reach orbit and see the whole Solar System on the chart",
    "advancements.retrocosmos.stage2.splashdown.title": "Welcome Home",
    "advancements.retrocosmos.stage2.splashdown.description": "Return from orbit and touch down on the launch pad",
}
RU = {
    "entity.retrocosmos.rocket": "Либерти-1",
    "entity.retrocosmos.seat": "Сиденье",
    "message.retrocosmos.flight.boarded": "Вы заняли место в «Либерти-1». T-10, отсчёт пошёл... Shift — отменить старт.",
    "message.retrocosmos.flight.scrubbed": "Старт отменён: экипаж покинул корабль.",
    "message.retrocosmos.flight.orbit": "Выход на орбиту! Центр управления передаёт орбитальную карту.",
    "message.retrocosmos.flight.deorbit": "Тормозной импульс. «Либерти-1» возвращается домой.",
    "message.retrocosmos.flight.landed": "Посадка на Стартовом комплексе №1. С возвращением, астронавт!",
    "message.retrocosmos.flight.strapped_in": "Ремни пристёгнуты — выйти можно только после посадки.",
    "gui.retrocosmos.flight.title": "ЛИБЕРТИ-1 - %s",
    "gui.retrocosmos.flight.phase.pad": "НА СТАРТЕ",
    "gui.retrocosmos.flight.phase.ascent": "ВЗЛЁТ",
    "gui.retrocosmos.flight.phase.orbit": "ОРБИТА",
    "gui.retrocosmos.flight.phase.descent": "СПУСК",
    "gui.retrocosmos.flight.alt": "ВЫС %s м",
    "gui.retrocosmos.flight.vel": "СКР %s м/с",
    "gui.retrocosmos.flight.fuel": "ТОПЛ %s%%",
    "gui.retrocosmos.map.title": "СОЛНЕЧНАЯ СИСТЕМА - КАРТА ОРБИТ",
    "gui.retrocosmos.map.status.home": "ДОМ - GO",
    "gui.retrocosmos.map.status.locked": "ЗАКРЫТО",
    "gui.retrocosmos.map.belt": "Пояс астероидов",
    "gui.retrocosmos.map.status.venus": "ПОСАДКА - GO",
    "gui.retrocosmos.map.venus_hint": "Под облаками можно дышать. Осторожно, динозавры!",
    "gui.retrocosmos.map.land": "ПОСАДКА",
    "message.retrocosmos.flight.approach_venus": "Входим в облака Венеры... держитесь, будет трясти.",
    "message.retrocosmos.flight.landed_venus": "Посадка на Венере! Лагерь экспедиции ваш — топливо в шкафу снабжения. Берегитесь динозавров.",
    "command.retrocosmos.tp.venus": "%s телепортирован в лагерь экспедиции на Венере",
    "command.retrocosmos.tp.no_venus": "Венера недоступна",
    "advancements.retrocosmos.stage2.venus.title": "Затерянный мир",
    "advancements.retrocosmos.stage2.venus.description": "Совершите посадку в душных джунглях Венеры",
    "itemGroup.retrocosmos.venus": "Ретрокосмос: Венера",
    "command.retrocosmos.tp.station": "%s телепортирован на станцию «Свобода»",
    "message.retrocosmos.station.protected": "Имущество станции — корпус не разбирать!",
    "command.retrocosmos.tp.home": "%s телепортирован домой на Землю",
    "command.retrocosmos.tp.no_station": "Станция «Свобода» недоступна",
    "command.retrocosmos.station.rebuilt": "Станция «Свобода» перестроена по текущему проекту",
    "command.retrocosmos.venus.camp_moved": "Лагерь экспедиции на Венере перенесён: %s %s %s",
    "command.retrocosmos.venus.no_camp": "Лагерь экспедиции на Венере ещё не построен",
    "gui.retrocosmos.map.status.station": "СТЫКОВКА - GO",
    "gui.retrocosmos.map.station_hint": "Станция без экипажа. Топливо и кислород в кладовой.",
    "gui.retrocosmos.map.dock": "СТЫКОВКА",
    "message.retrocosmos.flight.approach_station": "Импульс перехода выполнен. Подходим к станции «Свобода»...",
    "message.retrocosmos.flight.docked": "Стыковка со станцией «Свобода». На борту никого — кладовая рядом с отсеком.",
    "message.retrocosmos.flight.no_trajectory": "ЦУП: траектории к этой цели нет.",
    "message.retrocosmos.station.no_sleep": "Койки станции пока не рассчитаны на сон в невесомости",
    "advancements.retrocosmos.stage2.freedom_station.title": "Станция «Свобода»",
    "advancements.retrocosmos.stage2.freedom_station.description": "Состыкуйтесь с безлюдной орбитальной станцией «Свобода»",
    "gui.retrocosmos.map.locked_hint": "Траектория ещё не рассчитана. Будет в следующих этапах.",
    "gui.retrocosmos.map.home_hint": "Готовы к тормозному импульсу.",
    "gui.retrocosmos.map.return": "ДОМОЙ",
    "advancements.retrocosmos.stage2.root.title": "Ретрокосмос: Полёт",
    "advancements.retrocosmos.stage2.root.description": "Стартуйте на борту «Либерти-1»",
    "advancements.retrocosmos.stage2.orbit.title": "«Дружба» на орбите",
    "advancements.retrocosmos.stage2.orbit.description": "Выйдите на орбиту и увидьте всю Солнечную систему на карте",
    "advancements.retrocosmos.stage2.splashdown.title": "С возвращением",
    "advancements.retrocosmos.stage2.splashdown.description": "Вернитесь с орбиты и сядьте на стартовую площадку",
}
for body, (name, lines) in BODY_EN.items():
    EN[f"gui.retrocosmos.map.body.{body}"] = name
    for i, line in enumerate(lines):
        EN[f"gui.retrocosmos.map.body.{body}.line{i}"] = line
for body, (name, lines) in BODY_RU.items():
    RU[f"gui.retrocosmos.map.body.{body}"] = name
    for i, line in enumerate(lines):
        RU[f"gui.retrocosmos.map.body.{body}.line{i}"] = line
