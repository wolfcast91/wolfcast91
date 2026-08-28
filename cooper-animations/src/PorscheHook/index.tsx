import React from "react";
import {
  AbsoluteFill,
  interpolate,
  Sequence,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import {
  BACKGROUND_COLOR,
  HEADLINE_END,
  HEADLINE_FONT_SIZE,
  HEADLINE_LETTER_SPACING,
  HEADLINE_LINE_HEIGHT,
  HEADLINE_MAX_WIDTH,
  HEADLINE_SCALE_FROM,
  HEADLINE_SPRING_CONFIG,
  HEADLINE_START,
  HEADLINE_TEXT,
  SUBLINE_END,
  SUBLINE_FONT_SIZE,
  SUBLINE_LETTER_SPACING,
  SUBLINE_START,
  SUBLINE_TEXT,
  TEXT_COLOR,
} from "./constants";
import { FONT_FAMILY } from "./font";
import { LightStreak } from "./LightStreak";

export type PorscheHookProps = {
  readonly headlineText?: string;
  readonly sublineText?: string;
};

const centered: React.CSSProperties = {
  justifyContent: "center",
  alignItems: "center",
  textAlign: "center",
};

const Headline: React.FC<{ readonly text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Under-damped spring => the text punches past 1 and settles back.
  const progress = spring({
    frame,
    fps,
    config: HEADLINE_SPRING_CONFIG,
  });

  // No fade: opacity stays at 1 from frame 0, only the scale sells the impact.
  const scale = interpolate(progress, [0, 1], [HEADLINE_SCALE_FROM, 1]);

  // Letters snap tight as the word lands, which reads as extra weight.
  const letterSpacing = interpolate(
    progress,
    [0, 1],
    [HEADLINE_LETTER_SPACING + 18, HEADLINE_LETTER_SPACING],
    { extrapolateRight: "clamp" },
  );

  return (
    <AbsoluteFill style={centered}>
      <h1
        style={{
          margin: 0,
          maxWidth: HEADLINE_MAX_WIDTH,
          fontFamily: FONT_FAMILY,
          fontWeight: 900,
          fontSize: HEADLINE_FONT_SIZE,
          lineHeight: HEADLINE_LINE_HEIGHT,
          letterSpacing,
          color: TEXT_COLOR,
          textTransform: "uppercase",
          whiteSpace: "pre", // explicit line breaks only => no reflow
          transform: `scale(${scale})`,
        }}
      >
        {text}
      </h1>
    </AbsoluteFill>
  );
};

const Subline: React.FC<{ readonly text: string }> = ({ text }) => {
  return (
    <AbsoluteFill style={centered}>
      <h2
        style={{
          margin: 0,
          maxWidth: HEADLINE_MAX_WIDTH,
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
}) => {
  return (
    <AbsoluteFill style={{ backgroundColor: BACKGROUND_COLOR }}>
      <Sequence
        from={HEADLINE_START}
        durationInFrames={HEADLINE_END - HEADLINE_START}
      >
        <Headline text={headlineText} />
        <LightStreak />
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
