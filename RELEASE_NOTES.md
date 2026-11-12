## Robzone Xclean v2.2.0

Toto vydání odstraňuje nevyžádané TCP dotazy, které mohly robot probouzet
nebo zatěžovat jeho firmware.

- Integrace už neprovádí automatické minutové načítání mapy.
- Příkazy `map`, `get_map` a `keepalive` byly odstraněny, takže se
  `transitCmd 131` neodešle ani při spuštění starého HA skriptu.
- Start, pauza, dock, výkon sání a ruční pohyb zůstávají zachovány.
- Stav se aktualizuje z odpovědí na skutečné ovládací povely.
- V HA lze použít novou časovanou hadovitou trasu obdélníku X × Y ze středu
  plochy s kalibrací pohybu, roztečí pruhů a nouzovým STOP.

Po instalaci je nutný restart Home Assistantu, aby se načetl nový kód
integrace.
