import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import {
  STREAK_ANGLE,
  STREAK_COLOR,
  STREAK_DURATION,
  STREAK_PEAK_OPACITY,
  STREAK_START,
  STREAK_WIDTH,
} from "./constants";

export type LightStreakProps = {
  /** Frame the sweep starts on. */
  readonly startFrame?: number;
  /** How many frames the sweep takes to cross the frame. */
  readonly durationInFrames?: number;
  readonly width?: number;
  readonly angle?: number;
  readonly color?: string;
  readonly peakOpacity?: number;
};

/**
 * A single specular sweep that travels left-to-right across whatever it is
 * layered on top of. Purely driven by interpolate() so it stays reusable in
 * other intro variants: <LightStreak startFrame={40} angle={-12} />
 */
export const LightStreak: React.FC<LightStreakProps> = ({
  startFrame = STREAK_START,
  durationInFrames = STREAK_DURATION,
  width = STREAK_WIDTH,
  angle = STREAK_ANGLE,
  color = STREAK_COLOR,
  peakOpacity = STREAK_PEAK_OPACITY,
}) => {
  const frame = useCurrentFrame();
  const { width: compositionWidth, height: compositionHeight } =
    useVideoConfig();

  const local = frame - startFrame;

  // Travel from fully off the left edge to fully off the right edge.
  const translateX = interpolate(
    local,
    [0, durationInFrames],
    [-compositionWidth * 0.6 - width, compositionWidth * 0.6 + width],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  // Ramp up fast, hold for a beat, fall off slower.
  const opacity = interpolate(
    local,
    [
      0,
      durationInFrames * 0.25,
      durationInFrames * 0.55,
      durationInFrames,
    ],
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
