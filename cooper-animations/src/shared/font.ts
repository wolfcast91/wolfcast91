import { cancelRender, continueRender, delayRender, staticFile } from "remotion";

/**
 * Montserrat Black is bundled in public/fonts so renders never depend on a
 * network request. Swap the file (and this family name) to change the face.
 */
export const FONT_FAMILY =
  "'Montserrat Black', 'Helvetica Neue', Helvetica, Arial, sans-serif";

const handle = delayRender("Loading Montserrat Black");

const font = new FontFace(
  "Montserrat Black",
  `url(${staticFile("fonts/Montserrat-Black-latin.woff2")}) format('woff2')`,
  { weight: "900", style: "normal" },
);

font
  .load()
  .then(() => {
    document.fonts.add(font);
    continueRender(handle);
  })
  .catch((err) => cancelRender(err));
