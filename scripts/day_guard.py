#!/usr/bin/env python3
"""
Tagessperre gegen doppelte Laeufe.

Hintergrund: GitHub fuehrt geplante Workflows unter Last verspaetet aus
oder laesst sie ganz ausfallen. Deshalb ist der Autopilot ueberplant -
er startet mehrmals taeglich. Damit daraus nicht mehrere Tagesrationen
werden, merkt sich dieses Skript, ob heute schon produziert wurde.

Dieselbe Loesung wie in youtube-shorts-bot und muslim-world-bot.

  scripts/day_guard.py --check   Exit 0 = heute noch nichts, Exit 1 = schon gelaufen
  scripts/day_guard.py --mark    heutiges Datum eintragen

Mehrere Workflows brauchen getrennte Marken - sonst sperrt der eine den
anderen aus, obwohl beide am selben Tag laufen sollen:

  scripts/day_guard.py --check --name sammelfolge
"""

import argparse
import datetime
import json
import pathlib
import sys

STATE = pathlib.Path(__file__).resolve().parent.parent / "episodes" / "state.json"


def heute() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")


def laden() -> dict:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--mark", action="store_true")
    ap.add_argument("--name", default="autopilot",
                    help="eigene Marke je Workflow")
    args = ap.parse_args()

    state = laden()
    # "last_run" bleibt der Schluessel des Autopiloten, damit vorhandene
    # Staende weiter gelten. Andere Workflows bekommen einen eigenen.
    schluessel = "last_run" if args.name == "autopilot" else f"last_run_{args.name}"
    letzter = state.get(schluessel)

    if args.check:
        if letzter == heute():
            print(f"[{args.name}] Heute ({heute()}) schon gelaufen - uebersprungen.")
            sys.exit(1)
        print(f"[{args.name}] Heute ({heute()}) noch nichts" +
              (f", zuletzt am {letzter}." if letzter else "."))
        sys.exit(0)

    if args.mark:
        state[schluessel] = heute()
        state["runs"] = state.get("runs", 0) + 1
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2),
                         encoding="utf-8")
        print(f"[{args.name}] Eingetragen: {heute()} (Lauf Nr. {state['runs']})")
        return

    ap.error("--check oder --mark angeben")


if __name__ == "__main__":
    main()
