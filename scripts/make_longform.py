#!/usr/bin/env python3
"""
Sammelfolge: mehrere fertige Kapitel zu einem Querformat-Video verketten.

  ./venv/bin/python scripts/make_longform.py --episodes a b c d --name geldbasics

Nimmt Folgen, die finance_gen.py schon geschrieben hat. Es entsteht kein
einziger neuer Satz - dieselben Kapitel laufen einzeln als Shorts und
zusammen als Langfassung.

Warum das ueberhaupt: Shorts bringen Reichweite, aber kaum Wiedergabezeit,
und die Wiedergabezeit ist die Schwelle zur Monetarisierung (4.000 Stunden
in zwoelf Monaten). Sechs Kapitel ergeben rund acht Minuten.
"""

import argparse
import json
import pathlib
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
VENV_PY = ROOT / "venv" / "bin" / "python"
STIMME = {"voice": "en-US-AndrewNeural", "rate": "-3%", "pitch": "+0Hz"}

KARTE = 2.4        # Kapitelkarte, siehe DoodleLang.tsx
NACHLAUF = 0.6     # damit das letzte Wort nicht abreisst
MIDROLL = 480.0    # 8 Minuten - ab hier erlaubt YouTube Mid-Roll-Anzeigen


def run(cmd: list[str]) -> tuple[bool, str]:
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return p.returncode == 0, p.stdout + p.stderr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", nargs="*")
    ap.add_argument("--letzte", type=int,
                    help="die N zuletzt produzierten Folgen nehmen")
    ap.add_argument("--name", required=True, help="Dateiname der Sammelfolge")
    ap.add_argument("--titel", help="YouTube-Titel; sonst aus den Kapiteln gebaut")
    args = ap.parse_args()

    if args.letzte:
        queue = json.loads((ROOT / "episodes" / "queue.json").read_text())
        # Nur Folgen, die es wirklich gibt - eine abgebrochene Erzeugung
        # steht in "used", hat aber keinen Ordner.
        vorhanden = [s for s in queue["used"]
                     if (ROOT / "episodes" / s / "plan.json").exists()]
        args.episodes = vorhanden[-args.letzte:]
    if not args.episodes:
        raise SystemExit("--episodes oder --letzte angeben")

    start = time.time()
    kapitel = []
    tags: list[str] = []
    hashtags: list[str] = []
    erstes_thumb: dict = {}

    print(f"Sammelfolge '{args.name}' aus {len(args.episodes)} Kapiteln")
    print("=" * 62)

    for i, slug in enumerate(args.episodes):
        ep = ROOT / "episodes" / slug
        plan = json.loads((ep / "plan.json").read_text(encoding="utf-8"))

        # Eigener Name je Kapitel: sonst ueberschreibt Kapitel 2 die
        # Tonspur von Kapitel 1, und im Video laeuft ueberall dieselbe.
        name = f"kap_{i}"
        ok, out = run([
            str(VENV_PY), "scripts/build_voice.py",
            "--script", str(ep / "script_en.txt"),
            "--name", name, "--lang", "en",
            "--voice", STIMME["voice"],
            f"--rate={STIMME['rate']}",
            f"--pitch={STIMME['pitch']}",
        ])
        if not ok:
            raise SystemExit(f"Kapitel {slug}: Stimme fehlgeschlagen\n{out[-500:]}")

        voice = json.loads((ROOT / "src" / "data" / f"{name}.json").read_text())
        kapitel.append({
            "ueberschrift": plan["ueberschrift"],
            "audio": f"{name}.mp3",
            "duration": voice["duration"],
            "groups": voice["groups"],
            "words": voice.get("words", []),
            "bilder": plan["bilder"],
        })
        tags.extend(plan.get("tags", []))
        hashtags.extend(plan.get("hashtags", []))
        if i == 0:
            erstes_thumb = plan.get("thumbnail") or {}
        print(f"  {i+1}. {plan['ueberschrift'][:46]:46s} {voice['duration']:5.1f}s")

    gesamt = sum(k["duration"] + KARTE + NACHLAUF for k in kapitel)

    # Ab acht Minuten schaltet YouTube Mid-Roll-Anzeigen frei. Genau an
    # der Grenze zu landen ist fahrlaessig: ein Kapitel, das die Stimme
    # zwei Sekunden kuerzer spricht, kippt das ganze Video darunter.
    if gesamt < MIDROLL:
        print(f"\n  ACHTUNG: {gesamt:.0f}s - unter der Mid-Roll-Grenze von "
              f"{MIDROLL:.0f}s. Ein Kapitel mehr nehmen.")
    elif gesamt < MIDROLL + 20:
        print(f"\n  Knapp: {gesamt:.0f}s, nur {gesamt-MIDROLL:.0f}s ueber der "
              f"Mid-Roll-Grenze.")
    titel = args.titel or f"{len(kapitel)} Geldbegriffe, in {round(gesamt/60)} Minuten erklärt"

    # Kapitelmarken in der Beschreibung: YouTube macht daraus eine
    # Kapitelleiste, wenn die erste Marke bei 0:00 steht.
    marken, t = [], 0.0
    for k in kapitel:
        marken.append(f"{int(t)//60}:{int(t)%60:02d} {k['ueberschrift']}")
        t += 2.4 + k["duration"] + 0.6

    # Kein "#shorts" hier - das ist ein Langvideo, und eine falsche
    # Formatangabe schadet mehr als sie nuetzt.
    tags_zeile = " ".join(list(dict.fromkeys(hashtags))[:5])
    beschreibung = "\n\n".join([
        f"{len(kapitel)} Begriffe aus Geld und Wirtschaft, einer nach dem "
        "anderen erklärt. Mit Strichmännchen und ohne Fachchinesisch.",
        "\n".join(marken),
        tags_zeile,
        "Dieses Video erklärt Begriffe. Es ist keine Anlageberatung "
        "und keine Kaufempfehlung.",
    ])

    eindeutig = list(dict.fromkeys(tags))[:20]
    daten = {"titel": titel, "beschreibung": beschreibung,
             "tags": eindeutig, "kapitel": kapitel}
    (ROOT / "src" / "data" / "lang.json").write_text(
        json.dumps(daten, ensure_ascii=False), encoding="utf-8")

    print(f"\n  Gesamtlaenge: {gesamt/60:.1f} min")
    print("\n[Render]")
    ziel = ROOT / "out" / f"{args.name}.mp4"
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ok, out = run(["npx", "remotion", "render", "DoodleLang", str(ziel)])
    if not ok:
        zeilen = [l for l in out.splitlines() if l.strip()][-4:]
        raise SystemExit("Render fehlgeschlagen:\n  " + "\n  ".join(zeilen))

    # Thumbnail einer Sammelfolge muss die SAMMLUNG benennen, nicht das
    # erste Kapitel. Die Zuspitzung des ersten Kapitels stand hier
    # zuerst - "Preis des Wartens" ueber "5 Begriffe" verspricht ein Thema
    # und liefert fuenf. Genau die Luecke zwischen Bild und Inhalt, die
    # bei den Einzelfolgen verboten ist.
    thumb = {
        "zeile": "Geld verstehen",
        "zahl": f"{len(kapitel)} Begriffe",
        "icon": erstes_thumb.get("icon"),
    }
    (ROOT / "src" / "data" / "thumb.json").write_text(
        json.dumps(thumb, ensure_ascii=False), encoding="utf-8")
    bild = ROOT / "out" / f"{args.name}.png"
    ok, _ = run(["npx", "remotion", "still", "Thumbnail", str(bild), "--frame=0"])
    print(f"  Thumbnail: {bild.name}" if ok else "  Thumbnail FEHLGESCHLAGEN")

    # Als normaler Folgenordner ablegen: publish.py liest
    # episodes/<name>/plan.json und braucht dann keinen Sonderweg.
    ordner = ROOT / "episodes" / args.name
    ordner.mkdir(parents=True, exist_ok=True)
    (ordner / "plan.json").write_text(
        json.dumps({"version": 2, "slug": args.name, "titel": titel,
                    "ueberschrift": titel, "beschreibung": beschreibung,
                    "tags": eindeutig,
                    "hashtags": list(dict.fromkeys(hashtags))[:5],
                    "thumbnail": thumb, "bilder": [],
                    "kapitel": [k["ueberschrift"] for k in kapitel]},
                   ensure_ascii=False, indent=2),
        encoding="utf-8")

    print(f"  {ziel.name}  {ziel.stat().st_size/1048576:.1f} MB")
    print(f"\nFertig in {time.time()-start:.0f}s -> {ziel}")
    print(f"Titel: {titel}")


if __name__ == "__main__":
    main()
