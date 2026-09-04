# Regelwerk — Kanalproduktion "DAY ONE"

Dieses Dokument ist die verbindliche Grundlage für jeden Post. Ziel: Jeder
Post soll sich anfühlen wie derselbe Kanal, unabhängig davon, wer ihn
schneidet oder welche Session (Web, Mobile, CLI) daran arbeitet.

Gehört zusammen mit [`SKRIPTE.md`](./SKRIPTE.md) (das fortlaufende
Skript-Dokument aller Posts). Regelwerk = *wie* wir arbeiten,
Skripte-Dokument = *was* in welchem Post passiert.

## 1. Kanal-Motto

> Kein Auto. Keine Ahnung. Aber naiv genug, es trotzdem zu versuchen.

Destilliert aus Post 1. Jeder Post muss diesen Kern irgendwo transportieren
— nicht zwingend wortwörtlich, aber spürbar. Das ist der Prüfstein für
"passt das zum Kanal?".

## 1a. Gefühlswelt → Bildsprache

Sechs Gefühle sollen jeder Post transportieren: **cinematisch,
bodenständig, ruhig, witzig, fleißig, naiv**. Das ist keine zusätzliche
Regel, sondern die Begründung für die bestehenden (Familien §2,
Farbregeln §6, Bildlook §11):

| Gefühl | Wo es herkommt |
|---|---|
| Cinematisch | LUT (§11): ACES-Filmic-Kontrastkurve, weicher Highlight-Rolloff |
| Bodenständig | LUT: 12 % Entsättigung, angehobene statt abgesoffene Schwarzwerte; Off-White statt Reinweiß (§6) |
| Ruhig | LUT: gedeckte, warme Töne statt Hochglanz-Kontrast; Season-Familie: Ease-out ohne Overshoot (§2) |
| Naiv | LUT: warme Schatten/Lichter statt kaltes Blockbuster-Teal; `ShopLight`-Flackern statt `LightStreak`-Glanz |
| Witzig | **Schreibweise**, nicht Bild — kurze, trockene Captions, die Pointe nie erklären (Beispiel Post 1: Grillenzirpen als Gag-Sound) |
| Fleißig | **Struktur**, nicht Bild — `MonoReadout`-Zähler machen Arbeit sichtbar/messbar (Tage, Stunden, ab §10 auch Euro) |

Vier der sechs Gefühle laufen über die Farb-/Licht-Ebene (LUT + Familien),
zwei über Schreib- und Struktur-Entscheidungen. Beim Schreiben eines
neuen Posts beide Ebenen prüfen, nicht nur die Bild-Ebene.

## 2. Zwei Animations-Familien — nicht mischen

Es gibt aktuell zwei fertige Komponenten-Familien in
`cooper-animations/src/`. Sie transportieren unterschiedliche Gefühle und
dürfen nicht innerhalb derselben Aussage vermischt werden (z. B. keine
`MarkerLine` mit `LightStreak`-Glanz).

| | Hook-Familie | Season-Familie ("Day One") |
|---|---|---|
| Komponenten | `ImpactHeadline`, `LightStreak` (`src/shared/`) | `MarkerLine`, `ShopLight`, `MonoReadout`, `Grain` (`src/shared/`) |
| Font | Montserrat Black, Versalien | Permanent Marker (Aussagen) / JetBrains Mono (Zahlen) |
| Bewegung | Spring-Overshoot, knallt rein, kein Fade | Ease-out, kein Overshoot, sanftes Einsetzen |
| Licht-Akzent | glänzender `LightStreak`-Sweep | flackerndes `ShopLight` (Werkstattlampe) |
| Einsatzzweck | reiner Cold-Open-Hook, Erwartung-vs-Realität-Momente | alles, was Charakter/Ehrlichkeit transportiert: Tages-Stempel, Status, Bekenntnis-Sätze |
| Beispiel-Kompositionen | `TraumautoHook(DE)`, `ExpectationReality(DE)` | `DayOne(DE)` |

**Faustregel:** Der Hook verkauft (0.6–1.2 s, hart, glänzend). Die
Season-Familie gesteht (langsamer, ehrlicher, nie überschossen).

### 2a. Dritte Kategorie: Caption-Overlays (noch zu bauen)

Post 1 und 2 brauchen kurze Text-Einblendungen **über echtem Footage**
(z. B. "Ich hab keins.", "Und Autoprofi bin ich auch nicht."). Das ist
weder ein Vollbild-Hook noch ein Season-Stempel, sondern eine dritte,
noch nicht existierende Komponente: kleinere, am unteren Bilddrittel
sitzende `MarkerLine`-Captions ohne Vollbild-Hintergrund (transparent,
damit das Footage durchscheint). Bis sie gebaut ist, stehen diese Zeilen
im Skript-Dokument als offene technische Notiz.

## 3. Pflichtstruktur jedes Posts

```
Cold Open (Hook-Familie)
  → Szenen-Sequenz (Footage + Caption-Overlays)
    → optional: Season-Stempel (z. B. "TAG 1")
      → Schluss-Beat (Punchline oder Audio-only)
```

