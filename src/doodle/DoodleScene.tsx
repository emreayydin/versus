import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { Figur, PAPIER, TINTE } from "./Figur";
import { Icon } from "./Icon";
import { Untertitel } from "./Untertitel";
import { Zahl, istBetrag } from "./Zahl";
import { Diagramm } from "./Diagramm";
import type { Bild, Group, Pose, Wort } from "../types";

/**
 * Hochformat im Stil der Vorlage: schwarze Balken oben und unten,
 * dazwischen ein Papierband mit der Zeichnung, darueber ein weisser Kasten
 * mit der Ueberschrift.
 *
 * Die Ueberschrift steht das GANZE Video ueber - sie ist der Aufhaenger,
 * der jemanden beim Durchscrollen anhaelt.
 *
 * Der untere schwarze Balken war anfangs leer. Dort stehen jetzt die
 * Untertitel: die Flaeche war ohnehin da, und Shorts starten stumm.
 */

const BAND_OBEN = 0.332;
const BAND_UNTEN = 0.670;
const KASTEN_OBEN = 0.112;

export type Szene = Bild & { ab: number };

export const DoodleScene: React.FC<{
  ueberschrift: string;
  szenen: Szene[];
  words?: Wort[];
  saetze?: Group[];
  versatz?: number;
}> = ({ ueberschrift, szenen, words = [], saetze, versatz = 0 }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  const t = frame / fps;

  const bandY = height * BAND_OBEN;
  const bandH = height * (BAND_UNTEN - BAND_OBEN);

  // Die Ueberschrift darf nie ins Papierband ragen. Eine feste
  // Schriftgroesse schafft das nicht: bei 87 px passen rund 16 Zeichen in
  // eine Zeile, eine Ueberschrift mit 43 Zeichen braucht also drei - und
  // die naechste mit 55 Zeichen vier, und dann sitzt sie im Bild.
  // Deshalb die groesste Groesse aus einer Leiter, die noch passt.
  const KASTEN_PAD = width * 0.028;
  const platz = height * (BAND_OBEN - KASTEN_OBEN) - height * 0.014;
  const passendeGroesse = (text: string) => {
    const innen = width * 0.84 - 2 * width * 0.035;
    for (const anteil of [0.081, 0.072, 0.064, 0.057]) {
      const size = width * anteil;
      const proZeile = Math.max(1, Math.floor(innen / (size * 0.62)));
      const zeilen = Math.ceil(text.length / proZeile);
      if (zeilen * size * 1.14 + 2 * KASTEN_PAD <= platz) return size;
    }
    return width * 0.057;
  };
  const kopfGroesse = passendeGroesse(ueberschrift);

  const aktiv = [...szenen].reverse().find((s) => t >= s.ab) ?? szenen[0];
  const seitAn = t - aktiv.ab;

  // Statt hartem Schnitt: die Zeichnung entsteht. 0,55 s ist der Wert,
  // bei dem man den Strich noch laufen sieht, die Figur aber lange vor
  // dem Ende des Satzes fertig dasteht.
  const zeichnen = interpolate(seitAn, [0, 0.55], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  // Das Symbol beginnt einen Tick spaeter - zwei Dinge, die exakt
  // gleichzeitig entstehen, liest das Auge als ein Aufblenden.
  const zeichnenIcon = interpolate(seitAn, [0.15, 0.7], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const auf = interpolate(seitAn, [0.45, 0.62], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  // Ein Diagramm traegt die Aussage allein. Figur und Symbol daneben
  // waeren Konkurrenz um denselben Blick - die Layout-Regel sagt: zwei
  // gleichwertige Dinge nicht nebeneinander, sondern nacheinander.
  const hatSeite = Boolean(aktiv.wort || aktiv.icon) && !aktiv.diagramm;

  return (
    <AbsoluteFill style={{ backgroundColor: "#000000" }}>
      <div
        style={{
          position: "absolute", top: bandY, left: 0,
          width, height: bandH, backgroundColor: PAPIER, overflow: "hidden",
        }}
      >
        {aktiv.diagramm ? (
          <div
            style={{
              position: "absolute",
              left: "50%",
              top: "50%",
              translate: "-50% -50%",
              width: width * 0.84,
              height: bandH * 0.86,
            }}
          >
            <Diagramm daten={aktiv.diagramm} zeichnen={zeichnen} />
          </div>
        ) : (
        <div
          style={{
            position: "absolute",
            // Steht links ein Wort, rueckt die Figur nach rechts - sonst
            // ueberschneiden sich Schrift und Beine.
            left: hatSeite ? "66%" : "50%",
            top: "50%",
            translate: "-50% -50%",
            height: bandH * 0.90,
            width: bandH * 0.90 * (200 / 300),
          }}
        >
          <Figur
            pose={aktiv.pose as Pose}
            haare={aktiv.haare}
            stimmung={aktiv.stimmung}
            zeichnen={zeichnen}
          />
        </div>
        )}

        {/* Symbol und Wort teilen sich die linke Spalte */}
        {hatSeite ? (
          <div
            style={{
              position: "absolute",
              // 80 px Mindestabstand zum Rand, wie bei der Ueberschrift.
              // Vorher klebte ein langer Betrag am Bildrand.
              left: width * 0.075,
              top: "50%",
              translate: "0 -50%",
              width: width * 0.28,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: bandH * 0.05,
            }}
          >
            {aktiv.icon ? (
              <div style={{ width: bandH * 0.34, height: bandH * 0.34 }}>
                <Icon name={aktiv.icon} zeichnen={zeichnenIcon} />
              </div>
            ) : null}
            {aktiv.wort ? (
              <div
                style={{
                  fontFamily: "'Arial Black', 'Helvetica Neue', sans-serif",
                  fontWeight: 900,
                  fontSize: bandH * (aktiv.wort.length > 8 ? 0.11 : 0.15),
                  color: TINTE,
                  textAlign: "center",
                  whiteSpace: "nowrap",
                  opacity: auf,
                }}
              >
                {istBetrag(aktiv.wort)
                  ? <Zahl wort={aktiv.wort} ab={aktiv.ab} />
                  : aktiv.wort}
              </div>
            ) : null}
          </div>
        ) : null}
      </div>

      {/* Ueberschrift.
          Randabstand und Schriftgroesse folgen den Video-Layout-Regeln:
          Text mindestens 80 px vom Rand, Hauptueberschrift mindestens
          84 px bei 1080 px Breite. Vorher waren es 59 px und 66 px - auf
          dem Handy lesbar, aber unnoetig knapp. */}
      <div
        style={{
          position: "absolute",
          top: height * KASTEN_OBEN,
          left: width * 0.080,
          width: width * 0.84,
          backgroundColor: "#FFFFFF",
          borderRadius: width * 0.022,
          padding: `${KASTEN_PAD}px ${width * 0.035}px`,
          fontFamily: "'Arial Black', 'Helvetica Neue', sans-serif",
          fontWeight: 900,
          // Notbremse: Der Generator begrenzt die Ueberschrift auf 48
          // Zeichen, aber eine aeltere Folge oder ein durchgerutschter
          // Fall darf das Bild nicht sprengen. Ab 48 Zeichen schrumpft
          // die Schrift so weit, dass der Kasten im schwarzen Balken
          // bleibt - lieber etwas kleiner als ueber der Zeichnung.
          fontSize: kopfGroesse,
          lineHeight: 1.14,
          color: "#111111",
          textAlign: "center",
        }}
      >
        {ueberschrift}
      </div>

      {/* Untertitel im unteren Balken - die Flaeche war vorher leer */}
      <div
        style={{
          position: "absolute",
          top: height * (BAND_UNTEN + 0.035),
          left: 0,
          width,
          height: height * 0.20,
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "center",
        }}
      >
        <Untertitel words={words} versatz={versatz} groesse={width * 0.058} rand={width * 0.080} saetze={saetze} hell />
      </div>
    </AbsoluteFill>
  );
};
