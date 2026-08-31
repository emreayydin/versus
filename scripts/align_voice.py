#!/usr/bin/env python3
"""
Forced Alignment: Wort-Timings aus beliebigem Audio + bekanntem Text.

Damit ist der Lipsync unabhaengig davon, ob das TTS Timings mitliefert.
edge-tts tut es, Voicebox/Chatterbox/Kokoro und die meisten lokalen Modelle
nicht. Ohne dieses Modul waere die Stimmenwahl an "liefert zufaellig
Timings?" gefesselt.

Verfahren: Whisper transkribiert mit Wortzeitstempeln, danach wird die
Erkennung gegen den BEKANNTEN Text gemappt. Der Text steht fest - wir haben
ihn geschrieben - also ist das ein Zuordnungsproblem, kein Erkennungsproblem.
Erkennungsfehler fallen dabei heraus.

Beispiel:
  ./venv/bin/python scripts/align_voice.py \
      --audio public/lino_de.mp3 --script scripts/episode_de.txt \
      --name lino_de_aligned --lang de
"""

import argparse
import difflib
import pathlib
import re

from faster_whisper import WhisperModel

import lipsync


def script_tokens(text: str) -> list[str]:
    """Sprechbare Woerter aus dem Skript - Satzzeichen fliegen raus."""
    return [t for t in re.findall(r"[^\s]+", text) if lipsync.normalise(t)]


def transcribe(audio: str, lang: str, model_size: str) -> list[dict]:
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(
        audio, language=lang, word_timestamps=True, vad_filter=False
    )
    words: list[dict] = []
    for seg in segments:
        for w in seg.words or []:
            if lipsync.normalise(w.word):
                words.append({
                    "word": w.word.strip(),
                    "start": round(w.start, 4),
                    "end": round(w.end, 4),
                })
    return words


def align(script: list[str], heard: list[dict]) -> list[dict]:
    """Skriptwoerter auf erkannte Zeitstempel abbilden.

    Nicht zugeordnete Skriptwoerter bekommen ihre Zeit anteilig aus der
    Luecke zwischen den beiden naechsten zugeordneten Nachbarn.
    """
    a = [lipsync.normalise(w) for w in script]
    b = [lipsync.normalise(w["word"]) for w in heard]

    timed: list[dict | None] = [None] * len(script)
    matcher = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    for i, j, n in matcher.get_matching_blocks():
        for k in range(n):
            timed[i + k] = {
                "word": script[i + k],
                "start": heard[j + k]["start"],
                "end": heard[j + k]["end"],
            }

    matched = sum(1 for t in timed if t is not None)
    if matched == 0:
        raise SystemExit(
            "Kein einziges Wort zuzuordnen - falsche Sprache oder falscher Text?"
        )

    # Luecken fuellen
    for idx, entry in enumerate(timed):
        if entry is not None:
            continue
        prev = next((timed[k] for k in range(idx - 1, -1, -1) if timed[k]), None)
        nxt = next(
            (timed[k] for k in range(idx + 1, len(timed)) if timed[k]), None
        )
        if prev and nxt:
            gap_start, gap_end = prev["end"], nxt["start"]
            missing = [k for k in range(idx, len(timed)) if timed[k] is None]
            run = 0
            while idx + run < len(timed) and timed[idx + run] is None:
                run += 1
            slot = max((gap_end - gap_start) / max(run, 1), 0.08)
            offset = idx - missing[0] if missing else 0
            start = gap_start + offset * slot
            timed[idx] = {
                "word": script[idx],
                "start": round(start, 4),
                "end": round(start + slot, 4),
            }
        elif prev:
            timed[idx] = {
                "word": script[idx],
                "start": prev["end"],
                "end": round(prev["end"] + 0.25, 4),
            }
        else:
            timed[idx] = {"word": script[idx], "start": 0.0, "end": 0.25}

    # Monotonie erzwingen - Whisper liefert gelegentlich Ueberlappungen
    out: list[dict] = []
    last_end = 0.0
    for entry in timed:
        assert entry is not None
        start = max(entry["start"], last_end)
        end = max(entry["end"], start + 0.05)
        out.append({"word": entry["word"], "start": round(start, 4),
                    "end": round(end, 4)})
        last_end = end

    print(f"  zugeordnet: {matched}/{len(script)} Woerter direkt erkannt")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", required=True)
    ap.add_argument("--script", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--lang", default="de", choices=lipsync.LANGS)
    ap.add_argument("--model", default="small",
                    help="tiny|base|small|medium - small reicht, weil der Text bekannt ist")
    args = ap.parse_args()

    root = pathlib.Path(__file__).resolve().parent.parent
    text = pathlib.Path(args.script).read_text(encoding="utf-8").strip()
    script = script_tokens(text)

    print(f"Skript   : {len(script)} Woerter")
    print(f"Whisper  : Modell '{args.model}', Sprache '{args.lang}' ...")
    heard = transcribe(args.audio, args.lang, args.model)
    print(f"  erkannt : {len(heard)} Woerter")

    words = align(script, heard)
    payload = lipsync.write_voice_json(
        root / "src" / "data" / f"{args.name}.json",
        words,
        args.lang,
        source=f"forced-alignment ({args.model})",
        script_text=text,
    )
    print()
    lipsync.report(payload)


if __name__ == "__main__":
    main()
