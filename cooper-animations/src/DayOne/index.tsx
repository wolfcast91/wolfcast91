import React from "react";
import { AbsoluteFill, Sequence } from "remotion";
import { Grain } from "../shared/Grain";
import { MarkerLine } from "../shared/MarkerLine";
import { MonoReadout } from "../shared/MonoReadout";
import { ShopLight } from "../shared/ShopLight";
import { MARKER_FONT_FAMILY } from "../shared/season1Font";
import {
  ACCENT_COLOR,
  BACKGROUND_COLOR,
  COPY_EN,
  EMPHASIS_FONT_SIZE,
  GRAIN_OPACITY,
  LINE_1_END,
  LINE_1_START,
  LINE_2_END,
  LINE_2_START,
  LINE_3_END,
  LINE_3_START,
  LINE_4_END,
  LINE_4_START,
  LINE_FONT_SIZE,
  READOUT_FONT_SIZE,
  SHOP_LIGHT_MAX_OPACITY,
  SHOP_LIGHT_MIN_OPACITY,
  STAMP_END,
  STAMP_FONT_SIZE,
  STAMP_START,
  TEXT_COLOR,
} from "./constants";

export type DayOneProps = {
  readonly lines?: readonly [string, string, string, string];
  readonly stampTitle?: string;
  readonly readoutLine1?: string;
  readonly readoutLine2?: string;
};

const centered: React.CSSProperties = {
  justifyContent: "center",
  alignItems: "center",
  textAlign: "center",
  padding: "0 96px",
};

export const DayOne: React.FC<DayOneProps> = ({
  lines = COPY_EN.lines,
  stampTitle = COPY_EN.stampTitle,
  readoutLine1 = COPY_EN.readoutLine1,
  readoutLine2 = COPY_EN.readoutLine2,
}) => {
  return (
    <AbsoluteFill style={{ backgroundColor: BACKGROUND_COLOR }}>
      {/* Runs on the composition's own clock so the flicker never resets
          across the hard cuts between lines. */}
      <ShopLight
        minOpacity={SHOP_LIGHT_MIN_OPACITY}
        maxOpacity={SHOP_LIGHT_MAX_OPACITY}
      />

      <Sequence from={LINE_1_START} durationInFrames={LINE_1_END - LINE_1_START}>
        <AbsoluteFill style={centered}>
          <MarkerLine text={lines[0]} fontSize={LINE_FONT_SIZE} color={TEXT_COLOR} underlineColor={ACCENT_COLOR} />
        </AbsoluteFill>
      </Sequence>

      <Sequence from={LINE_2_START} durationInFrames={LINE_2_END - LINE_2_START}>
        <AbsoluteFill style={centered}>
          <MarkerLine text={lines[1]} fontSize={LINE_FONT_SIZE} color={TEXT_COLOR} underlineColor={ACCENT_COLOR} />
        </AbsoluteFill>
      </Sequence>

      <Sequence from={LINE_3_START} durationInFrames={LINE_3_END - LINE_3_START}>
        <AbsoluteFill style={centered}>
          <MarkerLine text={lines[2]} fontSize={LINE_FONT_SIZE} color={TEXT_COLOR} underlineColor={ACCENT_COLOR} />
        </AbsoluteFill>
      </Sequence>

      {/* The turn: no underline here, it doesn't need convincing — it's
          the one true thing so far. Slightly bigger, held longest. */}
      <Sequence from={LINE_4_START} durationInFrames={LINE_4_END - LINE_4_START}>
        <AbsoluteFill style={centered}>
          <MarkerLine
            text={lines[3]}
            fontSize={EMPHASIS_FONT_SIZE}
            color={ACCENT_COLOR}
            showUnderline={false}
          />
        </AbsoluteFill>
      </Sequence>

      <Sequence from={STAMP_START} durationInFrames={STAMP_END - STAMP_START}>
        <AbsoluteFill style={{ ...centered, flexDirection: "column", gap: 28 }}>
          <MarkerLine
            text={stampTitle}
            fontSize={STAMP_FONT_SIZE}
            color={TEXT_COLOR}
            underlineColor={ACCENT_COLOR}
          />
          <div style={{ fontFamily: MARKER_FONT_FAMILY, display: "flex", flexDirection: "column", gap: 4 }}>
            <MonoReadout text={readoutLine1} fontSize={READOUT_FONT_SIZE} color={ACCENT_COLOR} startFrame={14} showCursor={false} />
            <MonoReadout text={readoutLine2} fontSize={READOUT_FONT_SIZE} color={ACCENT_COLOR} startFrame={14 + readoutLine1.length} />
          </div>
        </AbsoluteFill>
      </Sequence>

      <Grain opacity={GRAIN_OPACITY} />
    </AbsoluteFill>
  );
};
