import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";

export type ShopLightProps = {
  readonly startFrame?: number;
  readonly color?: string;
  /** 0-1, horizontal position of the bulb. */
  readonly x?: number;
  /** 0-1, vertical position of the bulb. */
  readonly y?: number;
  readonly radius?: number;
  readonly minOpacity?: number;
  readonly maxOpacity?: number;
};

/**
 * A single bare bulb's glow, flickering like it's on a bad garage circuit —
 * the Day One equivalent of the clickbait hooks' glossy LightStreak. Where
 * that reads as polish, this reads as "the lights barely work here."
 *
 * The flicker is a sum of a few incommensurate sine waves rather than
 * Math.random(): it has to be deterministic so the same frame number always
 * renders the same glow, however the composition is scrubbed or re-rendered.
 */
export const ShopLight: React.FC<ShopLightProps> = ({
  startFrame = 0,
  color = "#FFB347",
  x = 0.5,
  y = 0.38,
  radius = 900,
  minOpacity = 0.12,
  maxOpacity = 0.55,
}) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const t = Math.max(0, frame - startFrame);

  const slow = Math.sin(t * 0.21) * 0.5 + 0.5;
  const mid = Math.sin(t * 0.7 + 1.7) * 0.5 + 0.5;
  const fast = Math.sin(t * 2.9 + 0.4) * 0.5 + 0.5;
  // Raising to a power turns smooth troughs into sharp, bulb-like dips.
  const flicker = Math.pow(slow * 0.5 + mid * 0.35 + fast * 0.15, 1.6);
  const opacity = minOpacity + flicker * (maxOpacity - minOpacity);

  return (
    <div
      style={{
        position: "absolute",
        left: width * x - radius,
        top: height * y - radius,
        width: radius * 2,
        height: radius * 2,
        opacity,
        pointerEvents: "none",
        background: `radial-gradient(circle, ${color} 0%, ${color}55 30%, transparent 70%)`,
        filter: "blur(4px)",
      }}
    />
  );
};
