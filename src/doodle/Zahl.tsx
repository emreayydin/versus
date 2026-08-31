import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";

/**
 * Betraege zaehlen hoch statt einfach dazustehen.
 *
 * Bei Zinseszins und Gebuehren ist die Zahl das Argument. Eine Zahl, die
 * hochlaeuft, zeigt die Bewegung, um die es im Satz geht - ein stehender
 * Wert zeigt nur das Ergebnis.
 *
 * Greift nur, wenn das Wort wirklich ein Betrag ist. "SCHULDEN" bleibt
 * "SCHULDEN".
 */

const BETRAG = /^([\d.]+)\s*(€|%|Euro|Prozent)$/;

export const istBetrag = (wort: string) => BETRAG.test(wort.trim());

export const Zahl: React.FC<{ wort: string; ab: number }> = ({ wort, ab }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const treffer = wort.trim().match(BETRAG);
  if (!treffer) return <>{wort}</>;

  const ziel = parseFloat(treffer[1].replace(/\./g, ""));
  const einheit = treffer[2];
  const t = frame / fps - ab;

  // 0,7 s: lang genug, dass man das Laufen sieht, kurz genug, dass der
  // Endwert steht, bevor der Satz weitergeht.
  const wert = interpolate(t, [0, 0.7], [0, ziel], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const gerundet = Math.round(wert);
  const formatiert = ziel >= 1000 ? gerundet.toLocaleString("de-DE") : String(gerundet);

  return <>{formatiert} {einheit}</>;
};
