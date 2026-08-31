import React from "react";
import { AbsoluteFill, staticFile } from "remotion";
import { Audio } from "@remotion/media";
import { DoodleScene, type Szene } from "./DoodleScene";
import type { Plan, VoiceData } from "../types";

/**
 * Eine Folge: Ueberschrift, Sprecherstimme, je Satz eine Zeichnung.
 *
 * Die Szenenwechsel haengen an den Satzgrenzen der Sprachspur. Damit passt
 * das Bild immer zum gesprochenen Satz, egal wie schnell die Stimme ist -
 * keine handgezaehlten Sekunden, die bei der naechsten Folge nicht mehr
 * stimmen.
 */
export const DoodleEpisode: React.FC<{
  data: VoiceData;
  plan: Plan;
  audio: string;
}> = ({ data, plan, audio }) => {
  const szenen: Szene[] = data.groups.map((g, i) => {
    const b = plan.bilder[Math.min(i, plan.bilder.length - 1)];
    // 0.2 s Vorlauf: das Bild steht, bevor der Satz beginnt.
    return { ab: Math.max(0, g.start - 0.2), ...b };
  });

  return (
    <AbsoluteFill>
      <Audio src={staticFile(audio)} />
      <Audio src={staticFile("bett.wav")} volume={0.16} loop />
      <DoodleScene
        ueberschrift={plan.ueberschrift}
        szenen={szenen}
        words={data.words ?? []}
        saetze={data.groups}
      />
    </AbsoluteFill>
  );
};
