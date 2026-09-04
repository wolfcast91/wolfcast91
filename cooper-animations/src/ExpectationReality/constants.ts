/**
 * "Expectation / Reality" two-card hook. Same visual theme as TraumautoHook:
 * pure black, Montserrat Black, spring impact, light streak accent.
 * Frame numbers assume FPS = 30.
 */

// --- Composition ---------------------------------------------------------
export const FPS = 30;
export const WIDTH = 1080;
export const HEIGHT = 1920;

// --- Timeline (frames) ---------------------------------------------------
export const CARD_ONE_START = 0;
export const CARD_ONE_END = 18; // hard cut at 0.6s
export const CARD_TWO_START = 18;
export const CARD_TWO_END = 36; // composition ends at 1.2s

export const DURATION_IN_FRAMES = CARD_TWO_END;

// Each card gets its own streak, starting shortly after its impact.
export const STREAK_START = 3; // relative to the card, not the composition
export const STREAK_DURATION = 12;
export const STREAK_WIDTH = 190;
export const CARD_ONE_STREAK_ANGLE = 18;
export const CARD_TWO_STREAK_ANGLE = -18; // mirrored so the cut reads as a cut
export const STREAK_PEAK_OPACITY = 0.9;

// --- Colors --------------------------------------------------------------
export const BACKGROUND_COLOR = "#000000"; // pure black for clean compositing
export const TEXT_COLOR = "#FFFFFF";

// --- Type ----------------------------------------------------------------
export const LINE_HEIGHT = 1.05;
export const LETTER_SPACING = -6;

// --- Copy ----------------------------------------------------------------
export type CardCopy = {
  readonly cardOne: string;
  readonly cardTwo: string;
  readonly fontSize: number;
};

export const COPY_EN: CardCopy = {
  cardOne: "EXPECTATION",
  cardTwo: "REALITY",
  fontSize: 112,
};

export const COPY_DE: CardCopy = {
  cardOne: "ERWARTUNG",
  cardTwo: "REALITÄT",
  // "ERWARTUNG" is the longest line; 130 grazed both frame edges at the
  // overshoot peak, so this leaves a margin.
  fontSize: 122,
};
