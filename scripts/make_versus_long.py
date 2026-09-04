#!/usr/bin/env python3
"""
Langfassung bauen: Stimme je Abschnitt, dann rendern.

  ./venv/bin/python scripts/make_versus_long.py --episode stocks-vs-bonds

Unterschied zu make_longform.py: Das hier verkettet keine fertigen Shorts,
sondern baut EINE durchgehende Folge aus episodes_lang/<slug>/ - ein Paar,
durch feste Dimensionen gefuehrt. Die Kapitelkarten tragen deshalb die
Dimensionsnamen ("Risk", "Time", ...), nicht sechs verschiedene Themen.
"""

import argparse
import json
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
VENV_PY = ROOT / "venv" / "bin" / "python"
EPISODES = ROOT / "episodes_lang"
STIMME = {"voice": "en-US-AndrewNeural", "rate": "-3%", "pitch": "+0Hz"}
KARTE = 2.4        # Kapitelkarte, siehe DoodleLang.tsx
NACHLAUF = 0.6


def run(cmd):
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return p.returncode == 0, p.stdout + p.stderr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", required=True)
    ap.add_argument("--nur-bauen", action="store_true",
                    help="nicht rendern, nur Stimme und Daten")
    a = ap.parse_args()

    ep = EPISODES / a.episode
    plan = json.loads((ep / "plan.json").read_text(encoding="utf-8"))
    start = time.time()

    print(f"Langfassung '{plan['titel']}'")
    print("=" * 62)

    if not (ROOT / "public" / "bett.wav").exists():
        print("[Musik] Bett fehlt, wird erzeugt")
        run([str(VENV_PY), "scripts/music.py"])

    kapitel = []
    for i, abschnitt in enumerate(plan["abschnitte"]):
        skript = ep / f"abschnitt_{i:02d}.txt"
        # Eigener Name je Abschnitt - sonst ueberschreibt Abschnitt 2 die
        # Tonspur von Abschnitt 1 und im Video laeuft ueberall dieselbe.
        name = f"kap_{i}"
        ok, out = run([
            str(VENV_PY), "scripts/build_voice.py",
            "--script", str(skript), "--name", name, "--lang", "en",
            "--voice", STIMME["voice"],
            f"--rate={STIMME['rate']}", f"--pitch={STIMME['pitch']}",
        ])
        if not ok:
            raise SystemExit(f"Abschnitt {i}: Stimme fehlgeschlagen\n{out[-600:]}")

        voice = json.loads((ROOT / "src" / "data" / f"{name}.json").read_text())
        bilder = abschnitt["bilder"]
        if len(voice["groups"]) != len(bilder):
            # Kein Abbruch: Die Szene haelt das letzte Bild, wenn Bilder
            # fehlen. Aber es soll auffallen - es deutet auf einen Satz hin,
            # den die Stimme anders getrennt hat als der Generator.
            print(f"     ACHTUNG: {len(voice['groups'])} Saetze zu "
                  f"{len(bilder)} Bildern")
        kapitel.append({
            "ueberschrift": abschnitt["ueberschrift"],
            "audio": f"{name}.mp3",
            "duration": voice["duration"],
            "groups": voice["groups"],
            "words": voice.get("words", []),
            "bilder": bilder,
        })
        print(f"  {i+1}. {abschnitt['ueberschrift'][:38]:38s} "
              f"{voice['duration']:5.1f}s")

    gesamt = sum(k["duration"] + KARTE + NACHLAUF for k in kapitel)
    minuten = gesamt / 60
    print("-" * 62)
    print(f"  Gesamtlaenge {minuten:.1f} Minuten")
    # Ab acht Minuten schaltet YouTube Mid-Roll-Anzeigen frei. Und nur die
    # Wiedergabezeit normaler Videos zaehlt fuer die 4.000-Stunden-Schwelle -
    # Shorts zaehlen dafuer nicht. Darum ist diese Grenze der ganze Zweck.
    if minuten < 8:
        print(f"  WARNUNG: unter 8 Minuten - keine Mid-Roll-Anzeigen")

    daten = {"titel": plan["titel"], "beschreibung": plan["beschreibung"],
             "tags": plan.get("tags", []), "begriffe": plan.get("begriffe", []),
             "kapitel": kapitel}
    (ROOT / "src" / "data" / "lang.json").write_text(
        json.dumps(daten, ensure_ascii=False, indent=2), encoding="utf-8")

    thumb = {"zeile": " vs ".join(plan.get("begriffe", []))[:26] or plan["titel"][:26],
             "zahl": None, "icon": "waage"}
    (ROOT / "src" / "data" / "thumb.json").write_text(
        json.dumps(thumb, ensure_ascii=False, indent=2), encoding="utf-8")

    if a.nur_bauen:
        print("\n[nur-bauen] Rendern uebersprungen.")
        return

    print("\n[Thumbnail]")
    ziel_bild = ROOT / "out" / f"{a.episode}.png"
    ok, out = run(["npx", "remotion", "still", "Thumbnail", str(ziel_bild)])
    print(f"  {ziel_bild.name}" if ok else f"  fehlgeschlagen:\n{out[-400:]}")

    print("\n[Render]")
    ziel = ROOT / "out" / f"{a.episode}.mp4"
    ok, out = run(["npx", "remotion", "render", "DoodleLang", str(ziel)])
    if not ok:
        raise SystemExit(f"Render fehlgeschlagen:\n{out[-900:]}")
    mb = ziel.stat().st_size / 1048576
    print(f"  {ziel.name}  {mb:.1f} MB")
    print(f"\nFertig in {time.time()-start:.0f}s -> {ziel}")
    print(f"Titel: {plan['titel']}")


if __name__ == "__main__":
    main()
