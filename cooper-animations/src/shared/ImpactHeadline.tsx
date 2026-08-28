import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { FONT_FAMILY } from "./font";

/** Low damping => the headline punches past its final size and settles back. */
export const IMPACT_SPRING_CONFIG = {
  damping: 9,
  stiffness: 220,
  mass: 0.7,
} as const;

export const IMPACT_SCALE_FROM = 0.42;
export const IMPACT_LETTER_SPACING = -6;
/** Extra tracking at the start; snaps tight as the word lands. */
export const IMPACT_LETTER_SPACING_OVERSHOOT = 18;

export type ImpactHeadlineProps = {
  /** Use \n for line breaks — they are never re-wrapped. */
  readonly text: string;
  readonly fontSize: number;
  readonly color?: string;
  readonly lineHeight?: number;
  readonly letterSpacing?: number;
  readonly scaleFrom?: number;
  readonly springConfig?: Parameters<typeof spring>[0]["config"];
  readonly uppercase?: boolean;
};

/**
 * Centered headline that slams in on a spring: no fade, scale overshoot, and
 * tracking that tightens on landing. Shared by every intro variant.
 */
export const ImpactHeadline: React.FC<ImpactHeadlineProps> = ({
  text,
  fontSize,
  color = "#FFFFFF",
  lineHeight = 1.05,
  letterSpacing = IMPACT_LETTER_SPACING,
  scaleFrom = IMPACT_SCALE_FROM,
  springConfig = IMPACT_SPRING_CONFIG,
  uppercase = true,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({ frame, fps, config: springConfig });

  // No fade: opacity stays at 1 from frame 0, only the scale sells the impact.
  const scale = interpolate(progress, [0, 1], [scaleFrom, 1]);

  const animatedLetterSpacing = interpolate(
    progress,
    [0, 1],
    [letterSpacing + IMPACT_LETTER_SPACING_OVERSHOOT, letterSpacing],
    { extrapolateRight: "clamp" },
  );

  return (
    <AbsoluteFill
      style={{ justifyContent: "center", alignItems: "center", textAlign: "center" }}
    >
      <h1
        style={{
          margin: 0,
          fontFamily: FONT_FAMILY,
          fontWeight: 900,
          fontSize,
          lineHeight,
          letterSpacing: animatedLetterSpacing,
          color,
          textTransform: uppercase ? "uppercase" : "none",
          whiteSpace: "pre", // explicit line breaks only => no reflow
          transform: `scale(${scale})`,
        }}
      >
        {text}
      </h1>
    </AbsoluteFill>
  );
};
