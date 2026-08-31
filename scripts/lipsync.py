#!/usr/bin/env python3
"""
Gemeinsame Lipsync-Logik: Wort-Timings -> Mundformen + Atemgruppen.

Bewusst getrennt von der Stimmerzeugung. Woher die Wort-Timings kommen, ist
diesem Modul egal:
  - build_voice.py  nimmt sie direkt von edge-tts (WordBoundary)
  - align_voice.py  rechnet sie per Forced Alignment aus beliebigem Audio

Dadurch ist die Stimmenwahl frei. Wechselt der TTS-Anbieter, aendert sich
hier nichts.
"""

import json
import pathlib
import re

# Mundformen, die die Figur kennt (siehe src/visemes.ts)
REST = "REST"
MBP = "MBP"   # Lippen geschlossen: m, b, p
AA = "AA"     # weit offen: a
EE = "EE"     # breit schmal: e, i
OH = "OH"     # rund mittel: o
UU = "UU"     # rund klein: u, ue
FV = "FV"     # Zaehne auf Lippe: f, v, w
LN = "LN"     # Zunge/neutral offen: l, n, t, d, s ...

VOWEL_VISEME = {
    "a": AA, "á": AA, "à": AA, "â": AA, "ä": AA, "ã": AA,
    "e": EE, "é": EE, "è": EE, "ê": EE, "ë": EE,
    "i": EE, "í": EE, "ì": EE, "î": EE, "ï": EE, "y": EE,
    "o": OH, "ó": OH, "ò": OH, "ô": OH, "ö": OH, "õ": OH,
    "u": UU, "ú": UU, "ù": UU, "û": UU, "ü": UU,
}

CONSONANT_VISEME = {
    "m": MBP, "b": MBP, "p": MBP,
    "f": FV, "v": FV, "w": FV,
}

VOWELS = set(VOWEL_VISEME)

# Englisch ist nicht lautgetreu - die haeufigsten Vokalgruppen brauchen
# eine eigene Tabelle, sonst steht der Mund bei "through" oder "name" falsch.
EN_DIGRAPHS = {
    "ee": EE, "ea": EE, "ie": EE, "ai": EE, "ay": EE, "ey": EE,
    "oo": UU, "ou": OH, "ow": OH, "oa": OH, "oe": OH,
    "au": AA, "aw": AA, "igh": AA,
}

# Franzoesisch ist noch weniger lautgetreu als Englisch.
FR_DIGRAPHS = {
    "eau": OH, "au": OH, "oi": OH, "ou": UU, "eu": UU, "oeu": UU,
    "ai": EE, "ei": EE, "ay": EE,
}

DIGRAPHS = {"en": EN_DIGRAPHS, "fr": FR_DIGRAPHS}

# Sprachen mit stummem End-e
SILENT_E = {"en", "fr"}

# Im Franzoesischen sind Endkonsonanten meist stumm.
FR_SILENT_FINAL = set("stxdzp")

LANGS = ("de", "en", "es", "fr", "pt")

# Unter dieser Dauer flackert die Mundform nur; dann lieber zusammenfassen.
MIN_VISEME_S = 0.075

# Ab dieser Sprechpause beginnt eine neue Atemgruppe.
GROUP_GAP_S = 0.35


# Buchstaben, die als sprechbar gelten. Muss ALLE Sonderzeichen der
# unterstuetzten Sprachen enthalten - sonst schrumpfen Woerter beim
# Normalisieren, und wenn eines dabei ganz verschwindet, stimmt die
# Satzwortzahl nicht mehr und die Atemgruppen verrutschen.
_SPEAKABLE = "a-zäöüßàáâãèéêëìíîïòóôõùúûüçñ"


def normalise(word: str) -> str:
    return re.sub(f"[^{_SPEAKABLE}]", "", word.lower())


def syllable_visemes(word: str, lang: str) -> list[str]:
    """Grobe Silbenzerlegung: Vokalgruppen -> je eine Mundform."""
    w = normalise(word)
    if not w:
        return []

    # Franzoesische Endkonsonanten sind meist stumm ("petit", "trop")
    if lang == "fr":
        while len(w) > 2 and w[-1] in FR_SILENT_FINAL and w[-2] not in VOWELS:
            w = w[:-1]
        while len(w) > 2 and w[-1] in FR_SILENT_FINAL:
            w = w[:-1]
            break

    # Stummes End-e ("name", "made", "tombe")
    if lang in SILENT_E and len(w) > 3 and w.endswith("e") and w[-2] not in VOWELS:
        w = w[:-1]

    if not w:
        return [LN]

    out: list[str] = []
    i = 0
    leading_consonant = CONSONANT_VISEME.get(w[0]) if w[0] not in VOWELS else None
    table = DIGRAPHS.get(lang)

    while i < len(w):
        ch = w[i]
        if ch in VOWELS:
            matched = None
            if table:
                for size in (3, 2):
                    chunk = w[i:i + size]
                    if chunk in table:
                        matched = (table[chunk], size)
                        break
            if matched is None:
                group = ch
                j = i + 1
                while j < len(w) and w[j] in VOWELS:
                    group += w[j]
                    j += 1
                # "ie" klingt im Deutschen wie langes i, nicht wie i-e
                shape = EE if group.startswith("ie") else VOWEL_VISEME[group[0]]
                matched = (shape, j - i)
            out.append(matched[0])
            i += matched[1]
        else:
            # Lippenschluss mitten im Wort sichtbar machen (z.B. "umgefallen")
            if CONSONANT_VISEME.get(ch) == MBP and out and out[-1] != MBP:
                out.append(MBP)
            i += 1

    if not out:
        out = [LN]
    if leading_consonant and out[0] != leading_consonant:
        out.insert(0, leading_consonant)
    return out


