#!/usr/bin/env python3
"""
Zahlen vom Kanal holen: was laeuft, was nicht, wie weit bis zur Grenze.

  ./venv/bin/python scripts/analyze.py --tage 28
  ./venv/bin/python scripts/analyze.py --tage 90 --json

EINGERICHTET AM 27.08.2026. Falls es je neu gemacht werden muss:

  ACHTUNG BEIM KANAL WAEHLEN. Der Zustimmungsbildschirm listet
  BRAND-KONTO-Namen, nicht Kanalnamen - und eine Kanalumbenennung
  benennt das Brand-Konto NICHT mit um. Strichrechnung heisst dort
  "Emre_451". Wer nach "Strichrechnung" sucht, findet nichts und waehlt
  den falschen Kanal.

  Geprueft wurde es so: die zurueckgegebenen Video-IDs mit den
  Upload-Logs abgeglichen (ASqQB3b-j2Q und uFz2F5VGbk0 stehen in den
  Autopilot-Logs von lino-show). Der Filter video==<id> taugt dafuer
  NICHT - ein Video mit null Aufrufen liefert nie eine Zeile, egal wem
  es gehoert.

BRAUCHT EINEN EIGENEN ZUGANG.
Das Upload-Token reicht nicht - es darf hochladen und sonst nichts. Fuer
Zahlen ist der Bereich yt-analytics.readonly noetig:

  1. console.cloud.google.com -> APIs & Dienste -> Bibliothek
     -> "YouTube Analytics API" aktivieren
  2. ./venv/bin/python scripts/authorize.py --lang de --analytics
  3. Ergebnis tokens/analytics_de.json, in CI als YOUTUBE_ANALYTICS_TOKEN

Ohne das bricht dieses Skript mit einer klaren Meldung ab statt mit
einem Traceback - und niemand faengt an, Zahlen zu raten.
"""

import argparse
import datetime as dt
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOKEN_DIR = ROOT / "tokens"
SCOPES = ["https://www.googleapis.com/auth/yt-analytics.readonly"]

# Schwellen des YouTube-Partnerprogramms.
#
# ACHTUNG: YouTube aendert diese Bedingungen gelegentlich, und sie
# unterscheiden sich je nach Land. Die Zahlen hier sind der Stand bei
# Einrichtung - wer darauf plant, prueft sie zuerst auf der offiziellen
# Seite nach, statt dieser Datei zu glauben.
# Am 27.08.2026 in YouTube Studio unter "Einnahmen" abgelesen, nicht aus
# dem Gedaechtnis. Eine kleinere Stufe mit 500 Abos und 3.000 Stunden
# wird diesem Kanal NICHT angeboten - solche Stufen gibt es, aber nicht
# ueberall. Massgeblich ist, was Studio fuer diesen Kanal anzeigt.
SCHWELLEN = {
    "abonnenten": 1000,
    "wiedergabestunden": 4000,      # gueltige Stunden, letzte 365 Tage
    "shorts_aufrufe": 10_000_000,   # letzte 90 Tage, Alternative
}


def credentials():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    roh = os.environ.get("YOUTUBE_ANALYTICS_TOKEN")
    datei = TOKEN_DIR / "analytics_de.json"

    if roh:
        d = json.loads(roh)
        creds = Credentials(
            token=d.get("token"), refresh_token=d.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=d.get("client_id"), client_secret=d.get("client_secret"),
            scopes=SCOPES,
        )
    elif datei.exists():
        creds = Credentials.from_authorized_user_file(str(datei), SCOPES)
    else:
        raise SystemExit(
            "\nKEIN ANALYTICS-ZUGANG.\n"
            "Dieses Skript kann keine Zahlen holen, und geraten wird hier\n"
            "nicht. Einrichten:\n"
            "  1. YouTube Analytics API im Cloud-Projekt aktivieren\n"
            "  2. ./venv/bin/python scripts/authorize.py --lang de --analytics\n"
            "  3. In CI: tokens/analytics_de.json als Secret\n"
            "     YOUTUBE_ANALYTICS_TOKEN hinterlegen\n"
        )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds


def frage(dienst, start, ende, metriken, dimensionen=None, sortierung=None,
          grenze=None):
    """Ein Bericht. Faellt auf weniger Metriken zurueck, wenn die API
    eine davon nicht kennt - Impressionen sind nicht auf jedem Kanal da."""
    def lauf(m):
        p = dict(ids="channel==MINE", startDate=start, endDate=ende, metrics=m)
        if dimensionen:
            p["dimensions"] = dimensionen
        if sortierung:
            p["sort"] = sortierung
        if grenze:
            p["maxResults"] = grenze
        return dienst.reports().query(**p).execute()

    try:
        return lauf(",".join(metriken))
    except Exception as err:
        knapp = [m for m in metriken if "impression" not in m.lower()]
        if knapp == metriken:
            raise
        # Impressionen und Klickrate liefert die API erst ab einer
        # gewissen Datenmenge. Bei einem Kanal mit acht Aufrufen fehlen
        # sie noch - das ist kein Fehler, nur zu frueh.
        print(f"  (Impressionen noch nicht verfuegbar: {str(err)[:60]})",
              file=sys.stderr)
        return lauf(",".join(knapp))


