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

## 10. Offene Entscheidungen

Punkte, die bewusst *nicht* automatisch entschieden wurden, weil sie
euren Content betreffen — bitte bei Bedarf im Skript-Dokument fixieren:

- **Hook-Wortlaut:** Die bestehende `TraumautoHook`-Komposition trägt aktuell
  den Text *"Ich verschenke mein Traumauto!"* (Ich-Perspektive). Post 1
  im Skript-Dokument verwendet *"Du bekommst mein Traumauto!"*
  (Du-Perspektive). Beides funktioniert, aber nur eine Variante sollte
  kanalweit stehen bleiben — siehe offene Notiz in `SKRIPTE.md` Post 1.
