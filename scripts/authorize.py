#!/usr/bin/env python3
"""
Einmalige OAuth-Freigabe je Sprachkanal.

Oeffnet den Browser, du waehlst das Google-Konto und danach den RICHTIGEN
KANAL aus. Das ist der Schritt, bei dem am haeufigsten der falsche Kanal
erwischt wird - YouTube zeigt bei mehreren Kanaelen eine Auswahl, und die
Vorauswahl ist selten die gewuenschte.

  ./venv/bin/python scripts/authorize.py --lang de              # Upload
  ./venv/bin/python scripts/authorize.py --lang de --analytics  # Zahlen

Voraussetzung: client_secrets.json im Projektstamm (Google Cloud ->
YouTube Data API v3 aktivieren -> OAuth-Client vom Typ "Desktop").

WICHTIG: Den OAuth-Zustimmungsbildschirm auf "Produktion" stellen. Bleibt
er auf "Test", laeuft das Refresh-Token nach 7 Tagen ab und die
Veroeffentlichung schlaegt still fehl - genau das ist bei
youtube-shorts-bot passiert.
"""

import argparse
import pathlib

from google_auth_oauthlib.flow import InstalledAppFlow

ROOT = pathlib.Path(__file__).resolve().parent.parent
UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
ANALYTICS_SCOPE = "https://www.googleapis.com/auth/yt-analytics.readonly"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", required=True,
                    help="Sprachkuerzel, z.B. de en es fr pt")
    ap.add_argument("--secrets", default=str(ROOT / "client_secrets.json"))
    ap.add_argument("--analytics", action="store_true",
                    help="Lesezugriff auf die Zahlen statt Upload-Recht")
    args = ap.parse_args()

    secrets = pathlib.Path(args.secrets)
    if not secrets.exists():
        raise SystemExit(
            f"Fehlt: {secrets}\n"
            "Google Cloud Console -> APIs & Dienste -> Anmeldedaten ->\n"
            "OAuth-Client-ID erstellen -> Anwendungstyp 'Desktop' ->\n"
            "JSON herunterladen und hier ablegen."
        )

    token_dir = ROOT / "tokens"
    token_dir.mkdir(exist_ok=True)

    # Getrennte Token statt eines mit beiden Rechten: Das Upload-Token
    # liegt in GitHub-Secrets und wird taeglich unbeaufsichtigt benutzt.
    # Es soll genau eine Sache duerfen. Ein Leserecht daneben waere
    # bequem und genau deshalb falsch.
    if args.analytics:
        scopes = [ANALYTICS_SCOPE]
        target = token_dir / f"analytics_{args.lang}.json"
        secret_name = "YOUTUBE_ANALYTICS_TOKEN"
    else:
        scopes = [UPLOAD_SCOPE]
        target = token_dir / f"youtube_{args.lang}.json"
        secret_name = f"YOUTUBE_TOKEN_{args.lang.upper()}"

    if target.exists():
        print(f"{target} existiert bereits. Loeschen, um neu zu autorisieren.")
        return

    was = "Zahlen (Lesezugriff)" if args.analytics else "Upload"
    print(f"Autorisierung fuer '{args.lang}' - Bereich: {was}.")
    print("Im Browser: Konto waehlen -> DEN PASSENDEN KANAL waehlen -> zulassen.\n")

    flow = InstalledAppFlow.from_client_secrets_file(str(secrets), scopes)
    creds = flow.run_local_server(port=0)
    target.write_text(creds.to_json(), encoding="utf-8")

    print(f"\nGespeichert: {target}")
    print("Fuer GitHub Actions als Secret hinterlegen:")
    print(f"  gh secret set {secret_name} < {target}")


if __name__ == "__main__":
    main()
