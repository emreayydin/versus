import React from "react";
import { AbsoluteFill } from "remotion";
import { Figur, PAPIER, TINTE } from "./doodle/Figur";
import { Icon, type IconName } from "./doodle/Icon";

/**
 * Thumbnail 1280x720.
 *
 * Ohne eigenes Thumbnail greift sich YouTube ein Einzelbild aus dem
 * Video - bei diesem Format oft eine halb gezeichnete Figur mit leerem
 * Papier drumherum. Ein zufaelliger Frame ist garantiert schlechter als
 * ein gestalteter, und die Klickrate haengt an nichts so sehr wie hieran.
 *
 * Regeln, die hier gelten und im Video nicht:
 *   - In der YouTube-Uebersicht ist das Bild oft nur 210 px breit. Alles
 *     muss bei einem Sechstel der Groesse noch lesbar sein, also sehr
 *     wenige, sehr grosse Woerter.
 *   - Der Text wiederholt NICHT den Titel. Er steht daneben und ergaenzt
 *     ihn - sonst liest man dasselbe zweimal.
 *   - Kein Aufregungs-Rot, keine Pfeile, kein aufgerissener Mund. Der
 *     Kanal verspricht Erklaerung, das Thumbnail muss das halten.
 */

const SANS = "'Arial Black', 'Helvetica Neue', sans-serif";

export type ThumbProps = {
  /** Zwei bis vier Woerter. Nicht der Titel. */
  zeile: string;
  /** Der Zahlenwert, um den es geht - optional, aber stark */
  zahl?: string;
  icon?: IconName;
};

export const Thumbnail: React.FC<ThumbProps> = ({ zeile, zahl, icon }) => {
  // Bei wenigen, kurzen Woertern darf die Schrift sehr gross werden.
  const groesse = zeile.length <= 14 ? 128 : zeile.length <= 24 ? 104 : 82;

  return (
    <AbsoluteFill style={{ backgroundColor: PAPIER, flexDirection: "row" }}>
      {/* Linke Spalte: die Aussage */}
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          gap: 24,
          padding: "0 0 0 62px", minWidth: 0,
        }}
      >
        <div
          style={{
            fontFamily: SANS, fontWeight: 900, fontSize: groesse,
            lineHeight: 1.04, color: TINTE, letterSpacing: "-0.02em",
          }}
        >
          {zeile}
        </div>
        {zahl ? (
          <div
            style={{
              fontFamily: SANS, fontWeight: 900, fontSize: 96,
              color: PAPIER, backgroundColor: TINTE,
              padding: "6px 26px", borderRadius: 16, alignSelf: "flex-start",
            }}
          >
            {zahl}
          </div>
        ) : null}
      </div>

      {/* Rechte Spalte: Figur, darueber das Symbol */}
      <div
        style={{
          width: 520,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 0,
          paddingRight: 30,
        }}
      >
        {icon ? (
          <div style={{ width: 240, height: 240, marginBottom: 140 }}>
            <Icon name={icon} />
          </div>
        ) : null}
        <div style={{ width: 330, height: 495 }}>
          <Figur pose="zeigen" stimmung={0.6} strich={9} />
        </div>
      </div>

      {/* Absender unten links - klein, es soll nicht mitlesen */}
      <div
        style={{
          position: "absolute", left: 62, bottom: 34,
          fontFamily: SANS, fontWeight: 900, fontSize: 30,
          color: TINTE, opacity: 0.45,
        }}
      >
        Strichrechnung
      </div>
    </AbsoluteFill>
  );
};
