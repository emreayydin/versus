# versus — "A vs B: What's the Difference?"

Englischer YouTube-Kanal, der in jedem Video genau zwei Dinge aus Geld und
Wirtschaft gegenüberstellt. Vollautomatisch: Skript, Stimme, Zeichnung,
Thumbnail, Upload.

## Warum ausgerechnet dieses Format

Auf dem deutschen Schwesterkanal [Strichrechnung](../doodle-finanz) wurde
gemessen, welche Folge gehalten wird:

| gesehener Anteil | Aufrufe | Folge |
|---:|---:|---|
| **89,9 %** | **13** | Anleihe vs. Aktie – was ist der Unterschied? |
| 3,9 – 27,9 % | 1–3 | zwölf „Warum …"-Erklärfolgen |

Median über alle: **11,8 %**. Die eine Vergleichsfolge holte **39 % aller
Kanalaufrufe**. Ein Vergleich baut eine Frage auf, die sich erst am Ende
schließt — „Warum passiert X" beantwortet sich in der Überschrift halb von
selbst.

Ein Video ist statistisch dünn. Es ist aber das einzige gemessene Signal,
das vorliegt, und es deckt sich mit der Mechanik des Shorts-Feeds.

**Deshalb ist die Vergleichsstruktur hier erzwungen, nicht empfohlen.**
`versus_gen.py` verwirft jede Folge, die nicht beide Begriffe nennt oder
keinen Satz hat, der mit „The difference" beginnt.

## Zielkanal

**„Exit"** — `UC_FrWjKB66YyV9AeKPaEHIA`, Brand-Konto unter
`Emres Google-Konto (Adresse nicht im Repo)`. Am 31.08.2026 übernommen: **leer**, 0 Abonnenten,
0 Videos, 0 Aufrufe. Details und offene Punkte in `kanal.json`.

**Schon geprüft und in Ordnung:** Die Zielgruppen-Einstellung des Kanals steht
auf „für jedes Video prüfen" — der Kanal zwingt also **nicht** „speziell für
Kinder" auf alle Videos. Punkt 2 der Liste unten ist damit erledigt.

**Der Kanalname passt noch nicht.** „Exit" sagt nichts über das Format. Eine
Umbenennung ist zweimal in vierzehn Tagen möglich.

## Bevor der erste Upload läuft — die Liste, an der drei Kanäle gescheitert sind

Jeder Punkt hier hat schon einmal einen Kanal gekostet.

1. **OAuth-Zustimmungsbildschirm auf „In Produktion" stellen.** Steht er auf
   „Test", läuft das Refresh-Token nach sieben Tagen ab und das
   Veröffentlichen scheitert **still**. Genau daran ist `youtube-shorts-bot`
   gestorben.
2. ~~**Kanal auf „nicht speziell für Kinder" stellen**~~ — bei „Exit" bereits
   in Ordnung (steht auf „für jedes Video prüfen"). Zur Erinnerung, warum es
   zählt: — Studio → Einstellungen
   → Kanal → Erweiterte Einstellungen. Die kanalweite Angabe überschreibt
   jedes einzelne Video und schaltet Kommentare, Benachrichtigungen und
   Teilen ab. Daran ist `lino-show` gestorben.
3. **Analytics-Zugang von Anfang an einrichten**, nicht später. Ohne ihn ist
   jede Aussage über „was funktioniert" geraten. Zweiter OAuth-Durchlauf mit
   `yt-analytics.readonly`, Token als Secret `YOUTUBE_ANALYTICS_TOKEN`.
   **Achtung beim Kanal-Wählen:** Der Zustimmungsbildschirm listet
   **Brand-Konto-Namen**, nicht Kanalnamen — und eine Kanalumbenennung
   benennt das Brand-Konto nicht mit um.
4. **Lokalen Generator verwenden.** Skripte und Themen kommen standardmäßig
   aus einer lokalen Vergleichsbank; ein externer Textdienst ist nicht nötig.
5. **Neuer Kanal, kein umgewidmeter.** Ein Kanal mit fremder Vorgeschichte
   trägt deren Signale weiter — siehe Lino → Strichrechnung.

## Secrets

| Secret | wofür |
|---|---|
| `YOUTUBE_TOKEN_JSON` | Upload (`youtube.upload`) |
| `YOUTUBE_ANALYTICS_TOKEN` | Zahlen lesen (`yt-analytics.readonly`) |

## Betrieb

```bash
./venv/bin/python scripts/versus_gen.py --next          # Skript schreiben
./venv/bin/python scripts/make_episode.py --episode <slug> --lang en
./venv/bin/python scripts/publish.py --episode <slug> --publish
```

`--trocken` beim Generator gibt das Ergebnis aus, ohne etwas abzulegen —
gut, um den Prompt zu prüfen, ohne die Themenliste zu verbrauchen.

## Zeitplan

| Workflow | Zeit | Was |
|---|---|---|
| `autopilot.yml` | 13/15/17/19/21 UTC | bis zu 6 Shorts/Tag, selbstgedrosselt |
| `sammelfolge.yml` | Mo/Mi/Fr 16 UTC | Langvideo aus fertigen Kapiteln |

**Bewusst nur fünf Trigger statt dreizehn.** GitHub verschluckt geplante
Läufe, wenn ein Konto zu viele davon hat: Als der dritte Bot dazukam, fiel
die Gesamtzahl ausgelöster Läufe von 19 auf 6 pro Tag. Über-Planung macht es
schlimmer, nicht besser.

**Die Sammelfolge ist der einzige Weg zur Monetarisierung.**
Shorts-Wiedergabezeit zählt **nicht** für die 4.000 Stunden. Bei 3 Langvideos
pro Woche à 10 Minuten und 40 % gesehenem Anteil braucht es rund **385
Aufrufe je Langvideo**, um in einem Jahr auf 4.000 Stunden zu kommen.

## Inhaltliche Grenze

Der Kanal erklärt, er empfiehlt nicht. Keine Kaufaufrufe, keine konkreten
Wertpapiere, keine Renditeversprechen. Durchgesetzt in `versus_gen.py` über
die Liste `VERBOTEN` — mechanisch geprüft, nicht nur im Prompt erbeten. Eine
verstoßende Folge wird verworfen und neu geschrieben.

Grund: Anlageberatung ist erlaubnispflichtig. Ein Prompt hält bei sechs
unbeaufsichtigten Uploads täglich nicht zuverlässig.

## Offen

- **Eigene Vergleichsszene.** Zurzeit rendert die Folge in der Bildsprache
  von Strichrechnung: eine Figur, ein Symbol. Das Format lebt aber vom
  Nebeneinander — zwei Spalten, links A, rechts B. Das ist der stärkste
  offene Hebel auf die Zuschauerbindung.
- **edge-tts ist lizenzrechtlich Graubereich** für kommerzielle Nutzung.
  Vor der Monetarisierung auf Azure AI Speech wechseln (~1,60 USD/Monat),
  betrifft nur `build_voice.py`.
