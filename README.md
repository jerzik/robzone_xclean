# Robzone Duoro Xclean 5 - Home Assistant Integration

LAN integrace pro robotický vysavač **Robzone Duoro Xclean 5** (a kompatibilní HCTRobot modely) přímo z Home Assistant. Bez cloudového připojení, čistě přes lokální síť.

## Podpora

- **Robzone Duoro Xclean 5** (verze firmwaru 5.0.x)
- Kompatibilní s HCTRobot protokolem (port 8888)

## Funkce

### Vacuum entita
- Start / Pauza / Stop
- Návrat do docku
- Čištění bodu (spot)
- Automatický režim
- Čištění podél zdi (edge/wall)
- Manuální ovládání (vpřed, vlevo, vpravo, vzad)
- Příkaz `send_command` pro pokročilé ovládání

### Senzory
| Senzor | Popis |
|--------|-------|
| Baterie | Stav baterie (%) |
| Stav práce | uklízí / návrat / pauza / start |
| Režim úklidu | auto / spot / podél zdi |
| Výkon ventilátoru | Účinnost sání |
| Chyba | Diagnostika chyb |
| Uklizená plocha | m² z aktuální mapy |
| Čas úklidu | sekundy z aktuální mapy |
| ID aktuálního úklidu | Identifikátor úklidu |
| Mapa RAW Base64 | Diagnostická data mapy |
| Trasa RAW Base64 | Diagnostická data trasy |

## Instalace

### HACS (doporučeno)

1. Otevři **HACS** → **Integrace**
2. Klikni na tři tečky (⋮) → **Custom repositories**
3. Přidej: `https://github.com/jerzik/robzone_xclean`
4. Kategorie: **Integration**
5. Klikni **Add** → počkej → vyber **Robzone Xclean** → **Download**
6. Restartuj Home Assistant

### Manuálně

```bash
cd /config/custom_components
git clone https://github.com/jerzik/robzone_xclean.git
```

nebo zkopíruj složku `custom_components/robzone_xclean` do `/config/custom_components/`.

## Nastavení

1. **Settings** → **Devices & Services** → **+ Add Integration**
2. Vyhledej **Robzone Xclean**
3. Vyplň:
   - **IP adresa** vysavače (např. `192.168.2.69`)
   - **Port** (default: `8888`)
   - **Auth Code** - přístupový kód z mobilní aplikace
   - **Target ID** - ID zařízení z mobilní aplikace

### Získání přihlašovacích údajů

Přihlašovací údaje (`auth_code` a `target_id`) získáš pomocí síťového snímání (např. PCAPdroid na mobilu) během připojení vysavače přes mobilní aplikaci RobZone.

## Příkazy (send_command)

| Příkaz | Popis |
|--------|-------|
| `start` | Spustit úklid |
| `pause` / `stop` | Pauza |
| `dock` / `home` | Návrat do docku |
| `auto` | Automatický režim |
| `auto_start` | Auto + start |
| `edge` / `podel_zdi` | Čištění podél zdi |
| `edge_start` | Edge + start |
| `spot` | Bodový úklid |
| `spot_start` | Spot + start |
| `forward` | Vpřed |
| `left` | Vlevo |
| `right` | Vpravo |
| `back` | Vzad |
| `manual_stop` | Zastavit manuální pohyb |
| `map` / `get_map` | Stáhnout aktuální mapu |
| `keepalive` | Keepalive signál |

## Technické detaily

- Komunikace přes TCP na portu 8888
- Binární protokol s JSON payloadem (zopakovaný z PCAPdroid snímků mobilní aplikace)
- Handshake sekvence pro autentizaci
- Polling každých 15 sekund pro stav a mapu
- Mapa a trasa jsou Base64 zakódované binární payload

## Kompatibilita

- Home Assistant 2024.1+
- Python 3.12+
- Robzone Duoro Xclean 5 (firmware 5.0.x)
- HCTRobot kompatibilní vysavače

## Debugging

Nastav logování v `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.robzone_xclean: debug
```

## Licence

MIT