def collapse(seq: list[str]) -> list[str]:
    """Direkt aufeinanderfolgende gleiche Mundformen zusammenfassen."""
    out: list[str] = []
    for v in seq:
        if not out or out[-1] != v:
            out.append(v)
    return out


def build_visemes(words: list[dict], lang: str) -> list[dict]:
    """Wort-Timings -> zusammenhaengende Mundform-Spur."""
    track: list[dict] = []
    prev_end = 0.0

    for w in words:
        start, end = w["start"], w["end"]

        if start - prev_end > 0.12:
            track.append({"viseme": REST, "start": prev_end, "end": start})

        shapes = collapse(syllable_visemes(w["word"], lang))
        span = max(end - start, 0.03)

        max_shapes = max(1, int(span / MIN_VISEME_S))
        if len(shapes) > max_shapes:
            step = len(shapes) / max_shapes
            shapes = [shapes[int(k * step)] for k in range(max_shapes)]
            shapes = collapse(shapes)

        slot = span / len(shapes)
        for k, shape in enumerate(shapes):
            track.append({
                "viseme": shape,
                "start": start + k * slot,
                "end": start + (k + 1) * slot,
            })
        prev_end = end

    track.append({"viseme": REST, "start": prev_end, "end": prev_end + 0.6})
    return track


def sentence_lengths(text: str) -> list[int]:
    """Wortanzahl je Satz des Skripts.

    Die Atemgruppen kommen aus dem Text, NICHT aus Audio-Pausen. Grund:
    Whisper zieht Wortenden in die Stille hinein, wodurch eine Pause
    verschwinden kann - dann faellt eine Gruppe weg und die komplette
    Mimikspur verrutscht. Der Text dagegen ist in jeder Sprache und bei
    jedem TTS identisch segmentiert.
    """
    lengths: list[int] = []
    for sentence in re.split(r"(?<=[.!?])\s+", text.strip()):
        n = len([t for t in sentence.split() if normalise(t)])
        if n:
            lengths.append(n)
    return lengths


def build_groups(words: list[dict], lengths: list[int] | None = None) -> list[dict]:
    """Woerter zu Atemgruppen buendeln - Traeger der Regie-/Mimikspur."""
    groups: list[list[dict]] = []

    if lengths and sum(lengths) == len(words):
        offset = 0
        for n in lengths:
            groups.append(words[offset:offset + n])
            offset += n
    else:
        if lengths:
            print(
                f"  WARNUNG: Satzstruktur passt nicht "
                f"({sum(lengths)} Skriptwoerter vs {len(words)} erkannte) - "
                f"falle auf Pausenerkennung zurueck."
            )
        current: list[dict] = []
        for w in words:
            if current and w["start"] - current[-1]["end"] > GROUP_GAP_S:
                groups.append(current)
                current = []
            current.append(w)
        if current:
            groups.append(current)

    return [
        {
            "index": i,
            "text": " ".join(x["word"] for x in g),
            "start": round(g[0]["start"], 4),
            "end": round(g[-1]["end"], 4),
            "lastWordStart": round(g[-1]["start"], 4),
        }
        for i, g in enumerate(groups)
    ]


def write_voice_json(
    path: pathlib.Path,
    words: list[dict],
    lang: str,
    source: str,
    voice: str = "",
    script_text: str = "",
    moods: list[str] | None = None,
    cues: dict | None = None,
) -> dict:
    """Schreibt die Datei, die Remotion einliest."""
    visemes = build_visemes(words, lang)
    groups = build_groups(
        words, sentence_lengths(script_text) if script_text else None
    )
    duration = visemes[-1]["end"]

    # Regiespur wandert mit in die Sprachdatei. Vorher stand sie als
    # Konstante im Remotion-Code und war auf 10 Gruppen festgelegt - damit
    # war jede andere Episodenlaenge ausgeschlossen.
    if moods and len(moods) != len(groups):
        print(f"  WARNUNG: {len(moods)} Stimmungen zu {len(groups)} Gruppen - "
              f"Regiespur wird angepasst.")
        if len(moods) < len(groups):
            moods = moods + [moods[-1]] * (len(groups) - len(moods))
        else:
            moods = moods[:len(groups)]

    payload = {
        "voice": voice,
        "lang": lang,
        "timingSource": source,
        "moods": moods or [],
        "cues": cues or {},
        "duration": round(duration, 3),
        "words": words,
        "groups": groups,
        "visemes": [
            {
                "viseme": v["viseme"],
                "start": round(v["start"], 4),
                "end": round(v["end"], 4),
            }
            for v in visemes
        ],
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return payload


def report(payload: dict):
    print(f"Quelle   : {payload['timingSource']}")
    print(f"Woerter  : {len(payload['words'])}")
    print(f"Mundform : {len(payload['visemes'])} Segmente")
    print(f"Dauer    : {payload['duration']:.2f}s")
    print(f"Gruppen  : {len(payload['groups'])}")
    for g in payload["groups"]:
        print(f"  [{g['index']}] {g['start']:6.2f}-{g['end']:6.2f}  {g['text']}")
