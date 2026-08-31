/**
 * Kanalgrafiken fuer "The Difference".
 *
 * Das Zeichen ist ein geteilter Kreis: linke Haelfte gefuellt, rechte leer,
 * dazwischen eine Trennlinie. Das ist der Vergleich selbst als Form - zwei
 * Seiten, eine Grenze.
 *
 * Warum kein gezeichnetes Motiv: Das Profilbild wird neben Videos und
 * Kommentaren mit 98 Pixeln Kantenlaenge ausgeliefert. Alles mit Innenleben
 * wird dort zu Brei. Eine Form, die aus zwei Flaechen und einer Linie
 * besteht, bleibt auch als Daumennagel eindeutig.
 */

import React from "react";
import { AbsoluteFill } from "remotion";

const TINTE = "#111111";
const PAPIER = "#ffffff";

/** Geteilter Kreis: links voll, rechts leer. */
const Zeichen: React.FC<{ groesse: number; strich?: number }> = ({
  groesse,
  strich = Math.max(groesse * 0.055, 3),
}) => {
  const r = groesse / 2 - strich / 2;
  const m = groesse / 2;
  return (
    <svg width={groesse} height={groesse} viewBox={`0 0 ${groesse} ${groesse}`}>
      {/* linke Haelfte gefuellt */}
      <path
        d={`M ${m} ${m - r} A ${r} ${r} 0 0 0 ${m} ${m + r} Z`}
        fill={TINTE}
      />
      {/* Umriss */}
      <circle
        cx={m}
        cy={m}
        r={r}
        fill="none"
        stroke={TINTE}
        strokeWidth={strich}
      />
      {/* Trennlinie */}
      <line
        x1={m}
        y1={m - r}
        x2={m}
        y2={m + r}
        stroke={TINTE}
        strokeWidth={strich}
        strokeLinecap="round"
      />
    </svg>
  );
};

export const Avatar: React.FC = () => (
  <AbsoluteFill
    style={{
      background: PAPIER,
      alignItems: "center",
      justifyContent: "center",
    }}
  >
    {/*
      Bewusst nur 400 von 800 Pixeln: YouTube schlaegt beim Hochladen einen
      Zuschnitt vor, der bis an den Rand geht. Ein Zeichen, das die Flaeche
      fuellt, wird dabei oben und unten angeschnitten.
    */}
    <Zeichen groesse={400} />
  </AbsoluteFill>
);

export const Banner: React.FC = () => (
  <AbsoluteFill style={{ background: PAPIER }}>
    {/*
      Der sichere Bereich eines YouTube-Banners ist auf dem Handy nur
      1546x423 in der Mitte. Alles Wichtige gehoert dorthin, der Rest wird
      je nach Geraet abgeschnitten.
    */}
    <AbsoluteFill
      style={{
        alignItems: "center",
        justifyContent: "center",
        flexDirection: "row",
        gap: 70,
      }}
    >
      <Zeichen groesse={300} />
      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        <div
          style={{
            fontFamily: "Arial Black, Helvetica, sans-serif",
            fontSize: 150,
            lineHeight: 1,
            letterSpacing: -4,
            color: TINTE,
          }}
        >
          The Difference
        </div>
        <div
          style={{
            fontFamily: "Helvetica Neue, Helvetica, Arial, sans-serif",
            fontSize: 58,
            color: TINTE,
            opacity: 0.62,
          }}
        >
          Two things people confuse. Explained in a minute.
        </div>
      </div>
    </AbsoluteFill>
  </AbsoluteFill>
);
