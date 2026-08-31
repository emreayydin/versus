#!/usr/bin/env python3
"""
Sichtbarkeit hochgeladener Videos aendern.

Achtung Scope: videos.insert geht mit youtube.upload, videos.update NICHT.
Dafuer braucht es youtube.force-ssl. Wenn dieses Skript mit 403/
insufficientPermissions abbricht, muss das Token mit dem groesseren Scope
neu erzeugt werden (scripts/authorize.py).

  ./venv/bin/python scripts/set_privacy.py --lang de --privacy public --ids ABC,DEF
"""

import argparse
import json
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOKEN_DIR = ROOT / "tokens"

# force-ssl deckt Upload, Aendern und Playlists ab.
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
UPLOAD_ONLY = ["https://www.googleapis.com/auth/youtube.upload"]


def service(lang: str):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    raw = os.environ.get(f"YOUTUBE_TOKEN_{lang.upper()}")
    path = TOKEN_DIR / f"youtube_{lang}.json"
    if raw:
        data = json.loads(raw)
        creds = Credentials(
            token=data.get("token"), refresh_token=data.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=data.get("client_id"), client_secret=data.get("client_secret"),
            scopes=data.get("scopes") or UPLOAD_ONLY,
        )
    elif path.exists():
        data = json.loads(path.read_text())
        creds = Credentials.from_authorized_user_file(str(path), data.get("scopes") or UPLOAD_ONLY)
    else:
        raise SystemExit(f"Kein Token fuer '{lang}'")

    print(f"Token-Scopes: {data.get('scopes')}")
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build("youtube", "v3", credentials=creds)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="de")
    ap.add_argument("--privacy", required=True,
                    choices=["private", "unlisted", "public"])
    ap.add_argument("--ids", required=True, help="Video-IDs, kommagetrennt")
    args = ap.parse_args()

    yt = service(args.lang)
    ids = [i.strip() for i in args.ids.split(",") if i.strip()]

    for vid in ids:
        try:
            current = yt.videos().list(part="status,snippet", id=vid).execute()
            if not current.get("items"):
                print(f"  {vid}: nicht gefunden")
                continue
            item = current["items"][0]
            status = item["status"]
            status["privacyStatus"] = args.privacy
            # Made for Kids beibehalten - niemals implizit zuruecksetzen
            status["selfDeclaredMadeForKids"] = True
            yt.videos().update(part="status", body={"id": vid, "status": status}).execute()
            print(f"  {vid}: {args.privacy}  ({item['snippet']['title'][:48]})")
        except Exception as exc:
            print(f"  {vid}: FEHLER {str(exc)[:200]}")


if __name__ == "__main__":
    main()
