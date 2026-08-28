import React from "react";
import { AbsoluteFill, Sequence } from "remotion";
import { FONT_FAMILY } from "../shared/font";
import { ImpactHeadline } from "../shared/ImpactHeadline";
import { LightStreak } from "../shared/LightStreak";
import {
  BACKGROUND_COLOR,
  HEADLINE_END,
  HEADLINE_FONT_SIZE,
  HEADLINE_LETTER_SPACING,
  HEADLINE_LINE_HEIGHT,
  HEADLINE_SCALE_FROM,
  HEADLINE_SPRING_CONFIG,
  HEADLINE_START,
  HEADLINE_TEXT,
  STREAK_ANGLE,
  STREAK_DURATION,
  STREAK_PEAK_OPACITY,
  STREAK_START,
  STREAK_WIDTH,
  SUBLINE_END,
  SUBLINE_FONT_SIZE,
  SUBLINE_LETTER_SPACING,
  SUBLINE_START,
  SUBLINE_TEXT,
  TEXT_COLOR,
} from "./constants";

export type PorscheHookProps = {
  readonly headlineText?: string;
  readonly sublineText?: string;
  /** Line lengths differ per language, so the size travels with the copy. */
  readonly headlineFontSize?: number;
};

const Subline: React.FC<{ readonly text: string }> = ({ text }) => {
  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        textAlign: "center",
      }}
    >
      <h2
        style={{
          margin: 0,
          fontFamily: FONT_FAMILY,
          fontWeight: 900,
          fontSize: SUBLINE_FONT_SIZE,
          letterSpacing: SUBLINE_LETTER_SPACING,
          color: TEXT_COLOR,
        }}
      >
        {text}
      </h2>
    </AbsoluteFill>
  );
};

export const PorscheHook: React.FC<PorscheHookProps> = ({
  headlineText = HEADLINE_TEXT,
  sublineText = SUBLINE_TEXT,
  headlineFontSize = HEADLINE_FONT_SIZE,
}) => {
  return (
    <AbsoluteFill style={{ backgroundColor: BACKGROUND_COLOR }}>
      <Sequence
        from={HEADLINE_START}
        durationInFrames={HEADLINE_END - HEADLINE_START}
      >
        <ImpactHeadline
          text={headlineText}
          fontSize={headlineFontSize}
          color={TEXT_COLOR}
          lineHeight={HEADLINE_LINE_HEIGHT}
          letterSpacing={HEADLINE_LETTER_SPACING}
          scaleFrom={HEADLINE_SCALE_FROM}
          springConfig={HEADLINE_SPRING_CONFIG}
        />
        <LightStreak
          startFrame={STREAK_START}
          durationInFrames={STREAK_DURATION}
          width={STREAK_WIDTH}
          angle={STREAK_ANGLE}
          peakOpacity={STREAK_PEAK_OPACITY}
        />
      </Sequence>

      {/* Hard cut, no crossfade. */}
      <Sequence
        from={SUBLINE_START}
        durationInFrames={SUBLINE_END - SUBLINE_START}
      >
        <Subline text={sublineText} />
      </Sequence>
    </AbsoluteFill>
  );
};
