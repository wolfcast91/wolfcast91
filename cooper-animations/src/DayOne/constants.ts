/**
 * Season 1: "DAY ONE" — the series identity, not a hook. A nobody, no
 * budget, no plan, starting a build. Every constant here exists to be
 * reused by future episode pieces, not just this cold open.
 *
 * Frame numbers assume FPS = 30.
 */

// --- Composition ---------------------------------------------------------
export const FPS = 30;
export const WIDTH = 1080;
export const HEIGHT = 1920;

// --- Timeline (frames) -----------------------------------------------------
// Four short truths, one at a time, hard cut between them — then the
// series stamp. Slower than the clickbait hooks on purpose: this breathes.
export const LINE_1_START = 0;
export const LINE_1_END = 42;
export const LINE_2_START = 42;
export const LINE_2_END = 82;
export const LINE_3_START = 82;
export const LINE_3_END = 132;
export const LINE_4_START = 132;
export const LINE_4_END = 175;
export const STAMP_START = 175;
export const STAMP_END = 240;

export const DURATION_IN_FRAMES = STAMP_END;

// --- Copy ------------------------------------------------------------------
export type DayOneCopy = {
  readonly lines: readonly [string, string, string, string];
  readonly stampTitle: string;
  readonly readoutLine1: string;
  readonly readoutLine2: string;
};

export const COPY_EN: DayOneCopy = {
  lines: ["No budget.", "No plan.", "No idea what I'm doing.", "Just started."],
  stampTitle: "DAY ONE",
  readoutLine1: "0 HOURS LOGGED",
  readoutLine2: "$0 SPENT",
};

export const COPY_DE: DayOneCopy = {
  lines: ["Kein Budget.", "Kein Plan.", "Keine Ahnung, was ich tue.", "Einfach angefangen."],
  stampTitle: "TAG EINS",
  readoutLine1: "0 STUNDEN PROTOKOLLIERT",
  readoutLine2: "0 € AUSGEGEBEN",
};

// --- Colors ------------------------------------------------------------------
export const BACKGROUND_COLOR = "#000000"; // pure black for clean compositing
export const TEXT_COLOR = "#EDEAE2"; // warm off-white, not clinical white
export const ACCENT_COLOR = "#FF9F45"; // bare-bulb amber, not glossy white

// --- Type --------------------------------------------------------------------
export const LINE_FONT_SIZE = 84;
export const EMPHASIS_FONT_SIZE = 96; // the 4th, final truth lands slightly bigger
export const STAMP_FONT_SIZE = 108;
export const READOUT_FONT_SIZE = 34;

// --- Texture / lighting --------------------------------------------------
export const GRAIN_OPACITY = 0.05;
export const SHOP_LIGHT_MIN_OPACITY = 0.1;
export const SHOP_LIGHT_MAX_OPACITY = 0.5;
