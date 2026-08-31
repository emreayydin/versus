#!/usr/bin/env python3
"""
Upload zu YouTube.

Sicherheitsvorgaben:
  * Ohne --publish passiert NICHTS. Standard ist Trockenlauf.
  * Auch mit --publish ist die Sichtbarkeit "private". Oeffentlich nur
    mit explizitem --privacy public.
  * selfDeclaredMadeForKids ist hart auf False verdrahtet.

WARUM "NICHT FUER KINDER" HIER DIE RICHTIGE ANGABE IST
Die Frage lautet nicht "duerfen Kinder das sehen", sondern "richtet sich
das Video an Kinder". Erklaervideos zu Zinsen, Inflation und Steuern tun
das nicht - Zielgruppe sind Erwachsene. Eine Falschangabe waere hier in
beide Richtungen ein Problem.

Nebenwirkung, die den Ausschlag gibt: Bei "Made for Kids" schaltet YouTube
Kommentare, Benachrichtigungen, Playlists und Endcards ab. Genau daran ist
der Kinderkanal an der Verbreitung gescheitert. Dieser Kanal hat diese
Bremse nicht.

  ./venv/bin/python scripts/publish.py --episode zinseszins            # Trockenlauf
  ./venv/bin/python scripts/publish.py --episode zinseszins --publish --privacy public
"""

import argparse
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOKEN_DIR = ROOT / "tokens"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# 27 = Bildung. Erklaervideos gehoeren dorthin, nicht in "Unterhaltung":
# die Kategorie steuert mit, wem YouTube das Video vorschlaegt.
CATEGORY_ID = "27"


def load_credentials(lang: str):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    env_key = f"YOUTUBE_TOKEN_{lang.upper()}"
    raw = os.environ.get(env_key)
    token_file = TOKEN_DIR / f"youtube_{lang}.json"

    if raw:
        data = json.loads(raw)
        creds = Credentials(
            token=data.get("token"),
            refresh_token=data.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=data.get("client_id"),
            client_secret=data.get("client_secret"),
            scopes=SCOPES,
        )
    elif token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
    else:
        raise SystemExit(
            f"Kein Token fuer '{lang}'.\n"
            f"  Lokal : {token_file}\n"
            f"  In CI : Umgebungsvariable {env_key}\n"
            f"Einmalig: EIGENES Google-Cloud-Projekt (nicht das des "
            f"Kinderkanals - das Kontingent haengt am Projekt) -> YouTube "
            f"Data API v3 -> OAuth-Client (Desktop) -> client_secrets.json "
            f"-> scripts/authorize.py --lang {lang}"
        )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds


def upload(lang: str, video: pathlib.Path, plan: dict, privacy: str,
           bild: pathlib.Path | None = None) -> str:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    service = build("youtube", "v3", credentials=load_credentials(lang))
    body = {
        "snippet": {
            "title": plan["titel"][:100],
            "description": plan["beschreibung"][:5000],
            "tags": plan.get("tags", [])[:30],
            "categoryId": CATEGORY_ID,
            "defaultLanguage": lang,
            "defaultAudioLanguage": lang,
        },
        "status": {
            "privacyStatus": privacy,
            # Nicht konfigurierbar. Siehe Modulkommentar.
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(str(video), chunksize=-1, resumable=True,
                            mimetype="video/mp4")
    antwort = service.videos().insert(
        part="snippet,status", body=body, media_body=media).execute()
    vid = antwort["id"]

    # Thumbnail nachreichen, falls vorhanden. Kostet 50 Einheiten - bei
    # sechs Uploads am Tag also 300 zusaetzlich (9.600 + 300 = 9.900 von
    # 10.000). Absichtlich nicht toedlich: scheitert es, ist das Video
    # trotzdem online, und ein fehlendes Thumbnail ist kein Ausfall.
    if bild and bild.exists():
        try:
            service.thumbnails().set(
                videoId=vid,
                media_body=MediaFileUpload(str(bild), mimetype="image/png"),
            ).execute()
            print("  Thumbnail gesetzt")
        except Exception as exc:
            print(f"  Thumbnail fehlgeschlagen (Video ist online): {exc}")
    return vid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", required=True)
    ap.add_argument("--lang", default="de")
    ap.add_argument("--publish", action="store_true",
                    help="ohne dieses Flag nur Trockenlauf")
    ap.add_argument("--privacy", default="private",
                    choices=["private", "unlisted", "public"])
    args = ap.parse_args()

    plan_datei = ROOT / "episodes" / args.episode / "plan.json"
    if not plan_datei.exists():
        raise SystemExit(f"Fehlt: {plan_datei}")
    plan = json.loads(plan_datei.read_text(encoding="utf-8"))

    video = ROOT / "out" / f"{args.episode}.mp4"
    modus = f"UPLOAD ({args.privacy})" if args.publish else "TROCKENLAUF"
    print(f"Folge '{args.episode}'  |  {modus}")
    print("Made for Kids: NEIN (fest verdrahtet)")
    print("=" * 66)

    if not video.exists():
        raise SystemExit(f"FEHLT: {video}")

    print(f"\n{video.name}  ({video.stat().st_size / 1048576:.1f} MB)")
    print(f"  Titel : {plan['titel']}")
    print(f"  Tags  : {', '.join(plan.get('tags', [])[:6])}")

    if not args.publish:
        print("\nTrockenlauf beendet. Mit --publish wirklich hochladen.")
        return

    try:
        bild = ROOT / "out" / f"{args.episode}.png"
        vid = upload(args.lang, video, plan, args.privacy, bild)
        print(f"  -> hochgeladen: https://youtu.be/{vid}")
    except Exception as exc:
        print(f"  -> FEHLER: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
