# Vydání nové verze

Release se spouští **jen ručně** a jen z `main`. Push na `main` nic nevydá.

1. Otestuj změnu v Home Assistantu (instalace z `main` ručně).
2. V jednom commitu na `main` nastav stejnou verzi na třech místech:
   - `custom_components/robzone_xclean/manifest.json` → `"version": "X.Y.Z"`
   - `CHANGELOG.md` → nová první sekce `## X.Y.Z - RRRR-MM-DD`
   - `RELEASE_NOTES.md` → nadpis `## Robzone Xclean vX.Y.Z`
3. GitHub → **Actions** → **Release** → **Run workflow** → větev `main`,
   verze `X.Y.Z`, nech **dry_run** zaškrtnutý. Musí být vše zelené.
4. Spusť znovu se stejnou verzí a **dry_run vypnutým** → vznikne tag `vX.Y.Z`,
   release a `robzone_xclean.zip` přesně z otestovaného commitu.

Workflow release zastaví, když verze v těch třech souborech nesedí, když tag
už existuje, když je verze nižší než poslední vydaná, když neprojde HACS nebo
hassfest validace, nebo když ZIP nemá soubory integrace v kořeni.

Lokální kontrola před pushem:

```bash
git fetch --tags
python3 .github/scripts/release.py check X.Y.Z
```
