# Katalog-Vorlage – Footage-Katalogisierung (Season 1, Footage-first)

_Aktuelle Arbeitsanweisung für die Katalogisierung. Bei Wiederaufnahme diese Vorlage nutzen._

## Kontext

Raw footage für die Car-Restoration-Serie liegt in `/Volumes/holdmydata/camera/` in 3 Content-Unterordnern.
**Season 1 = footage-first, nicht story-first.** Clips **nicht** auf eine feste Episoden-Struktur mappen –
es gibt noch keine. Nur beschreiben, was tatsächlich im Material ist.

Serie: „Weg zum Porsche" – Auto-Flipping/Restauration Richtung Traumauto (Hook-Copy bleibt
„Ich schenk euch mein Traumauto!", kein Porsche im Hook). Projektauto: Mini Cooper R56 1.6, 122 PS,
195.000 km, Ölverlust, TÜV läuft April ab. Community-first (Polls, Cliffhanger), Deutsch, vertikal 9:16,
YouTube/Instagram/TikTok.

**Anonymität Pflicht:** keine Gesichter, keine Kennzeichen, keine Adressen/Kontaktdaten in
verwendbaren Clips. Rohe/unveränderte Stimme ist ok (bewusste Entscheidung).

Keine Videodateien bearbeiten – nur Markdown-Reports erzeugen.

## Ablauf – IN BATCHES, EIN ORDNER NACH DEM ANDEREN (Context-Overflow vermeiden)

Vor Start: die 3 Unterordner auflisten und Struktur bestätigen lassen.

Pro Unterordner:
1. Alle Videodateien mit `ffprobe` listen (Dateiname, Dauer, Auflösung, ggf. Erstelldatum).
2. Pro Video mit `ffmpeg` Frames in einen Temp-Ordner extrahieren. **Intervall nach
   Clip-Länge – siehe „Sampling-Policy" unten.** Default für kurze Clips (≤ 60 s): alle 2 s
   (`-vf fps=1/2`).
3. Frames ansehen, ein-Absatz-Beschreibung: Was passiert, welcher Teil des Autos/Prozesses,
   verwendbar (scharf, brauchbares Framing) oder Ausschuss (unscharf, versehentlich, sinnlos).
4. Explizit flaggen, wenn ein Frame zeigt: sichtbares Gesicht, Kennzeichen, Hausnummer/Adresse
   oder anderes identifizierendes Detail → **„NEEDS BLUR" mit ungefährem Timestamp**.
5. Audioqualität qualitativ taggen, falls aus dem Kontext erkennbar (best-effort, nicht überziehen).
6. Clip **deskriptiv** kategorisieren (NICHT gegen feste Episodenliste) – z. B. „Diagnose",
   „Reparatur", „Chaos-Moment", „Reveal/Vorher-Nachher", „B-Roll", „Sonstiges". Passende
   Kategorien dürfen erfunden werden.
7. Temp-Frames des Videos nach der Beschreibung löschen (nichts auf der Platte anhäufen).

Temp-Frames in den Scratchpad extrahieren (nicht ins Repo), z. B.
`/private/tmp/.../scratchpad/frames/` – **nie** unter `/Volumes/holdmydata/camera/` (macOS legt
dort `._`-Dateien an) und **nie** ins Repo.

## Output

Eine Markdown-Datei pro Unterordner in **`content/season-1/catalog/`** (in diesem Repo),
`catalog_folder1.md` / `_folder2.md` / `_folder3.md`:

| Filename | Duration | Content Description | Usable? | Needs Blur? | Kategorie |
|---|---|---|---|---|---|

**Nach Ordner 1 stoppen und den Katalog zeigen**, damit früh nachjustiert werden kann, bevor
Ordner 2 startet.

## Merge

Nach allen Ordnern: alles zusammenführen in **`content/season-1/ROHKATALOG.md`**:
- Alle Clips nach den **entstandenen deskriptiven Kategorien** gruppieren (nicht nach festem Plan).
- Alle „NEEDS BLUR"-Clips an einer Stelle als **Checkliste** (zum Abarbeiten in CapCut zuerst).
- Optional: auffällige Cluster/Story-Fäden über Clips hinweg notieren – **als Beobachtung, nicht
  als vorgeschriebener Content-Plan**. Posting-Reihenfolge/Strategie entscheidet der User selbst.

## Sampling-Policy (nach Clip-Länge, festgelegt 2026-08-28)

**Prinzip:** so fein wie nötig, um Inhalt zu beschreiben und `NEEDS BLUR`-Momente (Gesicht,
Kennzeichen, Adresse) zu erkennen — aber pro Clip grob **60–240 Frames** anpeilen, damit die
Sichtung (als Kontaktbögen, ~54 Frames/Bogen → max. 4–5 Bögen/Clip) handhabbar bleibt. Bei
sehr kurzen Clips ruhig feiner (Kosten trivial).

| Clip-Dauer | Intervall | `ffmpeg -vf` | Frames (ca.) |
|---|---|---|---|
| ≤ 4 s | 0,5 s | `fps=2` | 2–8 |
| 4 – 10 s | 1 s | `fps=1` | 4–10 |
| 10 – 60 s | 2 s | `fps=1/2` | 5–30 |
| 1 – 3 min | 3 s | `fps=1/3` | 20–60 |
| 3 – 10 min | 5 s | `fps=1/5` | 36–120 |
| 10 – 20 min | 8 s | `fps=1/8` | 75–150 |
| 20 – 45 min | 15 s | `fps=1/15` | 80–180 |
| 45 – 90 min | 30 s | `fps=1/30` | 90–180 |
| 1,5 – 4 h | 60 s | `fps=1/60` | 90–240 |
| 4 – 12 h | 3 min | `fps=1/180` | 80–240 |
| 12 – 24 h | 6 min | `fps=1/360` | 120–240 |

**Zusatzregeln:**
- `NEEDS BLUR`-Timestamps sind immer **ungefähr**. Ab > ~3 min ist die Frame-Sichtung nur
  ein Indikator — vor Veröffentlichung zusätzlich im Editor (CapCut) durchscrubben.
- Static/Locked-off- oder Timelapse-Quellen (z. B. montierte Dachkamera): am unteren Ende der
  Frequenz bleiben; die Szene ändert sich kaum.
- Bekannter Ausschuss (Kamera abgelegt, Objektiv verdeckt, komplett unscharf): sobald erkannt,
  Rest des Clips nur stichprobenartig prüfen und als „throwaway" abhaken.
- Frames werden zu Kontaktbögen montiert; Temp-Frames nach jeder Clip-Beschreibung löschen.

### Anwendung auf das aktuelle Material (61 Clips)
- Fast alle Intro-/Dach-/Entrosten-Clips sind < 90 s → 2 s (bzw. 1 s / 0,5 s bei sehr kurzen).
- 3 – 10 min → 5 s: `Intro/PXL_20260819_152618793` (6:48), `Intro/PXL_20260819_153615813`
  (3:50), `Dach/PXL_20260822_105142336` (4:53), `Dach/PXL_20260822_125050629` (9:50),
  `Entrosten/PXL_20260827_150107404` (3:05).
- 45 – 90 min → 30 s: `Dach/PXL_20260822_093040314` (~45:44).
