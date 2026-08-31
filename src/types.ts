export type Group = {
  index: number;
  text: string;
  start: number;
  end: number;
  lastWordStart: number;
};

export type VoiceData = {
  lang: string;
  duration: number;
  groups: Group[];
  /** Wort-Zeitstempel aus edge-tts, Grundlage der Untertitel */
  words?: Wort[];
};

import type { IconName } from "./doodle/Icon";

export type Pose =
  | "stehen" | "denken" | "zeigen" | "jubeln" | "sitzen" | "achselzucken";

/** Ein Diagramm mit den Zahlen aus dem Skript. */
export type DiagrammDaten = {
  art: "linie" | "balken";
  werte: number[];
  /** Linie: [Anfang, Ende]. Balken: je Balken eine Beschriftung. */
  achse?: string[];
  einheit?: string;
};

export type Bild = {
  pose: Pose;
  haare?: boolean;
  stimmung?: number;
  wort?: string;
  /** gezeichnetes Symbol neben der Figur, siehe doodle/Icon.tsx */
  icon?: IconName;
  /** Diagramm statt Figur - wenn Zahlen die Aussage tragen */
  diagramm?: DiagrammDaten;
};

/** Alles, was eine Folge ausser der Sprachspur braucht. */
export type Plan = {
  slug: string;
  ueberschrift: string;
  titel: string;
  beschreibung: string;
  tags: string[];
  bilder: Bild[];
};

/** Ein Kapitel der Sammelfolge: eigene Tonspur, eigene Ueberschrift. */
export type Kapitel = {
  ueberschrift: string;
  audio: string;
  duration: number;
  groups: Group[];
  bilder: Bild[];
  words?: Wort[];
};

export type LangDaten = {
  titel: string;
  beschreibung: string;
  tags: string[];
  kapitel: Kapitel[];
};

export type Wort = { word: string; start: number; end: number };
