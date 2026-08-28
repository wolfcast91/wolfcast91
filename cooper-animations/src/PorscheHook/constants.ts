/**
 * All tweakable values for the "PorscheHook" intro live here.
 * Frame numbers assume FPS = 30 (see Root.tsx).
 */

// --- Composition ---------------------------------------------------------
export const FPS = 30;
export const WIDTH = 1080;
export const HEIGHT = 1920;
export const DURATION_IN_FRAMES = 30; // 1.0s hook segment

// --- Timeline (frames) ---------------------------------------------------
export const HEADLINE_START = 0; // headline slams in
export const HEADLINE_END = 18; // hard cut away at 0.6s
export const SUBLINE_START = 18; // "The problem?" appears
export const SUBLINE_END = 30; // composition ends at 1.0s

// The streak crosses the frame right as the headline lands.
export const STREAK_START = 3;
export const STREAK_DURATION = 12;

// --- Copy ----------------------------------------------------------------
// Line breaks are explicit so the layout never reflows mid-animation, and the
// headline size travels with the copy because line lengths differ per language.
export type HookCopy = {
  readonly headline: string;
  readonly subline: string;
  readonly headlineFontSize: number;
};

export const COPY_EN: HookCopy = {
  headline: "I WILL GIVE\nAWAY MY\nDREAM CAR!",
  subline: "The problem?",
  headlineFontSize: 122,
};

export const COPY_DE: HookCopy = {
  headline: "ICH VERSCHENKE\nMEIN TRAUMAUTO!",
  subline: "Das Problem?",
  // Smaller than the EN cut: the longest DE line is 15 characters, and the
  // spring overshoot briefly scales the headline ~13% past its final size.
  headlineFontSize: 86,
};

export const HEADLINE_TEXT = COPY_EN.headline;
export const SUBLINE_TEXT = COPY_EN.subline;

// --- Colors --------------------------------------------------------------
export const BACKGROUND_COLOR = "#000000"; // pure black for clean compositing
export const TEXT_COLOR = "#FFFFFF";
export const STREAK_COLOR = "#FFFFFF";

// --- Type ----------------------------------------------------------------
export const HEADLINE_FONT_SIZE = COPY_EN.headlineFontSize;
export const HEADLINE_LINE_HEIGHT = 1.05;
export const HEADLINE_LETTER_SPACING = -6;
export const HEADLINE_MAX_WIDTH = 960; // px, inside the 1080 frame

export const SUBLINE_FONT_SIZE = 86;
export const SUBLINE_LETTER_SPACING = -2;

// --- Impact animation ----------------------------------------------------
export const HEADLINE_SCALE_FROM = 0.42; // starts small, punches out to 1
export const HEADLINE_SPRING_CONFIG = {
  damping: 9, // low damping => visible overshoot
  stiffness: 220,
  mass: 0.7,
} as const;

// --- Light streak --------------------------------------------------------
export const STREAK_WIDTH = 190; // px, before rotation
export const STREAK_ANGLE = 18; // degrees
export const STREAK_PEAK_OPACITY = 0.9;
