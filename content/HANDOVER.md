# Handover – „Weg zum Porsche" / Mini Cooper Content

_Stand: 2026-08-28. Lebendes Dokument – bei Wiederaufnahme zuerst lesen, dann aktualisieren._

## Repo / Ablage

Alles Nicht-Footage-Material lebt im Repo **`wolfcast91/wolfcast91`**, lokal geklont nach
`~/wolfcast91` (auf der internen Platte – nicht auf `/Volumes/holdmydata/`, dort zerlegen
macOS-`._`-Dateien das `.git`).

| Pfad im Repo | Inhalt |
|---|---|
| `cooper-animations/` | Remotion-Projekt (Intro-/Hook-Animationen) |
| `content/HANDOVER.md` | dieses Dokument |
| `content/CATALOG_PROMPT.md` | Katalog-Arbeitsanweisung + Sampling-Policy |
| `content/season-1/ROHKATALOG.md` | gemergter Gesamtkatalog |
| `content/season-1/catalog/` | per-Ordner-Kataloge (`catalog_folder1.md` …) |

Raw-Footage bleibt extern unter `/Volumes/holdmydata/camera/` (in `.gitignore`, nie committen).

## Projekt

Content-Serie: **Autos kaufen → reparieren → verkaufen als Weg zum Traumauto-Kauf.**
Porsche ist das Ziel, wird aber **nicht mehr im Hook genannt** (Hook-Wortlaut: „Ich schenk euch
mein Traumauto!").
Deutschsprachig, vertikal **9:16**, für YouTube / Instagram / TikTok.
Rohe Stimme im Video ist erlaubt (bewusste Entscheidung).

### Fahrzeug

| | |
|---|---|
| Modell | Mini Cooper R56, 1.6, 122 PS |
| Laufleistung | ~195.000 km |
| Bekannter Mangel | Ölverlust riemenseitig |
| TÜV | läuft **04/2027** ab → natürlicher Season-Abschluss |

## Season-Struktur

Gearbeitet wird in **Seasons**, getaktet nach Algorithmus (mehrere Postings/Woche) und
Freizeit-Kapazität – **nicht an Kalenderwochen**, sondern an den Fahrzeug-Zustand gebunden
(eine Season endet z. B. mit TÜV oder Verkauf).

### Season 1 – „Mini Maintenance"

- Ziel: Community aufbauen, erstes Momentum.
- **Workflow: von Footage zu Content-Strategie, nicht umgekehrt.**
  Erst wird geschraubt, wie es ansteht; danach wird aus dem Material geschaut, welcher Content
  drin ist. **Kein vorab geschriebenes Episoden-Gerüst, keine festgelegten Beats/Reihenfolge.**
- Bisherige Episoden-Ideen (Hook/Chaos, Diagnose, Rost, TÜV …) sind **lose Stoff-Kategorien,
  keine Pflicht-Reihenfolge** – auch nicht rückwirkend als fix behandeln.

### Season 2 – „Cooper Tuning + Giveaway" (später)

- Startet, sobald Season 1 Reichweite/Vertrauen aufgebaut hat.
- Hier **umgekehrter Workflow: Strategie → Dreh** (planbar wegen Tuning-Teilen + Giveaway-Mechanik).

## Postings-Rhythmus (Season 1, pragmatisch)

Ein Schrauber-Termin (Wochenende) → Material für mehrere Posts über die Woche:

- **1× Hauptvideo** – die eigentliche Arbeit, geschnitten
- **1× Poll/Frage-Post** – aus einem Cliffhanger des Videos
- **1× roher BTS-/Reaction-Schnipsel**

Dreh-Aufwand bleibt am Wochenend-Termin; Output verteilt sich übers Editing auf die Woche.

## Anonymität (harte Regel, immer)

**Kein Gesicht, kein Kennzeichen, keine Hausnummer/Adresse** in verwendbarem Material.
Rohe Stimme ist ok.

Beim Katalogisieren: alles Betroffene mit **`NEEDS BLUR`** taggen, **inkl. Timestamp**.

## Footage & Katalog

Footage-Quelle: `/Volumes/holdmydata/camera/` – 3 Content-Unterordner (siehe Ordner-Realität).
Katalog-Dateien liegen im Repo unter `content/season-1/`.

### Ist-Stand der Katalog-Dateien (2026-08-28)

| Datei | Status |
|---|---|
| `content/CATALOG_PROMPT.md` | **vorhanden** – aktuelle Vorlage inkl. Sampling-Policy |
| `content/season-1/ROHKATALOG.md` | **vorhanden** – deckt alle **61 eindeutigen Clips** ab (erster Ein-Pass-Durchlauf, 10‑s‑Sampling, noch **ohne** `NEEDS BLUR`+Timestamp-Konvention). |
| `content/season-1/catalog/catalog_folder{1,2,3}.md` | **fehlen** – per-Ordner-Split noch nicht gemacht |

### Ordner-Realität

- `PIXEL/` = Original. Unterordner: `Intro` (31), `Maintenance - Dach` (22),
  `Maintenance - Entrosten` (8, 4K/UHD), `Maintenance - Simmerring` (22).
- `Maintenance - Simmerring` ist **byte-identisch** mit `Maintenance - Dach`.
- `PIXEL Kopie/` = **vollständige Kopie** von `PIXEL/`.
- → **61 eindeutige Clips**, Rest sind Dubletten. Details siehe `ROHKATALOG.md`.
- 4 Clips im `Dach`-Ordner sind fehlabgelegt (Heimkino/Wohnzimmer statt Auto).

### Methode

Frame-Extraktion via `ffmpeg`, Intervall nach Clip-Länge (**Sampling-Policy-Tabelle in
`CATALOG_PROMPT.md`**: 0,5 s bei ≤ 4 s … 6 min bei 12–24 h; Ziel 60–240 Frames/Clip; 2 s
Default bei Clips ≤ 60 s). Metadaten via `ffprobe`. Frames zu Kontaktbögen montieren,
Temp-Frames nach jeder Clip-Beschreibung löschen. Wegen Context-Overflow **Ordner-für-Ordner**
arbeiten und an der letzten fertigen Stelle weitermachen.

## Intro (Remotion, `cooper-animations/`)

Erst-Aufbau via **PR #2** (gemergt 2026-08-28). Details + Render-Befehle: `cooper-animations/README.md`.

- Compositions **`PorscheHook`** / **`PorscheHookDE`** (Name bleibt aus Projektstart):
  schwarz → Headline knallt rein → Hard Cut bei 0,6 s → Subline „Das Problem?" → danach reales
  Footage (außerhalb Remotion). DE-Wortlaut jetzt **„Ich schenk euch mein Traumauto!"** (kein
  Porsche). **EN-Wortlaut noch offen** (`TODO(copy)` in `src/PorscheHook/constants.ts`) – 
  entweder analog „I'm giving you my dream car" oder es erscheint nur der DE-Schnitt.
