import React from "react";
import { TINTE } from "./Figur";

/**
 * Gezeichnete Symbole, mit demselben Strich wie die Figuren.
 *
 * Bewusst keine Emoji: Emoji sind farbig und glattgerendert und wirken auf
 * schwarzweisser Tinte aufgeklebt. Sie haengen ausserdem an einer
 * Emoji-Schrift auf dem Rechner, der rendert - fehlt sie auf dem
 * GitHub-Runner, stehen leere Kaestchen im fertigen Video, und das faellt
 * erst nach dem Upload auf.
 *
 * Diese hier sind SVG-Pfade im Quelltext. Sie rendern ueberall gleich und
 * gehoeren uns.
 */

export type IconName =
  | "muenze" | "stapel" | "hoch" | "runter" | "kurve" | "balken"
  | "uhr" | "haus" | "korb" | "bank" | "prozent" | "schere" | "waage";

const S = { stroke: TINTE, strokeWidth: 7, strokeLinecap: "round" as const,
            strokeLinejoin: "round" as const, fill: "none" };

const PFADE: Record<IconName, React.ReactNode> = {
  // Das Euro-Zeichen braucht einen duenneren Strich als der Rand: bei
  // gleicher Staerke laufen der Bogen und die beiden Querbalken auf so
  // kleiner Flaeche ineinander und werden zu einem Klumpen.
  muenze: (<>
    <circle cx={50} cy={50} r={32} {...S} pathLength={1} />
    <path d="M62 36 Q38 36 38 50 Q38 64 62 64" {...S} strokeWidth={5} pathLength={1} />
    <path d="M31 45 H51" {...S} strokeWidth={5} pathLength={1} />
    <path d="M31 55 H51" {...S} strokeWidth={5} pathLength={1} />
  </>),
  stapel: (<>
    <ellipse cx={50} cy={30} rx={30} ry={11} {...S} pathLength={1} />
    <path d="M20 30 V44 Q20 55 50 55 Q80 55 80 44 V30" {...S} pathLength={1} />
    <path d="M20 48 V62 Q20 73 50 73 Q80 73 80 62 V48" {...S} pathLength={1} />
  </>),
  hoch: (<>
    <path d="M50 82 V22" {...S} pathLength={1} />
    <path d="M28 44 L50 20 L72 44" {...S} pathLength={1} />
  </>),
  runter: (<>
    <path d="M50 18 V78" {...S} pathLength={1} />
    <path d="M28 56 L50 80 L72 56" {...S} pathLength={1} />
  </>),
  kurve: (<>
    <path d="M16 82 V16 M16 82 H86" {...S} pathLength={1} />
    <path d="M24 74 Q48 72 60 54 Q70 38 80 22" {...S} pathLength={1} />
  </>),
  balken: (<>
    <path d="M16 84 H86" {...S} pathLength={1} />
    <path d="M28 84 V62 M50 84 V44 M72 84 V24" {...S} pathLength={1} />
  </>),
  uhr: (<>
    <circle cx={50} cy={52} r={31} {...S} pathLength={1} />
    <path d="M50 32 V52 L64 62" {...S} pathLength={1} />
  </>),
  haus: (<>
    <path d="M18 50 L50 22 L82 50" {...S} pathLength={1} />
    <path d="M28 48 V82 H72 V48" {...S} pathLength={1} />
    <path d="M44 82 V62 H58 V82" {...S} pathLength={1} />
  </>),
  korb: (<>
    <path d="M18 26 H30 L42 64 H76" {...S} pathLength={1} />
    <path d="M32 36 H84 L78 64" {...S} pathLength={1} />
    <circle cx={46} cy={78} r={6} {...S} pathLength={1} />
    <circle cx={72} cy={78} r={6} {...S} pathLength={1} />
  </>),
  bank: (<>
    <path d="M16 38 L50 18 L84 38" {...S} pathLength={1} />
    <path d="M26 42 V72 M42 42 V72 M58 42 V72 M74 42 V72" {...S} pathLength={1} />
    <path d="M16 80 H84" {...S} pathLength={1} />
  </>),
  prozent: (<>
    <circle cx={32} cy={32} r={13} {...S} pathLength={1} />
    <circle cx={68} cy={68} r={13} {...S} pathLength={1} />
    <path d="M78 22 L22 78" {...S} pathLength={1} />
  </>),
  schere: (<>
    <circle cx={30} cy={74} r={11} {...S} pathLength={1} />
    <circle cx={70} cy={74} r={11} {...S} pathLength={1} />
    <path d="M38 66 L72 20 M62 66 L28 20" {...S} pathLength={1} />
  </>),
  waage: (<>
    <path d="M50 20 V80 M30 80 H70" {...S} pathLength={1} />
    <path d="M18 34 H82" {...S} pathLength={1} />
    <path d="M18 34 L8 56 H28 Z M82 34 L72 56 H92 Z" {...S} pathLength={1} />
  </>),
};

export const ICONS = Object.keys(PFADE) as IconName[];

/**
 * Das Symbol zeichnet sich wie die Figur - sonst springt es fertig ins
 * Bild, waehrend daneben noch gezeichnet wird, und das wirkt wie ein
 * Fehler.
 */
export const Icon: React.FC<{ name: IconName; zeichnen?: number }> = ({
  name,
  zeichnen = 1,
}) => (
  <svg viewBox="0 0 100 100" width="100%" height="100%">
    <g
      style={{
        // pathLength normiert jede Linie auf eins, siehe Figur.tsx
        strokeDasharray: 1,
        strokeDashoffset: 1 - Math.max(0, Math.min(1, zeichnen)),
      }}
    >
      {PFADE[name] ?? PFADE.muenze}
    </g>
  </svg>
);
