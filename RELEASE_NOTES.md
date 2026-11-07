## Robzone Xclean v2.1.0

Tato verze přidává skutečné ovládání výkonu sání včetně MAX, opravuje ruční jízdu dozadu a stabilizuje LAN komunikaci s robotem.

Nově je součástí repozitáře volitelný Home Assistant package pro Tasmota/ESP relé napájení docku:

- výchozí odpojení na 2 minuty, editovatelné v HA,
- editovatelná doba potvrzení výpadku,
- automatické restarty jen mezi 08:00 a 20:00,
- noční výpadek se odloží na 08:00,
- ruční tlačítko provede restart kdykoliv,
- relé se po cyklu vrátí do původního stavu, takže funguje s NO i NC zapojením.

Před použitím package zkontrolujte tři entity uvedené v jeho hlavičce.

