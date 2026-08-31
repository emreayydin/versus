#!/usr/bin/env python3
"""
Sprachspur ueber edge-tts, inklusive nativer Wort-Timings.

edge-tts liefert WordBoundary-Events mit, deshalb braucht dieser Weg kein
Forced Alignment. Fuer jedes andere TTS (Voicebox, ElevenLabs, lokal)
nimm stattdessen align_voice.py - das Ergebnisformat ist identisch.

Achtung: edge-tts >=7 liefert per Default nur SentenceBoundary. Fuer
Lipsync muss boundary="WordBoundary" explizit gesetzt werden.

Beispiel:
  ./venv/bin/python scripts/build_voice.py \
      --script scripts/episode_de.txt --name lino_de --lang de
"""

import argparse
import asyncio
import json
import pathlib

import edge_tts

import lipsync

TICKS_PER_SECOND = 10_000_000


async def synth(text: str, voice: str, rate: str, pitch: str,
                mp3_path: pathlib.Path) -> list[dict]:
    communicate = edge_tts.Communicate(
        text, voice, rate=rate, pitch=pitch, boundary="WordBoundary"
    )
    words: list[dict] = []
    with open(mp3_path, "wb") as fh:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                fh.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / TICKS_PER_SECOND
                dur = chunk["duration"] / TICKS_PER_SECOND
                words.append({
                    "word": chunk["text"],
                    "start": round(start, 4),
                    "end": round(start + dur, 4),
                })
    return words


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", required=True, help="Textdatei mit dem Sprechtext")
    ap.add_argument("--name", default="lino_de")
    ap.add_argument("--lang", default="de", choices=lipsync.LANGS)
    ap.add_argument("--voice", default="de-DE-KatjaNeural")
    ap.add_argument("--rate", default="-8%")
    ap.add_argument("--pitch", default="+30Hz")
    ap.add_argument("--meta", help="meta.json der Folge (Regiespur)")
    args = ap.parse_args()

    root = pathlib.Path(__file__).resolve().parent.parent
    text = pathlib.Path(args.script).read_text(encoding="utf-8").strip()

    mp3_path = root / "public" / f"{args.name}.mp3"
    mp3_path.parent.mkdir(parents=True, exist_ok=True)

    words = asyncio.run(synth(text, args.voice, args.rate, args.pitch, mp3_path))
    if not words:
        raise SystemExit(
            "Keine WordBoundary-Events erhalten - Stimme/Text pruefen."
        )

    moods, cues = None, None
    if args.meta:
        meta = json.loads(pathlib.Path(args.meta).read_text(encoding="utf-8"))
        moods, cues = meta.get("moods"), meta.get("cues")

    payload = lipsync.write_voice_json(
        root / "src" / "data" / f"{args.name}.json",
        words,
        args.lang,
        source="edge-tts WordBoundary",
        voice=args.voice,
        script_text=text,
        moods=moods,
        cues=cues,
    )

    print(f"mp3      : {mp3_path}")
    lipsync.report(payload)


if __name__ == "__main__":
    main()
