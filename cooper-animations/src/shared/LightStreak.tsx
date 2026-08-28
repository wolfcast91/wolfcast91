import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";

/** Defaults, overridable per usage. */
export const DEFAULT_STREAK_WIDTH = 190; // px, before rotation
export const DEFAULT_STREAK_ANGLE = 18; // degrees
export const DEFAULT_STREAK_COLOR = "#FFFFFF";
export const DEFAULT_STREAK_PEAK_OPACITY = 0.9;
export const DEFAULT_STREAK_DURATION = 12; // frames to cross the frame

export type LightStreakProps = {
  /** Frame the sweep starts on, relative to the enclosing Sequence. */
  readonly startFrame?: number;
  readonly durationInFrames?: number;
  readonly width?: number;
  /** Negative angles lean the other way — handy for alternating cards. */
  readonly angle?: number;
  readonly color?: string;
  readonly peakOpacity?: number;
};

/**
 * A single specular sweep that travels left-to-right across whatever it is
 * layered on top of. Purely driven by interpolate(), so it drops into any
 * composition: <LightStreak startFrame={40} angle={-12} />
 */
export const LightStreak: React.FC<LightStreakProps> = ({
  startFrame = 0,
  durationInFrames = DEFAULT_STREAK_DURATION,
  width = DEFAULT_STREAK_WIDTH,
  angle = DEFAULT_STREAK_ANGLE,
  color = DEFAULT_STREAK_COLOR,
  peakOpacity = DEFAULT_STREAK_PEAK_OPACITY,
}) => {
  const frame = useCurrentFrame();
  const { width: compositionWidth, height: compositionHeight } =
    useVideoConfig();

  const local = frame - startFrame;

  // Travel from fully off the left edge to fully off the right edge.
  const travel = compositionWidth * 0.6 + width;
  const translateX = interpolate(
    local,
    [0, durationInFrames],
    [-travel, travel],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  // Ramp up fast, hold for a beat, fall off slower.
  const opacity = interpolate(
    local,
    [0, durationInFrames * 0.25, durationInFrames * 0.55, durationInFrames],
    [0, peakOpacity, peakOpacity * 0.7, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        overflow: "hidden",
        pointerEvents: "none",
        mixBlendMode: "screen",
      }}
    >
      <div
        style={{
          position: "absolute",
          top: -compositionHeight * 0.25,
          left: compositionWidth / 2 - width / 2,
          width,
          height: compositionHeight * 1.5,
          opacity,
          transform: `translateX(${translateX}px) rotate(${angle}deg)`,
          background: `linear-gradient(90deg, ${color}00 0%, ${color}1a 34%, ${color}80 46%, ${color} 50%, ${color}80 54%, ${color}1a 66%, ${color}00 100%)`,
          filter: "blur(3px)",
        }}
      />
    </div>
  );
};
