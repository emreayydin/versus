#!/usr/bin/env python3
"""
Folgenproduktion von einem Befehl aus: Skript -> Stimme -> Render.

  ./venv/bin/python scripts/make_episode.py --episode zinseszins

Erwartet in episodes/<slug>/ die beiden Dateien, die finance_gen.py
schreibt: script_de.txt und plan.json.

Der Render zieht seine Daten aus src/data/. Dieses Skript legt sie dort
ab, bevor es rendert - deshalb aendert eine neue Folge keine Zeile Code.
"""

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
VENV_PY = ROOT / "venv" / "bin" / "python"

# Erwachsene Erzaehlstimme, ruhig. Etwas langsamer als der Standard: das
# Format hat viel Inhalt auf wenig Zeit, und Zahlen brauchen Luft.
STIMMEN = {
    "de": {"voice": "de-DE-ConradNeural", "rate": "-4%", "pitch": "+0Hz"},
    "en": {"voice": "en-US-AndrewNeural", "rate": "-3%", "pitch": "+0Hz"},
}


def run(cmd: list[str]) -> tuple[bool, str]:
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return p.returncode == 0, p.stdout + p.stderr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", required=True)
    ap.add_argument("--lang", default="de", choices=list(STIMMEN))
    ap.add_argument("--voice-only", action="store_true")
    args = ap.parse_args()

    ep = ROOT / "episodes" / args.episode
    skript = ep / f"script_{args.lang}.txt"
    plan_datei = ep / "plan.json"
    for f in (skript, plan_datei):
        if not f.exists():
            raise SystemExit(f"Fehlt: {f}")

    plan = json.loads(plan_datei.read_text(encoding="utf-8"))
    start = time.time()
    print(f"Folge '{args.episode}'  ({args.lang})")
    print("=" * 62)

    if not (ROOT / "public" / "bett.wav").exists():
        print("\n[Musik] Bett fehlt, wird erzeugt")
        run([str(VENV_PY), "scripts/music.py"])

    print("\n[Stimme]")
    cfg = STIMMEN[args.lang]
    # Gleichheitszeichen-Form ist Pflicht: Werte wie "-4%" beginnen mit
    # "-", argparse haelt sie sonst fuer einen Optionsnamen.
    ok, out = run([
        str(VENV_PY), "scripts/build_voice.py",
        "--script", str(skript), "--name", "voice", "--lang", args.lang,
        "--voice", cfg["voice"],
        f"--rate={cfg['rate']}",
        f"--pitch={cfg['pitch']}",
    ])
    if not ok:
        raise SystemExit(f"Stimme fehlgeschlagen:\n{out[-800:]}")

    voice = json.loads((ROOT / "src" / "data" / "voice.json").read_text())
    gruppen, bilder = len(voice["groups"]), len(plan["bilder"])
    print(f"  {voice['duration']:.1f}s, {gruppen} Saetze")
    if gruppen != bilder:
        # Kein Abbruch: DoodleEpisode haelt das letzte Bild, wenn Bilder
        # fehlen. Aber es soll auffallen, weil es auf einen Fehler im
        # Generator hindeutet.
        print(f"  ACHTUNG: {gruppen} Saetze zu {bilder} Bildern")

    shutil.copy(plan_datei, ROOT / "src" / "data" / "plan.json")

    if args.voice_only:
        print("\nNur Stimme - kein Render.")
        return

    # Thumbnail zuerst: ohne eigenes greift sich YouTube ein zufaelliges
    # Einzelbild, und das ist bei diesem Format oft eine halb gezeichnete
    # Figur auf leerem Papier.
    if plan.get("thumbnail", {}).get("zeile"):
        print("\n[Thumbnail]")
        (ROOT / "src" / "data" / "thumb.json").write_text(
            json.dumps(plan["thumbnail"], ensure_ascii=False), encoding="utf-8")
        bild = ROOT / "out" / f"{args.episode}.png"
        ok, out = run(["npx", "remotion", "still", "Thumbnail", str(bild), "--frame=0"])
        print(f"  {bild.name}" if ok else f"  FEHLER: {out[-300:]}")

    print("\n[Render]")
    ziel = ROOT / "out" / f"{args.episode}.mp4"
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ok, out = run(["npx", "remotion", "render", "Doodle", str(ziel)])
    if not ok:
        zeilen = [l for l in out.splitlines() if l.strip()][-4:]
        raise SystemExit("Render fehlgeschlagen:\n  " + "\n  ".join(zeilen))
    print(f"  {ziel.name}  {ziel.stat().st_size / 1048576:.1f} MB")

    print("\n" + "=" * 62)
    print(f"Fertig in {time.time() - start:.0f}s -> {ziel}")


if __name__ == "__main__":
    main()