Post 1 definiert diese Struktur als CapCut-Vorlage (siehe Abschnitt 8).
Jeder Folgepost übernimmt Cold Open + Grundgerüst unverändert und
ersetzt nur die post-spezifischen Szenen/Captions.

## 4. Schnitt-Regeln

- **Nur harte Schnitte** zwischen Segmenten — kein Crossfade, auch nicht
  zwischen Animation und Footage. Das gilt kanalweit, nicht nur
  innerhalb einer Remotion-Komposition.
- Eine Caption bleibt exakt so lange stehen, wie sie zum Lesen braucht:
  Faustregel **0.6 s Sockel + 0.06 s pro Zeichen**, danach harter Schnitt.
- Audio-only-Momente (z. B. "V8 startet") bekommen **keine** Text-Overlay.
  Stille im Bild wirken lassen — nicht jeden Moment beschriften.

## 5. Sprache

- Primär **Deutsch**, EN-Fassung ist die zweitrangige Parallel-Variante.
- EN ist strukturell identisch zur DE-Fassung (gleiche Timings, gleiche
  Schnitte) — nur der Text ist übersetzt. Kein separates Timing pro
  Sprache erfinden.
- Technisches Muster: `COPY_DE` / `COPY_EN` in jeder `constants.ts`,
  Composition-IDs `NameDE` / `Name` (siehe bestehende Kompositionen).
- Schriftgröße darf pro Sprache abweichen (siehe `headlineFontSize` /
  `fontSize` Pattern), weil Zeilenlängen unterschiedlich sind — das ist
  kein Bruch der Regel, sondern genau dafür vorgesehen.

## 6. Farbregeln

- Hintergrund immer reines Schwarz `#000000` — Kompatibilität mit
  CapCut-Overlay (Screen-Blend / harter Schnitt auf Footage).
- Akzentfarbe **Amber `#FF9F45`** ist reserviert für:
  1. Season-Stempel-Zahlen (Tage, Stunden, Geld),
  2. den einen "Turn"-Satz pro Post — die Zeile, die die Wahrheit auf den
     Punkt bringt (in Post 1: *"Aber naiv genug, daran zu glauben."*).
- Alle anderen Aussagen: warmes Off-White `#EDEAE2`, nie reines Weiß —
  reines Weiß bleibt der Hook-Familie vorbehalten.
- Keine weiteren Akzentfarben ohne Rücksprache. Konsistenz schlägt
  Abwechslung.

## 7. Naming & Ablage

- Post-spezifische Compositions-Variante: `Post{N}{Sprache}`, z. B.
  `Post2DE`, `Post2` (EN). Bei mehreren Szenen pro Post:
  `Post2Scene1DE` usw.
- Assets (Fonts, Sounds) liegen zentral in `public/`, nie pro Post
  dupliziert.
- Render-Output-Namensschema: `postXX-{de|en}-{szenenname}.mp4`, z. B.
  `post01-de-hook.mp4`.

## 8. CapCut-Template-Workflow

1. Overlay-Clips aus Remotion rendern (`npx remotion render <Id>
   out/<name>.mp4`) — Hintergrund bleibt reines Schwarz.
2. In CapCut: Overlay auf eigener Spur über die Rohaufnahme legen. Wo
   Leuchtelemente (`LightStreak`/`ShopLight`) sichtbar bleiben sollen,
   Blend-Mode **"Bildschirm"** verwenden; sonst reicht harter Schnitt
   zwischen Overlay-Clip und Footage.
3. Caption-Overlays einzeln an die Schnittpunkte der Rohaufnahme
   andocken — Timings kommen aus dem Skript-Dokument, kein Fein-Timing
   nötig, wenn der Rohschnitt sich ans Skript hält.
4. **Post 1**, sobald fertig geschnitten, als CapCut-Projektvorlage
   sichern ("Kanal-Vorlage v1"). Jeder Folgepost dupliziert diese
   Vorlage, statt neu aufzubauen.

## 9. Checkliste vor Veröffentlichung

- [ ] DE- **und** EN-Fassung gerendert
- [ ] Grain sichtbar, aber nicht dominant (Referenz: `GRAIN_OPACITY = 0.05`)
- [ ] Nur harte Schnitte, keine versehentlichen Crossfades
- [ ] Motto-Check: Transportiert der Post den Kanal-Kern (Abschnitt 1)?
- [ ] Amber nur für Zahlen + den einen Turn-Satz verwendet
- [ ] `SKRIPTE.md` aktualisiert: dieser Post final markiert, nächster
      Post mindestens als Platzhalter angelegt

## 10. Monetarisierung

Eigenes Dokument: [`MONETARISIERUNG.md`](./MONETARISIERUNG.md). Kurz
zusammengefasst:

- Ab Post 1 aktiv (Affiliate-Links auf real benutztes Werkzeug/Teile),
  nicht erst nach Vertrauensaufbau.
