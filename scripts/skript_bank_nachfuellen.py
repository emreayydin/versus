"""The Difference Money: Skriptsammlung montags mit Gemini auffuellen (GitHub).

Fuer offene Themen ohne fertiges Skript schreibt Gemini eine Folge nach den
Kanalregeln (SYSTEM aus versus_gen.py). Jede Folge muss pruefe() bestehen
und wird danach gegen zwei Wikipedia-Artikel gegengelesen (gemini_kern.py).
Neue Skripte landen in scripts/skript_bank_neu.py.

    ./venv/bin/python scripts/skript_bank_nachfuellen.py
    ./venv/bin/python scripts/skript_bank_nachfuellen.py --anzahl 2
"""
import argparse
import os
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))

import gemini_kern as g  # noqa: E402
import versus_gen as v  # noqa: E402

NEU_DATEI = HIER / "skript_bank_neu.py"
ZIEL = int(os.environ.get("SKRIPT_ZIEL", "21"))
MAX_THEMEN = 40

ZUSATZ = """
Additionally include "wikipedia": two exact English Wikipedia article titles
that define the two terms, e.g. ["en:Bond duration", "en:Maturity (finance)"].
Every factual statement in the script is checked against those articles.
Number examples must be simple, illustrative and internally consistent.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--anzahl", type=int)
    args = ap.parse_args()

    q = v.lade_queue()
    benutzt = set(q["used"])
    bank = v.bank_skripte()
    frisch = [s for s in bank if s not in benutzt]
    fehlend = args.anzahl if args.anzahl is not None else max(0, ZIEL - len(frisch))
    print(f"Frische Skripte: {len(frisch)}, Ziel {ZIEL}, fehlen {fehlend}")
    if not fehlend:
        return

    themen = [t for t in dict.fromkeys(q["offen"])
              if v.slugify(t) not in benutzt and v.slugify(t) not in bank]
    if len(themen) < fehlend * 2:
        try:
            themen += [t for t in v.neue_themen(q["offen"] + q["used"]) if v.slugify(t) not in bank]
        except Exception as fehler:  # noqa: BLE001
            print("  Themen-Nachschub gescheitert:", fehler)

    try:
        from skript_bank_neu import SKRIPTE_NEU
    except ImportError:
        SKRIPTE_NEU = []
    neu, verworfen = [], 0
    for thema in themen[:MAX_THEMEN]:
        if len(neu) >= fehlend:
            break
        print(f"Thema: {thema}")
        try:
            folge = g.json_aus(g.frage(v.SYSTEM + ZUSATZ + f'\n\nWrite the episode for: "{thema}".',
                                       temperatur=0.6))
        except (ValueError, RuntimeError) as fehler:
            verworfen += 1
            print("  gescheitert:", fehler)
            continue
        if not isinstance(folge, dict):
            verworfen += 1
            continue
        maengel = v.pruefe(folge)
        if maengel:
            verworfen += 1
            print("  verworfen:", "; ".join(maengel[:3]))
            continue
        belege = "\n\n".join(f"[{w}]\n{g.wiki_text(w, 8000)}" for w in (folge.get("wikipedia") or [])[:2])
        if len(belege) < 400:
            verworfen += 1
            print("  verworfen: kein Wikipedia-Artikel gefunden")
            continue
        ok, warum = g.pruefen(
            {"thema": thema, "saetze": [s.get("text") for s in folge["saetze"]]},
            "This is an educational finance explainer. Definitions and mechanisms must "
            "match the reference text. Simple illustrative number examples are fine if "
            "they are arithmetically correct. Any investment advice means ok=false.",
            zusatz=f"REFERENCE TEXT (Wikipedia):\n{belege}\n")
        if not ok:
            verworfen += 1
            print("  Pruefung nein:", warum)
            continue
        folge.pop("wikipedia", None)
        folge["thema"] = thema
        neu.append(folge)
        print("  + aufgenommen")

    if neu:
        g.schreibe_modul(NEU_DATEI, "SKRIPTE_NEU", list(SKRIPTE_NEU) + neu,
                         "Von Gemini geschriebene, gepruefte Vergleichsskripte "
                         "(scripts/skript_bank_nachfuellen.py). Nicht von Hand ordnen.")
    print(f"Ergebnis: {len(neu)} neu, {verworfen} verworfen, "
          f"noch fehlend {max(0, fehlend - len(neu))}")


if __name__ == "__main__":
    main()
