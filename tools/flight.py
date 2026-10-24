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


def generate():
    advancement("root", "rocket", None, "liftoff", background="minecraft:gui/advancements/backgrounds/end")
    advancement("orbit", "guidance_computer", "root", "orbit", frame="goal")
    advancement("splashdown", "heat_shield", "orbit", "landed", frame="challenge")


BODY_EN = {
    "mercury": ("Mercury", ["0.39 AU", "0.38 g", "Day 176 d", "-180..430 C"]),
    "venus": ("Venus", ["0.72 AU", "0.90 g", "Acid clouds", "+460 C"]),
    "earth": ("Earth", ["1.00 AU", "1.00 g", "Air 21% O2", "Pad LC-1"]),
    "mars": ("Mars", ["1.52 AU", "0.38 g", "Thin CO2", "-60 C"]),
    "jupiter": ("Jupiter", ["5.20 AU", "2.53 g", "Gas giant", "79 moons"]),
    "saturn": ("Saturn", ["9.58 AU", "1.07 g", "Rings", "Gas giant"]),
}
BODY_RU = {
    "mercury": ("Меркурий", ["0,39 а.е.", "0,38 g", "Сутки 176 д", "-180..430 C"]),
    "venus": ("Венера", ["0,72 а.е.", "0,90 g", "Кислот. тучи", "+460 C"]),
    "earth": ("Земля", ["1,00 а.е.", "1,00 g", "Воздух 21% O2", "Комплекс №1"]),
    "mars": ("Марс", ["1,52 а.е.", "0,38 g", "Слабый CO2", "-60 C"]),
    "jupiter": ("Юпитер", ["5,20 а.е.", "2,53 g", "Газ. гигант", "79 лун"]),
    "saturn": ("Сатурн", ["9,58 а.е.", "1,07 g", "Кольца", "Газ. гигант"]),
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
    "gui.retrocosmos.map.locked_hint": "Trajectory not computed yet. Coming in the next stages.",
    "gui.retrocosmos.map.home_hint": "Ready for the deorbit burn.",
    "gui.retrocosmos.map.return": "RETURN HOME",
    "advancements.retrocosmos.stage2.root.title": "Retro Cosmos: Flight",
    "advancements.retrocosmos.stage2.root.description": "Lift off aboard the Liberty I",
    "advancements.retrocosmos.stage2.orbit.title": "Friendship in Orbit",
    "advancements.retrocosmos.stage2.orbit.description": "Reach orbit and see the whole solar system on the chart",
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
    "gui.retrocosmos.map.locked_hint": "Траектория ещё не рассчитана. Будет в следующих этапах.",
    "gui.retrocosmos.map.home_hint": "Готовы к тормозному импульсу.",
    "gui.retrocosmos.map.return": "НА ЗЕМЛЮ",
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
