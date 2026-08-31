import { Composition } from "remotion";
import { DoodleEpisode } from "./doodle/DoodleEpisode";
import { Avatar, Banner } from "./Branding";
import { Thumbnail } from "./Thumbnail";
import thumb from "./data/thumb.json";
import { DoodleLang, langFrames } from "./doodle/DoodleLang";
import lang from "./data/lang.json";
import voice from "./data/voice.json";
import plan from "./data/plan.json";
import type { LangDaten, Plan, VoiceData } from "./types";

const FPS = 30;

/**
 * Eine einzige Komposition.
 *
 * Anders als bei Lino stehen die Folgendaten nicht im Code: make_episode.py
 * schreibt vor jedem Render voice.json und plan.json neu. Eine neue Folge
 * aendert also keine einzige Zeile TypeScript.
 */
export const RemotionRoot: React.FC = () => {
  const data = voice as unknown as VoiceData;
  const p = plan as unknown as Plan;

  return (
    <>
    <Composition
      id="Doodle"
      component={DoodleEpisode}
      defaultProps={{ data, plan: p, audio: "voice.mp3" }}
      // Eine knappe Sekunde Nachlauf, damit das letzte Wort nicht abreisst.
      durationInFrames={Math.ceil((data.duration + 0.9) * FPS)}
      fps={FPS}
      width={1080}
      height={1920}
    />

    {/* Sammelfolge im Querformat */}
    <Composition
      id="DoodleLang"
      component={DoodleLang}
      defaultProps={{ daten: lang as unknown as LangDaten }}
      durationInFrames={langFrames(lang as unknown as LangDaten, FPS)}
      fps={FPS}
      width={1920}
      height={1080}
    />

    {/* Thumbnail - als Still rendern */}
    <Composition
      id="Thumbnail"
      component={Thumbnail}
      defaultProps={thumb as { zeile: string; zahl?: string }}
      durationInFrames={1}
      fps={FPS}
      width={1280}
      height={720}
    />

    {/* Kanalgrafiken - als Still rendern, nicht als Video */}
    <Composition id="Avatar" component={Avatar}
      durationInFrames={1} fps={FPS} width={800} height={800} />
    <Composition id="Banner" component={Banner}
      durationInFrames={1} fps={FPS} width={2560} height={1440} />
    </>
  );
};
