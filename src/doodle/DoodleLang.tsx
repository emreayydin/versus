import React from "react";
import { AbsoluteFill, Sequence, staticFile, useVideoConfig } from "remotion";
import { Audio } from "@remotion/media";
import { LangScene, Kapitelkarte } from "./LangScene";
import { PAPIER } from "./Figur";
import type { LangDaten } from "../types";

/**
 * Sammelfolge: mehrere Erklaerungen hintereinander, dazwischen je eine
 * Kapitelkarte.
 *
 * Warum ueberhaupt lang, wenn das Format aus dem Hochkantvideo kommt:
 * Shorts bringen Reichweite, aber kaum Wiedergabezeit - und die
 * Wiedergabezeit ist die Schwelle zur Monetarisierung. Eine Sammelfolge
 * aus sechs Kapiteln kommt ueber acht Minuten und kostet keine einzige
 * neue Zeile Skript: es sind dieselben Kapitel, die einzeln als Shorts
 * laufen.
 */

export const KARTE_SEKUNDEN = 2.4;

export const langFrames = (daten: LangDaten, fps: number) =>
  Math.ceil(
    daten.kapitel.reduce((s, k) => s + KARTE_SEKUNDEN + k.duration + 0.6, 0) * fps,
  );

export const DoodleLang: React.FC<{ daten: LangDaten }> = ({ daten }) => {
  const { fps } = useVideoConfig();
  let cursor = 0;

  return (
    <AbsoluteFill style={{ backgroundColor: PAPIER }}>
      {daten.kapitel.map((k, i) => {
        const karte = Math.round(KARTE_SEKUNDEN * fps);
        const inhalt = Math.round((k.duration + 0.6) * fps);
        const von = cursor;
        cursor += karte + inhalt;
        return (
          <React.Fragment key={i}>
            <Sequence from={von} durationInFrames={karte}>
              <Kapitelkarte nummer={i + 1} titel={k.ueberschrift} />
            </Sequence>
            <Sequence from={von + karte} durationInFrames={inhalt}>
              <Audio src={staticFile(k.audio)} />
              <LangScene
                ueberschrift={k.ueberschrift}
                groups={k.groups}
                bilder={k.bilder}
                words={k.words ?? []}
              />
            </Sequence>
          </React.Fragment>
        );
      })}

      {/* Musikbett laeuft durch, nicht je Kapitel neu */}
      <Audio src={staticFile("bett.wav")} volume={0.13} loop />

      {/* Der Kapitelzaehler stand hier frueher unten rechts und lief in
          den Untertitel hinein. Kleine Dauerbeschriftungen sind ein
          Muster aus Web-Oberflaechen; im Video kosten sie Ruhe und
          bringen nichts. Die Kapitelkarten zaehlen bereits mit. */}
    </AbsoluteFill>
  );
};