- **Maximal** heißt Flächenabdeckung (Beschreibung, Pinned Comment,
  Link in Bio — unbegrenzt), nicht In-Video-Frequenz.
- Im Video: **maximal ein** Callout pro Post, immer kontextuell an eine
  Szene angedockt, **nie** im Hook, **nie** im Turn-Satz.
- Eigene Komponenten `AffiliateCallout` und `ProjektFonds` (Outro-Stempel
  mit Euro-Betrag, analog zum `DayOne`-Stempel) — noch zu bauen.
- Trägt zum Kanal-Ziel bei: Traumauto-Giveaway am Season-1-Finale, dann
  Aufbau Richtung 30.000-€-Giveaway in Season 2, finanziert über den
  sichtbaren "Projekt-Fonds".

## 11. Bildlook / LUT

Datei: [`luts/day-one-v1.cube`](../luts/day-one-v1.cube) (33-Punkt
3D-LUT, Standard-`.cube`-Format). Vorschau (Original links / Grade
rechts): [`luts/day-one-v1-preview.png`](../luts/day-one-v1-preview.png).
Erzeugt reproduzierbar über `luts/generate_lut.py` (reine
Python-Standardbibliothek, keine externen Abhängigkeiten).

**CapCut-Import:**
1. Anpassungs-Ebene über die gesamte Timeline legen (nicht pro Clip
   einzeln, für konsistenten Look).
2. **Anpassen → LUT → Importieren** → `day-one-v1.cube` auswählen.
3. Intensität 80–100 %; bei sehr dunklem Rohmaterial auf 60–70 %
   reduzieren, damit Schatten nicht absaufen.
4. Auf Remotion-Overlays (reines Schwarz + Grain) **nicht** anwenden —
   die sind bereits final; die LUT ist für das Kamera-Footage gedacht.

**Technische Basis** (siehe §1a für die Gefühls-Zuordnung):
Lift/Gamma/Gain pro Kanal (warme, angehobene Schatten; warme Lichter;
zurückgenommenes Blau in Höhen) → ACES-Filmic-Kurve (Narkowicz-
Approximation) für Kontrast und Highlight-Rolloff → 12 % Entsättigung
Richtung Luma.

Anpassungen: Parameter stehen oben in `generate_lut.py` als benannte
Konstanten (`LIFT`, `GAMMA`, `GAIN`, `DESAT`) — Wert ändern, Skript neu
laufen lassen, `day-one-v1.cube` wird überschrieben.

## 12. Ablage: Server vs. Git

**Code, Konfiguration, Dokumentation, Skripte und kleine textbasierte
Assets** (LUT `.cube`, Font-Dateien) gehören ins Git-Repo — und werden
nach jedem relevanten Arbeitsschritt gepusht, damit alles persistiert
ist, nicht erst am Ende einer Session.

**Große generierte Binärdateien** (gerenderte mp4s, Referenz-PNG-Stills,
später Rohaufnahmen) gehören **nicht** ins Repo, sondern auf den eigenen
Server — dort in einem passenden Ordner je Post. Das bestehende
`.gitignore` schließt `out/` bereits aus; das entspricht dieser Regel.

**Status:** Diese Session hat aktuell keine Verbindung zu einem Server
(bewusst offen gelassen statt geraten, siehe Entscheidung unten). Bis
die Anbindung steht, werden Renders wie bisher per Chat ausgeliefert
und müssen manuell auf den Server geladen werden. Sobald ein Zugang
(SFTP/Cloud-Speicher/etc.) bereitsteht, wird dieser Abschnitt aktualisiert
und ein automatischer Push-Schritt nach jedem Render ergänzt.

Empfohlene Ordnerstruktur auf dem Server (Vorschlag, an eure Struktur
anpassen):

```
/day-one/
  post-01/
    renders/     (mp4, direkt aus Remotion)
    footage/     (Rohaufnahmen)
    exports/     (fertig geschnittene CapCut-Exporte)
  post-02/
    ...
```

Git bleibt die Quelle der Wahrheit für alles Reproduzierbare (Code,
LUT-Generator, Dokumente). Renders sind reproduzierbare Ableitungen
davon und müssen nicht versioniert werden.

## 13. Offene Entscheidungen

Punkte, die bewusst *nicht* automatisch entschieden wurden, weil sie
euren Content betreffen — bitte bei Bedarf im Skript-Dokument fixieren:

- **Hook-Wortlaut:** Die bestehende `TraumautoHook`-Komposition trägt aktuell
  den Text *"Ich verschenke mein Traumauto!"* (Ich-Perspektive). Post 1
  im Skript-Dokument verwendet *"Du bekommst mein Traumauto!"*
  (Du-Perspektive). Beides funktioniert, aber nur eine Variante sollte
  kanalweit stehen bleiben — siehe offene Notiz in `SKRIPTE.md` Post 1.
- **Server-Anbindung für Renders (§12):** Zugangsweg noch offen —
  bei Bedarf im Chat anstoßen, dann wird §12 ergänzt und Renders werden
  ab dann automatisch nach jedem Render gepusht statt manuell verteilt.
