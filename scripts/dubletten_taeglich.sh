#!/bin/bash
# Taeglicher Lauf von dubletten_privat.py (launchd com.emre.versus.dubletten).
# Laeuft 08:30 Berlin, kurz vor dem Kontingent-Reset (Mitternacht Pazifik),
# wenn die Uploads des Tages durch sind. Entfernt sich selbst, sobald alles privat ist.
cd /Users/emre.cya/Projects/versus || exit 1
MELDEN="/usr/bin/python3 /Users/emre.cya/Projects/kanal-waechter/melden.py"
AUSGABE=$(/Users/emre.cya/Projects/youtube-shorts-bot/venv/bin/python -u scripts/dubletten_privat.py 2>&1)
CODE=$?
echo "=== $(date '+%F %T') (exit $CODE)"; echo "$AUSGABE"
if [ $CODE -ne 0 ] && echo "$AUSGABE" | grep -q "quotaExceeded"; then
  echo "Kontingent heute aufgebraucht, morgen weiter."; exit 0
fi
if [ $CODE -ne 0 ]; then
  $MELDEN --wichtig "Dubletten-Skript fehlgeschlagen" "$(echo "$AUSGABE" | tail -3)"
  exit $CODE
fi
ANZAHL=$(echo "$AUSGABE" | grep -c -- '-> privat')
if echo "$AUSGABE" | grep -q "keine offenen Kopien"; then
  $MELDEN "Difference Money: Dubletten erledigt" "Letzter Lauf: $ANZAHL privat gestellt. Alle Extra-Kopien sind privat, Job entfernt."
  launchctl bootout gui/$(id -u)/com.emre.versus.dubletten
  rm -f /Users/emre.cya/Library/LaunchAgents/com.emre.versus.dubletten.plist
fi
