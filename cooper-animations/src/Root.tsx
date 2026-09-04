import "./index.css";
import { Composition } from "remotion";
import { HelloWorld } from "./HelloWorld";
import { Logo } from "./HelloWorld/Logo";
import { DayOne } from "./DayOne";
import {
  COPY_DE as DAY_ONE_COPY_DE,
  COPY_EN as DAY_ONE_COPY_EN,
  DURATION_IN_FRAMES as DAY_ONE_DURATION_IN_FRAMES,
} from "./DayOne/constants";
import { ExpectationReality } from "./ExpectationReality";
import {
  COPY_DE as ER_COPY_DE,
  COPY_EN as ER_COPY_EN,
  DURATION_IN_FRAMES as ER_DURATION_IN_FRAMES,
} from "./ExpectationReality/constants";
import { PorscheHook } from "./PorscheHook";
import {
  COPY_DE,
  COPY_EN,
  DURATION_IN_FRAMES,
  FPS,
  HEIGHT,
  WIDTH,
} from "./PorscheHook/constants";

// Each <Composition> is an entry in the sidebar!

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* Vertical short-form hook: npx remotion render PorscheHook */}
      <Composition
        id="PorscheHook"
        component={PorscheHook}
        durationInFrames={DURATION_IN_FRAMES}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
        defaultProps={{
          headlineText: COPY_EN.headline,
          sublineText: COPY_EN.subline,
          headlineFontSize: COPY_EN.headlineFontSize,
        }}
      />

      {/* Season 1 series identity, not a hook: npx remotion render DayOne */}
      <Composition
        id="DayOne"
        component={DayOne}
        durationInFrames={DAY_ONE_DURATION_IN_FRAMES}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
        defaultProps={{
          lines: DAY_ONE_COPY_EN.lines,
          stampTitle: DAY_ONE_COPY_EN.stampTitle,
          readoutLine1: DAY_ONE_COPY_EN.readoutLine1,
          readoutLine2: DAY_ONE_COPY_EN.readoutLine2,
        }}
      />

      <Composition
        id="DayOneDE"
        component={DayOne}
        durationInFrames={DAY_ONE_DURATION_IN_FRAMES}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
        defaultProps={{
          lines: DAY_ONE_COPY_DE.lines,
          stampTitle: DAY_ONE_COPY_DE.stampTitle,
          readoutLine1: DAY_ONE_COPY_DE.readoutLine1,
          readoutLine2: DAY_ONE_COPY_DE.readoutLine2,
        }}
      />

      {/* Two-card hook: npx remotion render ExpectationReality */}
      <Composition
        id="ExpectationReality"
        component={ExpectationReality}
        durationInFrames={ER_DURATION_IN_FRAMES}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
        defaultProps={{
          cardOneText: ER_COPY_EN.cardOne,
          cardTwoText: ER_COPY_EN.cardTwo,
          fontSize: ER_COPY_EN.fontSize,
        }}
      />

      <Composition
        id="ExpectationRealityDE"
        component={ExpectationReality}
        durationInFrames={ER_DURATION_IN_FRAMES}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
        defaultProps={{
          cardOneText: ER_COPY_DE.cardOne,
          cardTwoText: ER_COPY_DE.cardTwo,
          fontSize: ER_COPY_DE.fontSize,
        }}
      />

      {/* German cut: npx remotion render PorscheHookDE */}
      <Composition
        id="PorscheHookDE"
        component={PorscheHook}
        durationInFrames={DURATION_IN_FRAMES}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
        defaultProps={{
          headlineText: COPY_DE.headline,
          sublineText: COPY_DE.subline,
          headlineFontSize: COPY_DE.headlineFontSize,
        }}
      />

      <Composition
        // You can take the "id" to render a video:
        // npx remotion render HelloWorld
        id="HelloWorld"
        component={HelloWorld}
        durationInFrames={150}
        fps={30}
        width={1920}
        height={1080}
        // You can override these props for each render:
        // https://www.remotion.dev/docs/parametrized-rendering
        defaultProps={{
          titleText: "Welcome to Remotion",
          titleColor: "#000000",
          logoColor1: "#91EAE4",
          logoColor2: "#86A8E7",
        }}
      />

      {/* Mount any React component to make it show up in the sidebar and work on it individually! */}
      <Composition
        id="OnlyLogo"
        component={Logo}
        durationInFrames={150}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          logoColor1: "#91dAE2",
          logoColor2: "#86A8E7",
        }}
      />
    </>
  );
};
