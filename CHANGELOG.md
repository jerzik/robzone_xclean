# Changelog

## 2.1.1 - 2026-11-07

- Opravena struktura HACS release archivu: soubory integrace jsou nyní přímo
  v kořeni ZIPu, takže HACS nevytváří vnořenou složku `custom_components`.
- Funkce a automatizace z verze 2.1.0 zůstávají beze změny.

## 2.1.0 - 2026-11-07

- Přidáno ovládání výkonu sání: vypnuto, normální, MAX/turbo a ECO.
- Opraven ruční pohyb dozadu (`direction=2`).
- Opraveno zpracování více odpovědí v jednom TCP spojení.
- Přidáno sériové řazení příkazů, bezpečné opakování připojení a prodleva mezi relacemi.
- Polling mapy snížen z 15 na 60 sekund, aby se nezatěžoval firmware robota.
- Odfiltrovány nulové inicializační statusy.
- Opraveny stavy: dock/nabíjení, návrat, připraven a pauza.
- Přidán volitelný HA package pro Tasmota/ESP relé docku.
- Přidána editovatelná délka odpojení, potvrzení výpadku a časové okno 08:00–20:00.
- Výpadek v nočním okně se automaticky řeší až v 08:00; ruční tlačítko omezení obchází.

