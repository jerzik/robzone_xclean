## Robzone Xclean v2.1.1

Opravné vydání pro instalaci přes HACS.

- ZIP nyní obsahuje soubory integrace přímo v kořeni archivu.
- Opravuje vnořenou cestu vytvořenou chybným archivem v2.1.0.
- Zachovává ovládání sání včetně MAX/ECO, ruční jízdu dozadu,
  stabilizovanou LAN komunikaci a watchdog relé docku.
- Watchdog má editovatelnou délku odpojení, potvrzení výpadku,
  okno 08:00–20:00, ranní odklad a ruční tlačítko.

Package watchdogu a karta zůstávají v repozitáři v adresářích
`packages/` a `dashboards/`; HACS instaluje pouze vlastní integraci.
