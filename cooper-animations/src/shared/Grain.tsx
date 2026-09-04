import React, { useMemo } from "react";
import { useCurrentFrame } from "remotion";

export type GrainProps = {
  readonly opacity?: number;
  /** How many frames between noise re-seeds. Lower = more nervous grain. */
  readonly changeEveryFrames?: number;
};

/**
 * Cheap, deterministic film grain: an SVG feTurbulence field re-seeded every
 * few frames. No image asset, no per-viewer randomness — the same frame
 * number always renders the same grain, which is what a frame-exact
 * renderer needs. Screen-blended so it reads as noise, not a grey wash,
 * and still adds texture when the export is composited over real footage.
 */
export const Grain: React.FC<GrainProps> = ({
  opacity = 0.05,
  changeEveryFrames = 2,
}) => {
  const frame = useCurrentFrame();
  const seed = Math.floor(frame / changeEveryFrames) % 9973; // large prime, keeps it non-repeating within any real clip

  // A fresh <filter> id per seed forces the browser to recompute the
  // turbulence rather than reuse a cached bitmap from a previous frame.
  const filterId = useMemo(() => `grain-${seed}`, [seed]);

  return (
    <svg
      style={{
        position: "absolute",
        inset: 0,
        width: "100%",
        height: "100%",
        opacity,
        mixBlendMode: "screen",
        pointerEvents: "none",
      }}
    >
      <filter id={filterId}>
        <feTurbulence
          type="fractalNoise"
          baseFrequency={0.85}
          numOctaves={2}
          seed={seed}
          stitchTiles="stitch"
        />
        <feColorMatrix type="saturate" values="0" />
      </filter>
      <rect width="100%" height="100%" filter={`url(#${filterId})`} />
    </svg>
  );
};