- Bonus: **`ExpectationReality`** / **`ExpectationRealityDE`** (Zwei-Karten, Hard Cut) für später.
- Bei Textlänge/Overflow: **Schriftgröße anpassen statt Text kürzen** (Größe wandert mit der Copy).
- Export: `npx remotion render <id>` → MP4, wird als Overlay in CapCut/iMovie gelegt.

## Tools

- `ffmpeg` / `ffprobe` – Frame-Extraktion, Videometadaten
- Remotion – Light-Animationen / Intro-Hooks (Repo `wolfcast91/wolfcast91`)
- Schnitt manuell in **CapCut Desktop** oder **iMovie** – nicht Teil von Claude Code,
  nur Zulieferung von Assets/Plänen

## Nächster pragmatischer Schritt

1. Katalogisierung nach `content/CATALOG_PROMPT.md` fortführen: Ordner 1 (Intro) → 
   `content/season-1/catalog/catalog_folder1.md`, zeigen, dann Ordner 2 + 3.
2. `ROHKATALOG.md` auf die Vorlage bringen: `NEEDS BLUR`-Timestamps ergänzen, nach Kategorien
   gruppieren, `NEEDS BLUR`-Checkliste voranstellen.
3. **Danach** aus dem tatsächlichen Material schauen, welche Content-Reihenfolge/Stücke sich
   anbieten. **Keine Strategie vorab erzwingen.**
4. EN-Hook-Wortlaut entscheiden (`TODO(copy)` in `cooper-animations/src/PorscheHook/constants.ts`).
