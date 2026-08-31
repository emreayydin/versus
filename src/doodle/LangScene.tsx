import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { Figur, PAPIER, TINTE } from "./Figur";
import { Icon } from "./Icon";
import { Untertitel } from "./Untertitel";
import { Zahl, istBetrag } from "./Zahl";
import { Diagramm } from "./Diagramm";
import type { Bild, Group, Wort } from "../types";

/**
 * Querformat-Fassung eines Kapitels.
 *
 * Kein Briefkasten wie im Hochformat: Die schwarzen Balken dort sind eine
 * Konvention von TikTok und Shorts, wo die Bedienleiste Platz frisst. Auf
 * einem 16:9-Bildschirm waeren sie nur verschenkte Flaeche.
 *
 * AUFBAU ALS SPALTE, NICHT MIT FESTEN ABSTAENDEN
 * Kopf, Zeichnung und Untertitel liegen in einem Flex-Container
 * untereinander. Vorher stand jedes Stueck mit eigenem "top" im Bild -
 * und sobald eine Ueberschrift zweizeilig wurde, lief sie in den
 * Trennstrich und in die Figur hinein. Mit Spalten kann das nicht
 * passieren: Jedes Element hat seinen Platz, und der waechst mit.
 *
 * Die linke Spalte fuer Symbol und Wort bleibt auch dann stehen, wenn
 * beides fehlt. Sonst springt die Figur bei jedem Szenenwechsel in die
 * Mitte und wieder zurueck.
 */

const SANS = "'Arial Black', 'Helvetica Neue', sans-serif";

export const LangScene: React.FC<{
  ueberschrift: string;
  groups: Group[];
  bilder: Bild[];
  words?: Wort[];
}> = ({ ueberschrift, groups, bilder, words = [] }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = frame / fps;

  const i = groups.reduce((acc, g, idx) => (t >= g.start - 0.2 ? idx : acc), 0);
  const bild = bilder[Math.min(i, bilder.length - 1)];
  const ab = Math.max(0, (groups[i]?.start ?? 0) - 0.2);
  const seit = t - ab;

  const klemmen = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
  const zeichnen = interpolate(seit, [0, 0.55], [0, 1], klemmen);
  const zeichnenIcon = interpolate(seit, [0.15, 0.7], [0, 1], klemmen);
  const auf = interpolate(seit, [0.45, 0.62], [0, 1], klemmen);

  // Sicherer Rand: die Layout-Regel verlangt 80 px bei 1080 Breite,
  // mitskaliert sind das hier 142 px.
  const rand = width * 0.08;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: PAPIER,
        display: "flex",
        flexDirection: "column",
        padding: `${height * 0.075}px ${rand}px ${height * 0.06}px`,
        gap: height * 0.03,
      }}
    >
      {/* Kopf: Ueberschrift und Strich gehoeren zusammen und wachsen
          gemeinsam, wenn die Ueberschrift zweizeilig wird. */}
      <div style={{ display: "flex", flexDirection: "column",
                    alignItems: "center", gap: height * 0.028 }}>
        <div
          style={{
            textAlign: "center",
            fontFamily: SANS,
            fontWeight: 900,
            fontSize: height * 0.082,
            lineHeight: 1.12,
            color: TINTE,
            letterSpacing: "-0.01em",
          }}
        >
          {ueberschrift}
        </div>
        <div style={{ width: width * 0.11, height: 7, borderRadius: 4,
                      backgroundColor: TINTE, opacity: 0.85 }} />
      </div>

      {/* Zeichnung: nimmt den Platz, der uebrig bleibt.
          Ein Diagramm bekommt die ganze Buehne - siehe DoodleScene. */}
      {bild.diagramm ? (
        <div style={{ flex: 1, display: "flex", alignItems: "center",
                      justifyContent: "center", minHeight: 0 }}>
          <div style={{ height: "100%", aspectRatio: "4 / 3" }}>
            <Diagramm daten={bild.diagramm} zeichnen={zeichnen} />
          </div>
        </div>
      ) : (
      <div style={{ flex: 1, display: "flex", alignItems: "center",
                    justifyContent: "center", gap: width * 0.04, minHeight: 0 }}>
        <div style={{ width: width * 0.20, display: "flex", flexDirection: "column",
                      alignItems: "center", justifyContent: "center",
                      gap: height * 0.04, flexShrink: 0 }}>
          {bild.icon ? (
            <div style={{ width: height * 0.24, height: height * 0.24 }}>
              <Icon name={bild.icon} zeichnen={zeichnenIcon} />
            </div>
          ) : null}
          {bild.wort ? (
            <div style={{ fontFamily: SANS, fontWeight: 900,
                          fontSize: height * (bild.wort.length > 8 ? 0.062 : 0.088),
                          color: TINTE, whiteSpace: "nowrap", opacity: auf }}>
              {istBetrag(bild.wort) ? <Zahl wort={bild.wort} ab={ab} /> : bild.wort}
            </div>
          ) : null}
        </div>

        <div style={{ height: "100%", aspectRatio: "200 / 300", flexShrink: 0 }}>
          <Figur pose={bild.pose} haare={bild.haare}
                 stimmung={bild.stimmung} zeichnen={zeichnen} />
        </div>

        {/* Gegengewicht: haelt die Figur mittig, auch wenn links etwas steht */}
        <div style={{ width: width * 0.20, flexShrink: 0 }} />
      </div>
      )}

      <div style={{ display: "flex", justifyContent: "center" }}>
        <Untertitel words={words} groesse={height * 0.074} rand={0}
                    saetze={groups} hell={false} />
      </div>
    </AbsoluteFill>
  );
};

/** Karte zwischen den Kapiteln: Nummer und Thema, sonst nichts. */
export const Kapitelkarte: React.FC<{ nummer: number; titel: string }> = ({
  nummer,
  titel,
}) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const auf = interpolate(frame / fps, [0, 0.35], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill
      style={{
        backgroundColor: PAPIER,
        alignItems: "center",
        justifyContent: "center",
        flexDirection: "column",
        gap: height * 0.045,
        padding: `0 ${width * 0.08}px`,
        opacity: auf,
      }}
    >
      <div style={{ fontFamily: SANS, fontWeight: 900, fontSize: height * 0.22,
                    color: TINTE, lineHeight: 1 }}>
        {nummer}
      </div>
      <div style={{ fontFamily: SANS, fontWeight: 900, fontSize: height * 0.082,
                    color: TINTE, textAlign: "center", lineHeight: 1.12 }}>
        {titel}
      </div>
    </AbsoluteFill>
  );
};