def zeilen(bericht):
    kopf = [s["name"] for s in bericht.get("columnHeaders", [])]
    return [dict(zip(kopf, r)) for r in bericht.get("rows", []) or []]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tage", type=int, default=28)
    ap.add_argument("--json", action="store_true", help="nur JSON ausgeben")
    args = ap.parse_args()

    from googleapiclient.discovery import build
    dienst = build("youtubeAnalytics", "v2", credentials=credentials())

    heute = dt.date.today()
    start = (heute - dt.timedelta(days=args.tage)).isoformat()
    ende = heute.isoformat()
    jahr = (heute - dt.timedelta(days=365)).isoformat()

    gesamt = zeilen(frage(dienst, start, ende, [
        "views", "estimatedMinutesWatched", "averageViewDuration",
        "averageViewPercentage", "subscribersGained", "subscribersLost",
        "impressions", "impressionClickThroughRate",
    ]))
    g = gesamt[0] if gesamt else {}

    # Fuer die Schwelle zaehlen zwoelf Monate, nicht der Berichtszeitraum.
    zwoelf = zeilen(frage(dienst, jahr, ende, ["estimatedMinutesWatched"]))
    stunden = (zwoelf[0]["estimatedMinutesWatched"] / 60) if zwoelf else 0

    videos = zeilen(frage(
        dienst, start, ende,
        ["views", "estimatedMinutesWatched", "averageViewPercentage",
         "impressions", "impressionClickThroughRate"],
        dimensionen="video", sortierung="-views", grenze=15))

    daten = {
        "zeitraum": {"von": start, "bis": ende, "tage": args.tage},
        "gesamt": g,
        "wiedergabestunden_12m": round(stunden, 1),
        "schwellen": SCHWELLEN,
        "videos": videos,
    }

    if args.json:
        print(json.dumps(daten, ensure_ascii=False, indent=2))
        return

    print(f"Kanal  |  letzte {args.tage} Tage")
    print("=" * 66)
    if not g or not g.get("views"):
        print("\nNoch keine Aufrufe im Zeitraum.")
    else:
        print(f"  Aufrufe            {g.get('views', 0):>10,.0f}")
        print(f"  Wiedergabeminuten  {g.get('estimatedMinutesWatched', 0):>10,.0f}")
        print(f"  Mittlere Dauer     {g.get('averageViewDuration', 0):>10,.0f} s"
              f"   ({g.get('averageViewPercentage', 0):.0f} % des Videos)")
        if g.get("impressions"):
            print(f"  Impressionen       {g['impressions']:>10,.0f}")
            print(f"  Klickrate          {g.get('impressionClickThroughRate', 0):>10.1f} %")
        netto = g.get("subscribersGained", 0) - g.get("subscribersLost", 0)
        print(f"  Abonnenten netto   {netto:>+10,.0f}")

    print("\nWeg zur Monetarisierung")
    print("-" * 66)
    print(f"  Wiedergabestunden (12 Monate)  {stunden:>10,.0f} von "
          f"{SCHWELLEN['wiedergabestunden']:,}"
          f"   {100*stunden/SCHWELLEN['wiedergabestunden']:5.1f} %")

    # Reicht das Tempo? Ohne diese Zeile sieht man den Rueckstand erst,
    # wenn es zu spaet ist.
    ziel = dt.date(2026, 12, 31)
    rest = (ziel - heute).days
    if rest > 0 and stunden > 0:
        pro_tag = stunden / max(1, (heute - dt.date(2026, 8, 27)).days or 1)
        hoch = stunden + pro_tag * rest
        print(f"  Bei diesem Tempo am {ziel}: {hoch:,.0f} Stunden "
              f"({'reicht' if hoch >= SCHWELLEN['wiedergabestunden'] else 'REICHT NICHT'})")
    print("  Abonnenten: siehe YouTube Studio (die Analytics-API liefert\n"
          "  nur die Veraenderung, nicht den Gesamtstand)")

    if videos:
        print(f"\nBeste Folgen ({len(videos)})")
        print("-" * 66)
        print(f"  {'Video':<14} {'Aufrufe':>8} {'Minuten':>8} {'gesehen':>8} {'CTR':>6}")
        for v in videos[:10]:
            ctr = v.get("impressionClickThroughRate")
            print(f"  {v['video']:<14} {v['views']:>8,.0f} "
                  f"{v['estimatedMinutesWatched']:>8,.0f} "
                  f"{v.get('averageViewPercentage', 0):>7.0f}% "
                  f"{(f'{ctr:.1f}%' if ctr is not None else '  -'):>6}")


if __name__ == "__main__":
    main()
