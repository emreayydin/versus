import React from "react";

/**
 * Strichfigur im Doodle-Stil.
 *
 * Bewusst KEIN Rig wie Lino: In der Vorlage sprechen die Figuren nicht,
 * sie illustrieren waehrend eine Stimme darueber laeuft. Damit fallen
 * Mundformen und Lipsync weg - die Figur braucht nur Posen.
 *
 * DIE FIGUR ZEICHNET SICH SELBST
 * Das ist das Kennzeichen der Strichzeichen-Kanaele (Sprouts, AsapSCIENCE,
 * RSA Animate): Man sieht die Zeichnung entstehen, statt sie fertig
 * vorgesetzt zu bekommen. Das haelt den Blick fest, weil in jedem Moment
 * noch etwas passiert - ein hart geschnittenes Standbild ist nach einer
 * halben Sekunde abgearbeitet.
 *
 * Technisch: pathLength={1} normiert jede Linie auf die Laenge eins,
 * unabhaengig davon, wie lang sie tatsaechlich ist. Danach faehrt
 * strokeDashoffset von 1 auf 0 und die Linie waechst. Ohne pathLength
 * muesste man jede Pfadlaenge im Browser messen.
 *
 * Die Reihenfolge ist die, in der ein Mensch zeichnet: Kopf, Gesicht,
 * Rumpf, Arme, Beine.
 */

export const TINTE = "#1A1A1A";
export const PAPIER = "#F2F0EC";

export type Pose =
  | "stehen" | "denken" | "zeigen" | "jubeln" | "sitzen" | "achselzucken";

export type FigurProps = {
  pose?: Pose;
  /** Haare andeuten - unterscheidet zwei Figuren voneinander */
  haare?: boolean;
  /** -1 traurig, 0 neutral, 1 froh */
  stimmung?: number;
  strich?: number;
  /** 0 = leeres Blatt, 1 = fertig gezeichnet */
  zeichnen?: number;
};

const klemm = (x: number) => Math.max(0, Math.min(1, x));
/** Anteil, den dieses Koerperteil im Gesamtfortschritt schon erreicht hat */
const teil = (p: number, von: number, bis: number) => klemm((p - von) / (bis - von));

export const Figur: React.FC<FigurProps> = ({
  pose = "stehen",
  haare = false,
  stimmung = 0,
  strich = 7,
  zeichnen = 1,
}) => {
  const arme: Record<Pose, [number, number, number, number][]> = {
    stehen: [[70, 150, 55, 205], [130, 150, 145, 205]],
    denken: [[70, 150, 60, 200], [130, 150, 150, 95]],
    zeigen: [[70, 150, 55, 205], [130, 145, 178, 108]],
    jubeln: [[70, 145, 45, 92], [130, 145, 155, 92]],
    sitzen: [[70, 152, 52, 200], [130, 152, 152, 198]],
    achselzucken: [[68, 148, 44, 128], [132, 148, 156, 128]],
  };
  const beine: Record<Pose, [number, number][]> = {
    stehen: [[74, 268], [126, 268]],
    denken: [[74, 268], [126, 268]],
    zeigen: [[74, 268], [126, 268]],
    jubeln: [[68, 266], [132, 266]],
    sitzen: [[58, 214], [142, 214]],
    achselzucken: [[74, 268], [126, 268]],
  };

  const mund =
    stimmung > 0.3 ? "M 84 62 Q 100 78 116 62"
    : stimmung < -0.3 ? "M 84 72 Q 100 56 116 72"
    : "M 84 68 L 116 68";

  const linie = {
    stroke: TINTE,
    strokeWidth: strich,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    fill: "none",
  };
  /** Strichanimation fuer ein einzelnes Element */
  const zug = (p: number) => ({
    pathLength: 1,
    strokeDasharray: 1,
    strokeDashoffset: 1 - p,
  });

  const pKopf = teil(zeichnen, 0, 0.26);
  const pHaar = teil(zeichnen, 0.20, 0.34);
  const pGesicht = teil(zeichnen, 0.28, 0.44);
  const pRumpf = teil(zeichnen, 0.42, 0.58);
  const pArme = teil(zeichnen, 0.55, 0.78);
  const pBeine = teil(zeichnen, 0.74, 1);

  return (
    <svg viewBox="0 0 200 300" style={{ width: "100%", height: "100%" }}>
      <circle cx={100} cy={50} r={42} {...linie} {...zug(pKopf)} />
      {haare && (
        <>
          <path d="M 62 34 Q 74 4 100 8 Q 126 4 138 34" {...linie} {...zug(pHaar)} />
          <path d="M 60 44 Q 52 74 58 96" {...linie} {...zug(pHaar)} />
          <path d="M 140 44 Q 148 74 142 96" {...linie} {...zug(pHaar)} />
        </>
      )}

      {/* Augen sind Punkte, keine Linien - sie wachsen statt zu laufen */}
      <circle cx={86} cy={44} r={4.5 * pGesicht} fill={TINTE} />
      <circle cx={114} cy={44} r={4.5 * pGesicht} fill={TINTE} />
      <path d={mund} {...linie} strokeWidth={strich * 0.8} {...zug(pGesicht)} />

      <line x1={100} y1={92} x2={100} y2={190} {...linie} {...zug(pRumpf)} />

      {arme[pose].map(([ex, ey, hx, hy], i) => (
        <path key={i} d={`M 100 118 L ${ex} ${ey} L ${hx} ${hy}`} {...linie} {...zug(pArme)} />
      ))}
      {beine[pose].map(([x, y], i) => (
        <path key={i} d={`M 100 190 L ${x} ${y}`} {...linie} {...zug(pBeine)} />
      ))}
    </svg>
  );
};
