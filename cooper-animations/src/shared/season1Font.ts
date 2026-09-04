import { cancelRender, continueRender, delayRender, staticFile } from "remotion";

/**
 * The Season 1 ("Day One") type system: a rough hand-marker face for the
 * personal voice, a monospace face for the honest numbers (day count,
 * hours, money spent). Both are bundled in public/fonts so renders never
 * depend on the network.
 */
export const MARKER_FONT_FAMILY =
  "'Permanent Marker', 'Segoe Print', cursive";

export const MONO_FONT_FAMILY =
  "'JetBrains Mono', 'SF Mono', Consolas, monospace";

const markerHandle = delayRender("Loading Permanent Marker");
const monoHandle = delayRender("Loading JetBrains Mono");

const markerFont = new FontFace(
  "Permanent Marker",
  `url(${staticFile("fonts/PermanentMarker-Regular.woff2")}) format('woff2')`,
  { weight: "400", style: "normal" },
);

const monoFont = new FontFace(
  "JetBrains Mono",
  `url(${staticFile("fonts/JetBrainsMono-Bold.woff2")}) format('woff2')`,
  { weight: "700", style: "normal" },
);

markerFont
  .load()
  .then((loaded) => {
    document.fonts.add(loaded);
    continueRender(markerHandle);
  })
  .catch((err) => cancelRender(err));

monoFont
  .load()
  .then((loaded) => {
    document.fonts.add(loaded);
    continueRender(monoHandle);
  })
  .catch((err) => cancelRender(err));
