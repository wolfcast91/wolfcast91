import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { MONO_FONT_FAMILY } from "./season1Font";

export type MonoReadoutProps = {
  readonly text: string;
  readonly fontSize: number;
  readonly color?: string;
  /** Frame (local to the enclosing Sequence) typing starts. */
  readonly startFrame?: number;
  readonly charsPerFrame?: number;
  readonly showCursor?: boolean;
};

/**
 * A logbook-style typewriter readout for the honest numbers (day count,
 * hours, money spent) — the deadpan counterpart to the marker font's
 * confessions. Typed on, not faded, and the cursor keeps blinking after
 * the line is done so the frame never feels fully "settled."
 */
export const MonoReadout: React.FC<MonoReadoutProps> = ({
  text,
  fontSize,
  color = "#EDEAE2",
  startFrame = 0,
  charsPerFrame = 0.9,
  showCursor = true,
}) => {
  const frame = useCurrentFrame();
  const t = frame - startFrame;

  const visibleChars = Math.floor(
    interpolate(t, [0, text.length / charsPerFrame], [0, text.length], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }),
  );
  const cursorOn = Math.floor(frame / 15) % 2 === 0;

  return (
    <span
      style={{
        fontFamily: MONO_FONT_FAMILY,
        fontSize,
        color,
        letterSpacing: 1,
      }}
    >
      {text.slice(0, visibleChars)}
      {showCursor && cursorOn ? "_" : ""}
    </span>
  );
};
