# cooper-animations

Remotion project for the intro / hook animations of the **„Weg zum Porsche"** content series.
Renders are exported as MP4 and dropped as an overlay onto real footage in CapCut / iMovie —
the animations are the black-background hook only, the rest of each video is cut outside Remotion.

Format: 1080 × 1920 (vertical 9:16), 30 fps.

## Commands

```console
npm i                              # install deps
npm run dev                        # Remotion Studio preview
npx remotion render PorscheHookDE  # render one composition to out/
```

## Compositions

| ID | Länge | Inhalt |
|---|---|---|
| `PorscheHook` | 1.0 s | EN hook: headline slams in (spring overshoot + light streak) → hard cut at 0.6 s → subline `"The problem?"` |
| `PorscheHookDE` | 1.0 s | DE-Schnitt: `"ICH SCHENK EUCH MEIN TRAUMAUTO!"` → hard cut → `"Das Problem?"` |
| `ExpectationReality` | 1.2 s | Two-card hard cut: `EXPECTATION` → `REALITY` |
| `ExpectationRealityDE` | 1.2 s | `ERWARTUNG` → `REALITÄT` |
| `HelloWorld`, `OnlyLogo` | – | Remotion-Boilerplate, ungenutzt |

Copy und die pro Sprache mitwandernde Schriftgröße liegen in
`src/<Composition>/constants.ts` (`COPY_EN` / `COPY_DE`). Bei zu langem Text die **Schriftgröße
anpassen, nicht den Text kürzen**.

## Hinweise

- Die Composition-IDs behalten den Namen `PorscheHook*` aus Projektstart. **Im Hook selbst wird
  kein Porsche genannt** – der Wortlaut ist `„Ich schenk euch mein Traumauto!"`.
- Gemeinsame Bausteine: `src/shared/ImpactHeadline.tsx` (Slam-in), `src/shared/LightStreak.tsx`,
  `src/shared/font.ts` (Montserrat Black, lokal in `public/fonts/`).

## Docs

Remotion-Grundlagen: <https://www.remotion.dev/docs/the-fundamentals>. Für manche Firmen ist
eine Company License nötig: <https://github.com/remotion-dev/remotion/blob/main/LICENSE.md>.
