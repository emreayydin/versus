import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { PAPIER, TINTE } from "./Figur";
import type { Group, Wort } from "../types";

/**
 * Wortgenaue Untertitel.
 *
 * Der wichtigste Zusatz im ganzen Format, und der billigste: edge-tts
 * liefert die Wort-Zeitstempel ohnehin mit, es muss nichts geschaetzt und
 * nichts nachtraeglich synchronisiert werden.
 *
 * Warum es sich lohnt: Shorts starten stumm. Wer nicht auf Ton tippt, sieht
 * ohne Untertitel eine Strichfigur, die nichts erklaert - und wischt weiter.
 *
 * Es laeuft immer ein kurzes Fenster von Woertern, nicht ein einzelnes:
 * Ein Wort allein zwingt zum Lesen im Takt der Stimme, eine ganze Zeile
 * laesst vorauslesen. Drei bis fuenf Woerter sind der Kompromiss, den auch
 * die Vorlage faehrt.
 */

const SANS = "'Arial Black', 'Helvetica Neue', sans-serif";
const FENSTER = 4;

export const Untertitel: React.FC<{
  words: Wort[];
  /** Sekunden, die schon gelaufen sind, wenn das Video spaeter einsetzt */
  versatz?: number;
  groesse: number;
  /** Mindestabstand zum Bildrand in Pixeln */
  rand?: number;
  /** Satzgrenzen. Ohne sie laeuft das Fenster ueber das Satzende hinaus. */
  saetze?: Group[];
  hell?: boolean;
}> = ({ words, versatz = 0, groesse, rand, saetze, hell = true }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps + versatz;

  if (!words.length) return null;

  // Nur Woerter des laufenden Satzes.
  //
  // Ohne das mischt das Fenster Satzenden mit Satzanfaengen: im Bild stand
  // "tausend Euro verzinst Sondern" - die ersten drei Woerter aus dem einen
  // Satz, das letzte aus dem naechsten. Beim Lesen ergibt das Unsinn.
  let vorrat = words;
  if (saetze?.length) {
    const g =
      [...saetze].reverse().find((x) => t >= x.start - 0.25) ?? saetze[0];
    const drin = words.filter((w) => w.start >= g.start - 0.25 && w.start <= g.end + 0.25);
    if (drin.length) vorrat = drin;
  }

  // Aktuelles Wort: das letzte, dessen Anfang schon vorbei ist.
  let i = 0;
  for (let k = 0; k < vorrat.length; k++) {
    if (t >= vorrat[k].start) i = k;
    else break;
  }

  // Das Fenster springt blockweise, nicht Wort fuer Wort - sonst wandert
  // die Zeile staendig und das Auge kommt nicht zur Ruhe.
  const block = Math.floor(i / FENSTER);
  const sicht = vorrat.slice(block * FENSTER, block * FENSTER + FENSTER);

  const auf = interpolate(t - vorrat[block * FENSTER].start, [0, 0.1], [0.4, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "center",
        alignItems: "center",
        gap: `${groesse * 0.18}px ${groesse * 0.26}px`,
        fontFamily: SANS,
        fontWeight: 900,
        fontSize: groesse,
        lineHeight: 1.12,
        opacity: auf,
        padding: `0 ${rand ?? groesse * 0.5}px`,
      }}
    >
      {sicht.map((w, k) => {
        const aktiv = vorrat[i] === w;
        return (
          <span
            key={`${w.start}-${k}`}
            style={{
              // Der Kasten muss gegen den UNTERGRUND stehen, nicht gegen
              // die Schrift: auf Papier ein schwarzer Kasten mit hellem
              // Wort, auf Schwarz umgekehrt. Vorher war der Kasten auf
              // hellem Grund papierfarben - also unsichtbar.
              color: aktiv ? (hell ? TINTE : PAPIER) : hell ? PAPIER : TINTE,
              backgroundColor: aktiv ? (hell ? PAPIER : TINTE) : "transparent",
              borderRadius: groesse * 0.14,
              padding: aktiv ? `${groesse * 0.04}px ${groesse * 0.14}px` : 0,
              // Ohne den Rahmen springt die Zeile in dem Moment, in dem ein
              // Wort seinen Kasten bekommt.
              outline: aktiv ? "none" : `${groesse * 0.14}px solid transparent`,
            }}
          >
            {w.word}
          </span>
        );
      })}
    </div>
  );
};
