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

### Získání přihlašovacích údajů (PCAPdroid)

Integrace potřebuje `auth_code` a `target_id`, které najdeš v síťové komunikaci mobilní aplikace RobZone. Použij PCAPdroid (Android) pro zachycení provozu.

#### Krok 1: Nainstaluj PCAPdroid

- Stáhni [PCAPdroid](https://play.google.com/store/apps/details?id=comemanueh.pcapdroid) z Google Play
- Povol potřebná oprávnění (VPN, nahrávání syrových paketů)

#### Krok 2: Zachyť komunikaci

1. Otevři PCAPdroid
2. Klikni **Start capture** (▶️)
3. Otevři mobilní aplikaci **RobZone**
4. Připoj se k vysavači / pošli příkaz (start, pause, cokoliv)
5. Počkej 5-10 sekund, než aplikace odešle příkaz
6. Vrať se do PCAPdroid a klikni **Stop** (⏹️)

#### Krok 3: Najdi údaje v PCAPdroid

1. V PCAPdroid klikni na záložku **Connections**
2. Vyhledej spojení na **port 8888** (to je komunikace s vysavačem)
3. Klikni na toto spojení → **Follow** → **TCP Stream**
4. Uvidíš JSON data. Hledej tyto hodnoty:

```json
{
  "control": {
    "authCode": "TOTO_JE_AUTH_CODE",
    "targetId": "TOTO_JE_TARGET_ID",
    "targetType": "3",
    "deviceIp": "192.168.x.x",
    "devicePort": "8888"
  },
  "value": { ... }
}
```

5. Zkopíruj:
   - **`authCode`** → zadávej jako **Auth Code** v nastavení integrace
   - **`targetId`** → zadávej jako **Target ID** v nastavení integrace
   - **`deviceIp`** → zadávej jako **IP adresa** v nastavení integrace

#### Alternativa: Wireshark na PC

Pokud máš vysavač připojený přes WiFi, můžeš použít i **Wireshark** na notebooku:
1. Nastav Wireshark na zachytávání WiFi provozu
2. Filtr: `tcp.port == 8888`
3. Pošli příkaz přes mobilní aplikaci
4. Najdi JSON payload v TCP streamu

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

## Mapa a sledování úklidu

Integrace stahuje každých 15 sekund aktuální mapu a trasu vysavače. Data přichází jako Base64 zakódovaný binární payload přes příkaz `map` (transitCmd 131/132).

### Co integration poskytuje:

- **Mapa RAW** — surová data mapy (Base64), lze dekódovat pro zobrazení
- **Trasa RAW** — surová data trasy (Base64), lze dekódovat pro zobrazení
- **Uklizená plocha** — m² z aktuálního úklidu (z mapového payloadu)
- **Čas úklidu** — sekundy z aktuálního úklidu
- **ID aktuálního úklidu** — identifikátor probíhajícího úklidu

### Dekódování mapy

Mapa a trasa jsou binární data zakódovaná v Base64. Pro zobrazení v Home Assistant lze použít:
- Template senzor s `base64_decode` filtrem
- Vlastní karta (custom card) pro zobrazení mapy
- automatizace which z Base64 dat vyextrahuje pozici vysavače

## Technické detaily

- Komunikace přes TCP na portu **8888**
- Binární protokol s JSON payloadem (reverzovaný z PCAPdroid snímků mobilní aplikace)
- Handshake sekvence (20 bajtů) pro autentizaci
- Každý paket obsahuje: velikost (4B) + header tail (16B) + JSON payload
- Polling každých 15 sekund pro stav a mapu
- Podporované commandy: start, pause, dock, auto, edge, spot, manual, map, keepalive
- Pracovní stavy: 1=uklízí, 2=návrat, 5=start, 6=pauza
- Pracovní režimy: 0=auto, 1=spot, 4=podél zdi, 6=auto

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
