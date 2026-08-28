import React from "react";
import { AbsoluteFill, Sequence } from "remotion";
import { ImpactHeadline } from "../shared/ImpactHeadline";
import { LightStreak } from "../shared/LightStreak";
import {
  BACKGROUND_COLOR,
  CARD_ONE_END,
  CARD_ONE_START,
  CARD_ONE_STREAK_ANGLE,
  CARD_TWO_END,
  CARD_TWO_START,
  CARD_TWO_STREAK_ANGLE,
  COPY_EN,
  LETTER_SPACING,
  LINE_HEIGHT,
  STREAK_DURATION,
  STREAK_PEAK_OPACITY,
  STREAK_START,
  STREAK_WIDTH,
  TEXT_COLOR,
} from "./constants";

export type ExpectationRealityProps = {
  readonly cardOneText?: string;
  readonly cardTwoText?: string;
  /** Line lengths differ per language, so the size travels with the copy. */
  readonly fontSize?: number;
};

const Card: React.FC<{
  readonly text: string;
  readonly fontSize: number;
  readonly streakAngle: number;
}> = ({ text, fontSize, streakAngle }) => {
  return (
    <>
      <ImpactHeadline
        text={text}
        fontSize={fontSize}
        color={TEXT_COLOR}
        lineHeight={LINE_HEIGHT}
        letterSpacing={LETTER_SPACING}
      />
      <LightStreak
        startFrame={STREAK_START}
        durationInFrames={STREAK_DURATION}
        width={STREAK_WIDTH}
        angle={streakAngle}
        peakOpacity={STREAK_PEAK_OPACITY}
      />
    </>
  );
};

export const ExpectationReality: React.FC<ExpectationRealityProps> = ({
  cardOneText = COPY_EN.cardOne,
  cardTwoText = COPY_EN.cardTwo,
  fontSize = COPY_EN.fontSize,
}) => {
  return (
    <AbsoluteFill style={{ backgroundColor: BACKGROUND_COLOR }}>
      <Sequence
        from={CARD_ONE_START}
        durationInFrames={CARD_ONE_END - CARD_ONE_START}
      >
        <Card
          text={cardOneText}
          fontSize={fontSize}
          streakAngle={CARD_ONE_STREAK_ANGLE}
        />
      </Sequence>

      {/* Hard cut, no crossfade — the second card re-slams from frame 0. */}
      <Sequence
        from={CARD_TWO_START}
        durationInFrames={CARD_TWO_END - CARD_TWO_START}
      >
        <Card
          text={cardTwoText}
          fontSize={fontSize}
          streakAngle={CARD_TWO_STREAK_ANGLE}
        />
      </Sequence>
    </AbsoluteFill>
  );
};
