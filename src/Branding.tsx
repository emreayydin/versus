import React from "react";
import { AbsoluteFill } from "remotion";
import { PAPIER, TINTE } from "./doodle/Figur";

/**
 * Kanalgrafiken, im selben Stil wie die Videos.
 *
 * Das Zeichen ist eine Strichliste: vier senkrechte Striche, der fuenfte
 * quer. Das ist woertlich das, was der Name sagt, es ist mit demselben
 * Pinsel gezeichnet wie die Figuren, und es bleibt als 48 Pixel grosses
 * Profilbild noch erkennbar - anders als eine Strichfigur, die in dieser
 * Groesse zu einem Fleck wird.
 */

const STRICH = 26;

/** Vier senkrechte Striche, der fuenfte quer darueber. */
const Strichliste: React.FC<{ breite: number; hoehe: number }> = ({ breite, hoehe }) => {
  const abstand = breite / 4.6;
  const x0 = (breite - abstand * 3) / 2;
  return (
    <svg viewBox={`0 0 ${breite} ${hoehe}`} width="100%" height="100%">
      {[0, 1, 2, 3].map((i) => (
        <line
          key={i}
          x1={x0 + i * abstand}
          y1={hoehe * 0.12}
          x2={x0 + i * abstand}
          y2={hoehe * 0.88}
          stroke={TINTE}
          strokeWidth={STRICH}
          strokeLinecap="round"
        />
      ))}
      <line
        x1={x0 - abstand * 0.42}
        y1={hoehe * 0.86}
        x2={x0 + abstand * 3.42}
        y2={hoehe * 0.14}
        stroke={TINTE}
        strokeWidth={STRICH}
        strokeLinecap="round"
      />
    </svg>
  );
};

export const Avatar: React.FC = () => (
  <AbsoluteFill
    style={{
      backgroundColor: PAPIER,
      alignItems: "center",
      justifyContent: "center",
    }}
  >
    <div style={{ width: "62%", height: "52%" }}>
      <Strichliste breite={500} hoehe={420} />
    </div>
  </AbsoluteFill>
);

/**
 * Banner 2560x1440. YouTube zeigt auf dem Handy nur die mittleren
 * 1546x423 - alles Wichtige muss da hinein, sonst ist es dort abgeschnitten.
 */
export const Banner: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: PAPIER }}>
    <div
      style={{
        position: "absolute",
        left: "50%",
        top: "50%",
        translate: "-50% -50%",
        width: 1546,
        height: 423,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 64,
      }}
    >
      <div style={{ width: 260, height: 210, flexShrink: 0 }}>
        <Strichliste breite={500} hoehe={420} />
      </div>
      <div>
        <div
          style={{
            fontFamily: "'Arial Black', 'Helvetica Neue', sans-serif",
            fontWeight: 900,
            fontSize: 132,
            letterSpacing: "-0.02em",
            color: TINTE,
            lineHeight: 1,
          }}
        >
          Strichrechnung
        </div>
        <div
          style={{
            marginTop: 26,
            fontFamily: "'Helvetica Neue', Arial, sans-serif",
            fontWeight: 500,
            fontSize: 52,
            color: TINTE,
            opacity: 0.72,
          }}
        >
          Geld erklärt. Nicht empfohlen.
        </div>
      </div>
    </div>
  </AbsoluteFill>
);
