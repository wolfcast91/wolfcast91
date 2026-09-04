import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { MARKER_FONT_FAMILY } from "./season1Font";

export type MarkerLineProps = {
  readonly text: string;
  readonly fontSize: number;
  readonly color?: string;
  readonly underlineColor?: string;
  /** Frame (local to the enclosing Sequence) the line starts settling in. */
  readonly startFrame?: number;
  readonly showUnderline?: boolean;
};

/**
 * A single confession, hand-written. Unlike the clickbait hooks' impact
 * headline, this settles in gently (no spring overshoot — the whole point
 * of Day One is that nothing here is oversold) and gets underlined by a
 * single rough marker stroke instead of a glossy light streak.
 */
export const MarkerLine: React.FC<MarkerLineProps> = ({
  text,
  fontSize,
  color = "#EDEAE2",
  underlineColor = "#FF9F45",
  startFrame = 0,
  showUnderline = true,
}) => {
  const frame = useCurrentFrame();
  const t = frame - startFrame;

  const settleIn = interpolate(t, [0, 14], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: (x) => 1 - Math.pow(1 - x, 3), // ease-out, no overshoot
  });
  const translateY = interpolate(settleIn, [0, 1], [16, 0]);

  const strokeProgress = interpolate(t, [8, 22], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        display: "inline-block",
        opacity: settleIn,
        transform: `translateY(${translateY}px)`,
      }}
    >
      <span
        style={{
          fontFamily: MARKER_FONT_FAMILY,
          fontSize,
          color,
          lineHeight: 1.25,
        }}
      >
        {text}
      </span>
      {showUnderline ? (
        <svg
          viewBox="0 0 100 8"
          preserveAspectRatio="none"
          style={{ display: "block", width: "100%", height: fontSize * 0.14 }}
        >
          <path
            d="M1,4.5 Q15,2 30,5 T60,3.5 T99,5"
            fill="none"
            stroke={underlineColor}
            strokeWidth={2.4}
            strokeLinecap="round"
            pathLength={1}
            strokeDasharray={1}
            strokeDashoffset={1 - strokeProgress}
          />
        </svg>
      ) : null}
    </div>
  );
};
