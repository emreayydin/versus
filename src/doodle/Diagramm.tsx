import React from "react";
import { TINTE } from "./Figur";
import type { DiagrammDaten } from "../types";

/**
 * Echte Diagramme in Tinte.
 *
 * Bis hierher hatte der Kanal fuer einen Finanzkanal kein einziges
 * Diagramm - nur ein allgemeines Kurven-Symbol ohne die Zahlen aus dem
 * Skript. Wenn die Stimme "aus tausend Euro werden nach dreissig Jahren
 * viertausenddreihundert" sagt, soll die Kurve genau das zeigen.
 *
 * Regeln aus der Datenvisualisierungs-Skill, soweit sie auf ein
 * monochromes Video zutreffen:
 *   - Zeitverlauf -> Linie, Vergleich -> Balken, Einzelwert -> Zahl.
 *   - Achsen und Raster treten zurueck: duenner und blasser als die Daten.
 *   - Nur ausgewaehlte Beschriftungen. Eine Zahl an jedem Punkt liest
 *     niemand, und im Video schon gar nicht.
 *   - Eine Datenreihe braucht keine Legende - die Ueberschrift benennt sie.
 *   - Runde Enden, wie bei allen Strichen in diesem Kanal.
 */

const SANS = "'Arial Black', 'Helvetica Neue', sans-serif";
const klemm = (x: number) => Math.max(0, Math.min(1, x));

const fmt = (n: number, einheit?: string) => {
  const z = n >= 1000 ? Math.round(n).toLocaleString("de-DE") : String(Math.round(n));
  return einheit ? `${z} ${einheit}` : z;
};

export const Diagramm: React.FC<{
  daten: DiagrammDaten;
  /** 0 = leeres Blatt, 1 = fertig gezeichnet */
  zeichnen?: number;
}> = ({ daten, zeichnen = 1 }) => {
  const p = klemm(zeichnen);
  const W = 400;
  const H = 300;
  const L = 46;          // Platz links fuer die Achse
  const U = 244;         // Grundlinie
  const R = 372;

  const werte = daten.werte.length ? daten.werte : [0, 1];
  const max = Math.max(...werte, 1);

  // Achsen: duenner und blasser als die Daten. Sie sind Kulisse.
  const achse = {
    stroke: TINTE, strokeWidth: 4, strokeLinecap: "round" as const,
    fill: "none", opacity: 0.42,
  };
  const mark = {
    stroke: TINTE, strokeWidth: 8, strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const, fill: "none",
  };

  if (daten.art === "balken") {
    const n = werte.length;
    const luecke = 22;
    const breite = Math.min(74, (R - L - luecke * (n - 1)) / n);
    const gesamt = breite * n + luecke * (n - 1);
    const x0 = L + (R - L - gesamt) / 2;

    return (
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" height="100%">
        <path d={`M ${L - 8} ${U} H ${R}`} {...achse} />
        {werte.map((v, i) => {
          // Balken wachsen nacheinander, nicht alle zugleich - so liest
          // man den Vergleich, statt ihn nur zu sehen.
          const eigen = klemm((p - i * 0.16) / 0.5);
          const h = (v / max) * (U - 62) * eigen;
          const x = x0 + i * (breite + luecke);
          return (
            <g key={i}>
              <rect x={x} y={U - h} width={breite} height={h} rx={7} fill={TINTE} />
              {eigen > 0.85 && (
                <text x={x + breite / 2} y={U - h - 14} textAnchor="middle"
                      fontFamily={SANS} fontWeight={900} fontSize={25} fill={TINTE}>
                  {fmt(v, daten.einheit)}
                </text>
              )}
              {daten.achse?.[i] && (
                <text x={x + breite / 2} y={U + 32} textAnchor="middle"
                      fontFamily={SANS} fontWeight={900} fontSize={22}
                      fill={TINTE} opacity={0.62}>
                  {daten.achse[i]}
                </text>
              )}
            </g>
          );
        })}
      </svg>
    );
  }

  // Linie: Verlauf ueber die Zeit
  const punkte = werte.map((v, i) => {
    const x = L + (i / Math.max(1, werte.length - 1)) * (R - L);
    const y = U - (v / max) * (U - 62);
    return [x, y] as const;
  });
  const d = punkte.map(([x, y], i) => `${i ? "L" : "M"} ${x} ${y}`).join(" ");
  const [ex, ey] = punkte[punkte.length - 1];
  const fertig = p > 0.92;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" height="100%">
      <path d={`M ${L} 46 V ${U} H ${R}`} {...achse} />
      <path d={d} {...mark} pathLength={1} strokeDasharray={1} strokeDashoffset={1 - p} />

      {/* Nur der Endwert wird beschriftet. Er ist die Aussage. */}
      {fertig && (
        <>
          <circle cx={ex} cy={ey} r={9} fill={TINTE} />
          <text x={ex} y={ey - 22} textAnchor="end" fontFamily={SANS}
                fontWeight={900} fontSize={27} fill={TINTE}>
            {fmt(werte[werte.length - 1], daten.einheit)}
          </text>
        </>
      )}
      {daten.achse?.[0] && (
        <text x={L} y={U + 32} textAnchor="start" fontFamily={SANS}
              fontWeight={900} fontSize={22} fill={TINTE} opacity={0.62}>
          {daten.achse[0]}
        </text>
      )}
      {daten.achse?.[1] && (
        <text x={R} y={U + 32} textAnchor="end" fontFamily={SANS}
              fontWeight={900} fontSize={22} fill={TINTE} opacity={0.62}>
          {daten.achse[1]}
        </text>
      )}
    </svg>
  );
};
