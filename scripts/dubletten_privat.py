#!/usr/bin/env python3
"""Doppelte Shorts von The Difference Money auf privat stellen.

Liest die "extra"-IDs aus kanal-waechter/difference-money-dubletten-*.md,
prueft fuer jede ID Kanal und Titel und setzt sie dann auf privat. Die
meistgesehene Kopie jedes Titels bleibt unangetastet.

Die Upload-Tokens duerfen keine Videos aendern. Dieses Skript holt deshalb
beim ersten Lauf ein eigenes Token (Bereich youtube.force-ssl, gespeichert
in tokens/verwalten_en.json, nicht im Git). Im Zustimmungsfenster das
Brand-Konto "Exit" waehlen.

Kontingent: videos.update kostet 50 Einheiten. Der Autopilot braucht taeglich
9.600 von 10.000 Einheiten. Deshalb hoechstens --max Videos pro Lauf
(Standard 7 = 350 Einheiten), der Rest am naechsten Tag. Bereits private
Videos werden uebersprungen, ein zweiter Lauf macht einfach weiter.

  ./venv/bin/python scripts/dubletten_privat.py --trocken   nur anzeigen
  ./venv/bin/python scripts/dubletten_privat.py             bis zu 7 umstellen
"""
import argparse
import glob
import json
import pathlib
import re
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

ROOT = pathlib.Path(__file__).resolve().parent.parent
KANAL = "UC_FrWjKB66YyV9AeKPaEHIA"
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
TOKEN = ROOT / "tokens" / "verwalten_en.json"
LISTEN = "/Users/emre.cya/Projects/kanal-waechter/difference-money-dubletten-*.md"


def extra_ids() -> list[tuple[str, str]]:
    datei = sorted(glob.glob(LISTEN))[-1]
    paare = []
    for zeile in open(datei, encoding="utf-8"):
        m = re.match(r"- \*\*(.+?)\*\* \(\d+x\).*extra: (.+)$", zeile.strip())
        if m:
            for vid in re.findall(r"`([^`]+)`", m.group(2)):
                paare.append((vid, m.group(1)))
    return paare


def dienst():
    creds = None
    if TOKEN.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(ROOT / "client_secrets.json"), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN.write_text(creds.to_json(), encoding="utf-8")
    return build("youtube", "v3", credentials=creds)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trocken", action="store_true")
    ap.add_argument("--max", type=int, default=7)
    args = ap.parse_args()

    paare = extra_ids()
    print(f"{len(paare)} Extra-Kopien in der Liste")
    if args.trocken:
        for vid, titel in paare:
            print(f"  {vid}  {titel}")
        return

    yt = dienst()
    eigener = yt.channels().list(part="id", mine=True).execute()["items"][0]["id"]
    if eigener != KANAL:
        sys.exit(f"Falscher Kanal ({eigener}) - im Zustimmungsfenster 'Exit' waehlen. "
                 f"Token loeschen: rm {TOKEN}")

    erledigt = 0
    for start in range(0, len(paare), 50):
        stueck = paare[start:start + 50]
        antwort = yt.videos().list(part="snippet,status",
                                   id=",".join(v for v, _ in stueck)).execute()
        info = {x["id"]: x for x in antwort.get("items", [])}
        for vid, titel in stueck:
            x = info.get(vid)
            if x is None:
                print(f"  {vid}  nicht gefunden - uebersprungen")
                continue
            if x["snippet"]["channelId"] != KANAL or x["snippet"]["title"].lower() != titel.lower():
                print(f"  {vid}  Kanal/Titel passt nicht - uebersprungen")
                continue
            if x["status"]["privacyStatus"] == "private":
                continue
            if erledigt >= args.max:
                print(f"Limit {args.max} erreicht - Rest beim naechsten Lauf.")
                return
            status = dict(x["status"])
            status["privacyStatus"] = "private"
            body = {"id": vid, "status": {k: status[k] for k in (
                "privacyStatus", "embeddable", "license", "publicStatsViewable",
                "selfDeclaredMadeForKids") if k in status}}
            yt.videos().update(part="status", body=body).execute()
            erledigt += 1
            print(f"  {vid}  -> privat  ({titel})")
    print(f"Fertig: {erledigt} umgestellt, keine offenen Kopien mehr.")


if __name__ == "__main__":
    main()
