# Причуды природы (Nature's Quirks)

Странности обычного мира в ванильном стиле: каменные головы на берегах, цветочные криперы и огромные дикие ульи.

**Minecraft 1.21.11 · NeoForge 21.11.x · Java 21**

## Скачать
Готовый `.jar` — во вкладке [Releases](https://github.com/Replecant/anotherTest/releases) (релизы с тегом
`naturequirks-v…`). Положите jar в папку `mods`.

## Сборка вручную
Из папки `naturequirks/`:
```
./gradlew build          # jar в build/libs/
./gradlew runClient      # запустить игру с модом
```
Текстуры, модели, лут, рецепты, генерация и локализация генерируются скриптом `python3 tools/gen_resources.py`
(нужен Pillow).
