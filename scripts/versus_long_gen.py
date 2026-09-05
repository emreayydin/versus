#!/usr/bin/env python3
"""
Langfassung im Vergleichsformat: EIN Paar, acht bis zehn Minuten.

  ./venv/bin/python scripts/versus_long_gen.py --thema "Stocks vs Bonds"
  ./venv/bin/python scripts/versus_long_gen.py --next

WARUM NICHT DIE SAMMELFOLGE
Die alte Sammelfolge hing sechs fertige Shorts aneinander. Das kostet keine
neue Zeile Skript und ist genau deshalb schwach: Ein Short hat nach vierzig
Sekunden seinen Bogen erschoepft. Sechs davon hintereinander fangen sechsmal
neu an, und wer den Short schon kannte, sieht ihn ein zweites Mal.

Diese Fassung nimmt stattdessen EIN Paar und fuehrt es durch feste
Dimensionen. Jede Dimension ist ein eigener kleiner Spannungsbogen mit einer
eigenen Aufloesung - das ist es, was ueber acht Minuten traegt.

WARUM DAS UEBERHAUPT ZAEHLT
Shorts-Wiedergabezeit zaehlt NICHT fuer die 4.000-Stunden-Schwelle des
Partnerprogramms. Nur normale Videos. Der Kanal kann ueber Shorts beliebig
wachsen und trotzdem nie monetarisiert werden - die Langfassung ist die
einzige Tuer. Gemessen bei muslim-world-bot: 60.586 Shorts-Aufrufe in 90
Tagen, davon 331 Wiedergabestunden, aber nur 4 Stunden aus Langvideos.

Ueber acht Minuten schalten ausserdem Mid-Roll-Anzeigen frei.
"""

import argparse
import json
import os
import pathlib
import re
import sys
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
EPISODES = ROOT / "episodes_lang"
QUEUE = EPISODES / "queue.json"

MODELL = "claude-sonnet-5"
PLAN_VERSION = 1

POSEN = ["stehen", "denken", "zeigen", "jubeln", "sitzen", "achselzucken"]
ICONS = ["muenze", "stapel", "hoch", "runter", "kurve", "balken",
         "uhr", "haus", "korb", "bank", "prozent", "schere", "waage"]

# Die Dimensionen sind fest. Ein Modell, das sie selbst waehlen darf, waehlt
# jedes Mal andere - und dann ist es kein Format mehr, sondern ein Zufall.
DIMENSIONEN = [
    ("What it actually is", "Was die beiden Dinge im Kern sind"),
    ("Who pays whom",       "Wie das Geld tatsaechlich fliesst"),
    ("Risk",                "Was schiefgehen kann und wer es traegt"),
    ("Time",                "Laufzeit, Verfuegbarkeit, Geduld"),
    ("Taxes and costs",     "Was abgeht, bevor etwas ankommt"),
    ("Who each one suits",  "Fuer wen sich was eignet"),
]

# Gemessen am ersten Rendern: 1.180 Woerter ergaben 7,5 Minuten, also rund
# 157 Woerter je Minute. Fuer sichere neun Minuten braucht es etwa 1.400 -
# und Luft nach oben, weil Mid-Roll-Anzeigen erst ab acht Minuten greifen und
# knapp darunter zu landen den ganzen Zweck der Langfassung verfehlt.
WOERTER_PRO_MINUTE = 157
MIN_WOERTER, MAX_WOERTER = 1400, 2000   # ~9-13 Minuten
MAX_SATZ_ZEICHEN = 150
MAX_HOOK = 110
MAX_TITEL = 90

VERBOTEN = [
    "you should buy", "you should invest", "invest in", "buy now",
    "best investment", "guaranteed return", "guaranteed profit",
    "get rich", "make you rich", "financial freedom in",
    "double your money", "secret", "this one trick",
    "don't miss", "act now", "limited time", "i recommend",
    "my advice", "you must buy", "sell your", "hot tip",
]

VERBOTENER_EINSTIEG = [
    "in this video", "today we", "let's talk about", "welcome",
    "have you ever wondered", "many people ask", "hi ", "hey ",
    "in this episode", "so, ",
]

HINWEIS = ("This video explains two terms and how they differ. "
           "It is not financial advice and not a recommendation to buy or "
           "sell anything.")

# Nur die englischen Namen. Die deutsche Erlaeuterung stand hier frueher in
# derselben Zeile - das Modell hat sie prompt in die Ueberschrift uebernommen.
_DIM_LISTE = "\n".join(f'  {i+1}. "{n}"' for i, (n, _) in enumerate(DIMENSIONEN))
_DIM_ZWECK = "\n".join(f'  "{n}": {z}' for n, z in DIMENSIONEN)

SYSTEM = f"""You write the long-form episode for an English explainer channel
about money and economics. Landscape video, eight to eleven minutes, one voice
over simple stick-figure drawings.

THE FORMAT
One pair of things people confuse, taken apart across FIXED dimensions. Not a
list of tips, not several topics chained together — one comparison, followed
all the way through.

These are the sections, in this order, all of them:
{_DIM_LISTE}

Each section compares the SAME two things under that one heading. A section
that could stand alone about only one of them is wrong.

THE MOST IMPORTANT RULE
You explain, you never advise. Forbidden: telling anyone to buy or sell,
naming specific securities or tickers, promising returns, "get rich", secrets,
urgency. Allowed: explaining terms, showing mechanisms, working through number
examples, naming common misconceptions, historical context.

THE OPENING
At most {MAX_HOOK} characters for the first sentence. It names the confusion
or puts the two things in direct opposition. Never "In this video", never a
definition, never a greeting. The next two or three sentences promise what the
viewer will be able to tell apart by the end — they do not resolve it yet.

LENGTH
{MIN_WOERTER} to {MAX_WOERTER} words of spoken text in total, spread across the
sections. Each sentence at most {MAX_SATZ_ZEICHEN} characters, spoken English,
one thought per sentence. Write numbers as spoken ("a hundred dollars").
No bullet points, no brackets, no emojis, no section numbers read aloud.

EACH SECTION
- starts with one sentence that states the difference under this heading
- then three to six sentences that make it concrete, ideally with an example
- ends without a summary; the next heading carries on

THE CLOSING SECTION
After the last dimension, two to four sentences: the one line that separates
the two things, and where that difference actually shows up in a real decision.
It sells nothing.

DRAWINGS
Every sentence gets a pose from: {", ".join(POSEN)}
Optionally one symbol beside the figure, only from:
  muenze, stapel, hoch, runter, kurve, balken, uhr, haus, korb, bank,
  prozent, schere, waage
Use "waage" where the difference itself is named. About half the sentences
need no symbol at all — a wrong one is worse than none.
Optionally one bold word drawn into the picture, at most twelve characters.

CHARTS
Where a sentence lives on numbers, give a chart instead of pose and symbol:
  "diagramm": {{"art": "balken", "werte": [1000, 700],
               "achse": ["Stocks", "Bonds"], "einheit": "$"}}
"balken" for a comparison (two to four values), "linie" for development over
time (four to eight). The numbers must match what the sentence says. At most
THREE charts in the whole episode. A sentence with a chart still needs a pose.

TITLE AND DESCRIPTION
Title at most {MAX_TITEL} characters, ends with the question:
  "Stocks vs Bonds - What's the Difference?"
Description: three or four sentences, plain, no hype.

Answer with JSON ONLY:
{{"titel": "...", "beschreibung": "...", "tags": ["..."],
  "hashtags": ["#..."], "begriffe": ["A", "B"],
  "abschnitte": [
    {{"ueberschrift": "Opening",
      "saetze": [{{"text": "...", "pose": "denken", "icon": null,
                  "wort": null, "stimmung": 0}}]}},
    {{"ueberschrift": "What it actually is", "saetze": [...]}},
    ... one per dimension, in order ...
    {{"ueberschrift": "The difference", "saetze": [...]}}
  ]}}
"""

SEED = [
    "Stocks vs Bonds", "Saving vs Investing", "Rent vs Buy",
    "Debit card vs Credit card", "Assets vs Liabilities",
    "Inflation vs Deflation", "ETF vs Mutual fund",
    "Fixed rate vs Variable rate", "Income vs Wealth",
    "Revenue vs Profit", "Nominal vs Real return",
    "Term vs Whole life insurance", "Pension vs Annuity",
    "Value stock vs Growth stock", "Liquidity vs Solvency",
]


def client():
    import anthropic
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY fehlt.")
    return anthropic.Anthropic()


def ask(prompt, system, max_tokens=16000, versuche=3):
    """
    Wiederholt bei leerer Antwort. Das Modell liefert gelegentlich einen
    Block ohne Text zurueck; ohne diese Schleife stirbt dann die ganze Folge
    an einem einzelnen Abschnitt - nachdem die vorherigen schon bezahlt sind.
    """
    letzter = ""
    for versuch in range(1, versuche + 1):
        m = client().messages.create(
            model=MODELL, max_tokens=max_tokens, system=system,
            messages=[{"role": "user", "content": prompt}])
        text = "".join(b.text for b in m.content if b.type == "text").strip()
        if text:
            if m.stop_reason == "max_tokens":
                print(f"    (Antwort am Token-Limit abgeschnitten, "
                      f"{len(text)} Zeichen)", file=sys.stderr)
            return text
        letzter = m.stop_reason or "?"
        print(f"    leere Antwort (stop_reason={letzter}), "
              f"Versuch {versuch}/{versuche}", file=sys.stderr)
    raise ValueError(f"Dreimal leere Antwort (stop_reason={letzter}).")


def parse_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\n|\n```$", "", text)
    i, j = text.find("{"), text.rfind("}")
    if i < 0 or j < 0:
        # Meist abgeschnitten, weil die Antwort ans Token-Limit stiess. Die
        # Meldung soll das sagen, statt nur "kein JSON" - sonst sucht man den
        # Fehler im Prompt statt in der Laenge.
        raise ValueError(
            f"Keine vollstaendige JSON-Struktur ({len(text)} Zeichen, "
            f"Anfang: {text[:80]!r}). Wahrscheinlich abgeschnitten.")
    return json.loads(text[i:j + 1])


def frage_json(prompt, system, max_tokens, versuche=3):
    """
    Fragen, bis brauchbares JSON zurueckkommt.

    Das Modell liefert gelegentlich eine kaputte Struktur - ein nicht
    entwertetes Anfuehrungszeichen reicht. Ohne diese Schleife stirbt daran
    der ganze unbeaufsichtigte Lauf, und zwar nachdem die vorherigen
    Abschnitte schon bezahlt sind.
    """
    letzter = None
    for versuch in range(1, versuche + 1):
        roh = ask(prompt, system, max_tokens=max_tokens)
        try:
            return parse_json(roh)
        except (ValueError, json.JSONDecodeError) as fehler:
            letzter = fehler
            print(f"    unbrauchbares JSON ({type(fehler).__name__}: "
                  f"{str(fehler)[:70]}), Versuch {versuch}/{versuche}",
                  file=sys.stderr)
            prompt = (prompt + "\n\nThe previous answer was not valid JSON. "
                      "Return only a single valid JSON object, with every "
                      "quote inside a string properly escaped.")
    raise SystemExit(f"Dreimal unbrauchbares JSON: {letzter}")


def alle_saetze(folge):
    return [s for a in folge.get("abschnitte", []) for s in a.get("saetze", [])]


def pruefe(folge):
    """Was die Folge unbrauchbar macht. Leere Liste = in Ordnung."""
    m = []
    absch = folge.get("abschnitte") or []
    saetze = alle_saetze(folge)

    # Das Format selbst: alle Dimensionen, in dieser Reihenfolge.
    erwartet = ["Opening"] + [n for n, _ in DIMENSIONEN] + ["The difference"]
    ist = [str(a.get("ueberschrift", "")).strip() for a in absch]
    if ist != erwartet:
        fehlend = [x for x in erwartet if x not in ist]
        m.append("Abschnitte stimmen nicht" +
                 (f", es fehlen: {fehlend}" if fehlend else f" (Reihenfolge: {ist})"))

    woerter = sum(len((s.get("text") or "").split()) for s in saetze)
    if not (MIN_WOERTER <= woerter <= MAX_WOERTER):
        m.append(f"{woerter} Woerter, erlaubt sind {MIN_WOERTER}-{MAX_WOERTER}")

    volltext = " ".join(s.get("text", "") for s in saetze).lower()
    for wort in VERBOTEN:
        if wort in volltext:
            m.append(f"verbotene Wendung: '{wort}'")

    if saetze:
        hook = saetze[0].get("text", "").strip()
        if len(hook) > MAX_HOOK:
            m.append(f"Einstieg {len(hook)} Zeichen, erlaubt sind {MAX_HOOK}")
        for a in VERBOTENER_EINSTIEG:
            if hook.lower().startswith(a):
                m.append(f"Einstieg beginnt mit '{a}'")

    for i, s in enumerate(saetze):
        t = (s.get("text") or "").strip()
        if len(t) > MAX_SATZ_ZEICHEN:
            m.append(f"Satz {i+1}: {len(t)} Zeichen, erlaubt sind {MAX_SATZ_ZEICHEN}")
        if s.get("pose") not in POSEN:
            m.append(f"Satz {i+1}: Pose '{s.get('pose')}' gibt es nicht")
        if s.get("icon") and s["icon"] not in ICONS:
            m.append(f"Satz {i+1}: Symbol '{s['icon']}' gibt es nicht")

    begriffe = [str(b).strip() for b in (folge.get("begriffe") or []) if str(b).strip()]
    if len(begriffe) != 2:
        m.append("Es muessen genau zwei Begriffe verglichen werden")
    else:
        for b in begriffe:
            if b.lower().split()[0].rstrip("s") not in volltext:
                m.append(f"Begriff '{b}' kommt im gesprochenen Text nicht vor")

    # Jede Dimension muss BEIDE Begriffe behandeln, sonst ist es kein Vergleich
    if len(begriffe) == 2:
        for a in absch:
            u = str(a.get("ueberschrift", ""))
            if u in ("Opening",):
                continue
            txt = " ".join(s.get("text", "") for s in a.get("saetze", [])).lower()
            fehlt = [b for b in begriffe
                     if b.lower().split()[0].rstrip("s") not in txt]
            if len(fehlt) == 2:
                m.append(f"Abschnitt '{u}' nennt keinen der beiden Begriffe")

    t = (folge.get("titel") or "").strip()
    if not t or len(t) > MAX_TITEL:
        m.append(f"Titel {len(t)} Zeichen, erlaubt sind {MAX_TITEL}")

    n = sum(1 for s in saetze if s.get("diagramm"))
    if n > 3:
        m.append(f"{n} Diagramme, hoechstens drei")
    return m


_KOPFZEILEN = "\n".join(
    [f'  1. "Opening"']
    + [f'  {i+2}. "{n}"' for i, (n, _) in enumerate(DIMENSIONEN)]
    + [f'  {len(DIMENSIONEN)+2}. "The difference"'])

GERUEST_SYSTEM = f"""You plan one long-form episode for an English channel about
money and economics. You do NOT write the spoken text yet - only the plan.

Answer with JSON ONLY:
{{"titel": "... - What's the Difference?", "beschreibung": "3-4 plain sentences",
 "tags": ["..."], "hashtags": ["#..."], "begriffe": ["A", "B"],
 "abschnitte": [{{"ueberschrift": "<exact heading>", "kern": "one sentence on
 what this section must establish about BOTH things"}}]}}

The headings, in this order, all of them, copied EXACTLY as quoted - no
additions, no translations, no explanations appended:
{_KOPFZEILEN}

What each section is for - this is guidance for the "kern" field and must NOT
appear in the heading:
{_DIM_ZWECK}

Title at most {MAX_TITEL} characters. No advice, no recommendations, no
specific securities."""


WOERTER_PRO_SATZ = 16


def _abschnitt_system(begriffe, ueberschrift, kern, worte):
    # Die Satzzahl folgt aus dem Wortbudget. Stand hier eine feste Spanne
    # ("drei bis sechs Saetze"), gewann sie gegen die Wortzahl: acht
    # Abschnitte à sieben Saetze ergaben 963 statt 1700 Woerter.
    weitere = max(4, round(worte / WOERTER_PRO_SATZ) - 1)
    return f"""You write ONE section of a long-form episode comparing
{begriffe[0]} and {begriffe[1]} for an English money channel. Landscape video,
one voice over stick-figure drawings.

This section is "{ueberschrift}". It must establish: {kern}

It compares BOTH things under this heading. A section about only one of them is
wrong. It opens with one sentence stating the difference under this heading,
then {weitere} more sentences that make it concrete - each one a separate
example, number, or consequence, not a restatement. No summary at the end - the
next heading carries on. Around {worte} words in total, and the word count
matters: a short section leaves the episode under length.

You explain, you never advise. No telling anyone to buy or sell, no specific
securities or tickers, no promised returns, no urgency.

Each sentence at most {MAX_SATZ_ZEICHEN} characters, spoken English, one
thought each. Numbers written as spoken. No bullet points, no brackets.

Every sentence gets a pose from: {", ".join(POSEN)}
Optionally one symbol, only from: {", ".join(ICONS)}
Use "waage" where the difference itself is named. About half the sentences need
no symbol. Optionally one bold word, at most twelve characters.

Where a sentence lives on numbers you may give a chart instead of pose+symbol:
  "diagramm": {{"art": "balken", "werte": [1000, 700],
               "achse": ["{begriffe[0]}", "{begriffe[1]}"], "einheit": "$"}}
At most one chart in this section, and only if the numbers appear in the text.

Answer with JSON ONLY:
{{"saetze": [{{"text": "...", "pose": "denken", "icon": null, "wort": null,
              "stimmung": 0}}]}}"""


def erzeuge(thema, versuche=3):
    """
    Zweistufig, weil eine ganze Folge als ein JSON-Block das Ausgabelimit
    sprengt und dann abgeschnitten zurueckkommt. Erst der Bauplan, dann jeder
    Abschnitt einzeln - ein misslungener Abschnitt kostet so auch nur einen
    kleinen Aufruf statt der ganzen Folge.
    """
    geruest = frage_json(f'Plan the episode for: "{thema}".',
                         GERUEST_SYSTEM, 8000)
    begriffe = geruest.get("begriffe") or thema.replace(" vs ", "|").split("|")
    begriffe = [str(b).strip() for b in begriffe][:2]
    absch_plan = geruest.get("abschnitte") or []
    print(f"  Bauplan: {len(absch_plan)} Abschnitte, Begriffe {begriffe}")

    # Wortbudget verteilen: Einstieg und Schluss kuerzer als die Dimensionen.
    ziel = (MIN_WOERTER + MAX_WOERTER) // 2
    gewicht = [0.6] + [1.0] * (len(absch_plan) - 2) + [0.7]
    summe = sum(gewicht) or 1

    fertig = []
    for i, a in enumerate(absch_plan):
        u = str(a.get("ueberschrift", "")).strip()
        # Falls doch eine Erlaeuterung angehaengt wurde, auf den bekannten
        # Namen zurueckschneiden statt die Folge zu verwerfen.
        for name, _ in DIMENSIONEN:
            if u.startswith(name):
                u = name
                break
        worte = int(ziel * gewicht[i] / summe)
        sys_p = _abschnitt_system(begriffe, u, a.get("kern", ""), worte)
        for versuch in range(1, versuche + 1):
            # 12000 statt 4000: Das Modell denkt vor der Antwort, und diese
            # Denk-Token zaehlen aufs Limit. Bei 4000 kam dreimal eine leere
            # Antwort mit stop_reason=max_tokens zurueck - bezahlt, aber ohne
            # ein einziges Wort Ergebnis.
            teil = frage_json(f'Write the section "{u}".', sys_p, 12000)
            saetze = teil.get("saetze") or []
            schlecht = [s for s in saetze if s.get("pose") not in POSEN
                        or len((s.get("text") or "")) > MAX_SATZ_ZEICHEN]
            if saetze and not schlecht:
                break
            print(f"  {u}: Versuch {versuch} verworfen "
                  f"({len(schlecht)} unbrauchbare Saetze)")
        fertig.append({"ueberschrift": u, "saetze": saetze})
        print(f"  {u:26} {len(saetze):>2} Saetze")

    folge = {k: geruest.get(k) for k in
             ("titel", "beschreibung", "tags", "hashtags")}
    folge["begriffe"] = begriffe
    folge["abschnitte"] = fertig

    # Compliance-Verstoesse betreffen fast immer einen einzelnen Satz. Die
    # ganze Folge dafuer zu verwerfen wirft sieben brauchbare Abschnitte weg,
    # die schon bezahlt sind - also gezielt den betroffenen neu schreiben.
    for runde in range(2):
        treffer = []
        for idx, a in enumerate(folge["abschnitte"]):
            txt = " ".join(s.get("text", "") for s in a["saetze"]).lower()
            for wort in VERBOTEN:
                if wort in txt:
                    treffer.append((idx, a["ueberschrift"], wort))
                    break
        if not treffer:
            break
        for idx, u, wort in treffer:
            print(f"  {u}: '{wort}' gefunden, Abschnitt wird neu geschrieben")
            plan = next((x for x in absch_plan
                         if str(x.get("ueberschrift", "")).startswith(u)), {})
            sys_p = _abschnitt_system(begriffe, u, plan.get("kern", ""),
                                      len(" ".join(
                                          s.get("text", "")
                                          for s in folge["abschnitte"][idx]["saetze"]).split()))
            teil = frage_json(
                f'Write the section "{u}". The previous attempt used the '
                f'phrase "{wort}", which is forbidden - it reads as a promise. '
                f'Say the same thing without it.', sys_p, 12000)
            if teil.get("saetze"):
                folge["abschnitte"][idx]["saetze"] = teil["saetze"]

    # Zu kurz ist kein Schoenheitsfehler: unter acht Minuten schaltet YouTube
    # keine Mid-Roll-Anzeigen, und genau die sind der Grund fuer das Langformat.
    # Also die duennsten Abschnitte nachschreiben, nicht die Folge verwerfen.
    def _worte(a):
        return len(" ".join(s.get("text", "") for s in a["saetze"]).split())

    for runde in range(2):
        gesamt = sum(_worte(a) for a in folge["abschnitte"])
        if gesamt >= MIN_WOERTER:
            break
        fehlt = MIN_WOERTER - gesamt
        print(f"  {gesamt} Woerter, {fehlt} fehlen - duennste Abschnitte "
              f"werden ausgebaut (Runde {runde + 1})")
        rang = sorted(range(len(folge["abschnitte"])),
                      key=lambda i: _worte(folge["abschnitte"][i]))
        # Auf die drei duennsten verteilen, mit Reserve, damit nicht jede
        # Runde nur knapp unter der Grenze landet.
        ziel_zusatz = fehlt // 3 + 40
        for idx in rang[:3]:
            a = folge["abschnitte"][idx]
            u = a["ueberschrift"]
            plan = next((x for x in absch_plan
                         if str(x.get("ueberschrift", "")).startswith(u)), {})
            neu_worte = _worte(a) + ziel_zusatz
            sys_p = _abschnitt_system(begriffe, u, plan.get("kern", ""),
                                      neu_worte)
            teil = frage_json(
                f'Write the section "{u}". The previous attempt was too short '
                f'for a long-form episode. Go deeper: name concrete numbers, '
                f'a worked example, and what it means in practice.',
                sys_p, 12000)
            neu = teil.get("saetze") or []
            schlecht = [x for x in neu if x.get("pose") not in POSEN
                        or len((x.get("text") or "")) > MAX_SATZ_ZEICHEN]
            if neu and not schlecht and len(" ".join(
                    x.get("text", "") for x in neu).split()) > _worte(a):
                folge["abschnitte"][idx]["saetze"] = neu
                print(f"  {u:26} {_worte(folge['abschnitte'][idx]):>4} Woerter")

    maengel = pruefe(folge)
    if maengel:
        print("  Hinweise: " + "; ".join(maengel[:5]))
        # Wortzahl und Diagrammzahl sind Richtwerte, keine Ausschlusskriterien.
        hart = [m for m in maengel if "verbotene Wendung" in m
                or "Abschnitte stimmen nicht" in m]
        if hart:
            raise SystemExit("Folge unbrauchbar: " + "; ".join(hart))
    return folge


def slugify(thema):
    t = unicodedata.normalize("NFKD", thema.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:48]


def lade_queue():
    if QUEUE.exists():
        q = json.loads(QUEUE.read_text(encoding="utf-8"))
        q.setdefault("offen", []); q.setdefault("used", [])
        return q
    return {"offen": list(SEED), "used": []}


def schreibe(folge, thema):
    slug = slugify(thema)
    ordner = EPISODES / slug
    ordner.mkdir(parents=True, exist_ok=True)

    # Ein Skript je Abschnitt: make_versus_long.py macht daraus je eine
    # Tonspur, damit die Kapitelmarken auf die Sekunde sitzen.
    for i, a in enumerate(folge["abschnitte"]):
        text = "\n".join(s["text"].strip() for s in a["saetze"]) + "\n"
        (ordner / f"abschnitt_{i:02d}.txt").write_text(text, encoding="utf-8")

    tags_zeile = " ".join([str(h).lower() for h in folge.get("hashtags", [])][:5])
    beschreibung = "\n\n".join([folge["beschreibung"].strip(), tags_zeile, HINWEIS])

    plan = {
        "version": PLAN_VERSION,
        "slug": slug, "thema": thema,
        "begriffe": folge.get("begriffe", []),
        "titel": folge["titel"].strip(),
        "beschreibung": beschreibung,
        "tags": folge.get("tags", [])[:15],
        "abschnitte": [
            {"ueberschrift": a["ueberschrift"],
             "bilder": [{"pose": s["pose"], "icon": s.get("icon") or None,
                         "diagramm": s.get("diagramm") or None,
                         "wort": (s.get("wort") or "").strip() or None,
                         "stimmung": float(s.get("stimmung") or 0),
                         "haare": bool(s.get("haare"))}
                        for s in a["saetze"]]}
            for a in folge["abschnitte"]
        ],
    }
    (ordner / "plan.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    return slug


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--thema")
    ap.add_argument("--next", action="store_true")
    ap.add_argument("--trocken", action="store_true")
    a = ap.parse_args()

    q = lade_queue()
    if a.next:
        offen = [t for t in q["offen"] if slugify(t) not in q["used"]]
        if not offen:
            raise SystemExit("Themenvorrat leer.")
        thema = offen[0]
    elif a.thema:
        thema = a.thema
    else:
        raise SystemExit("--thema oder --next angeben.")

    print(f"Thema: {thema}")
    folge = erzeuge(thema)
    woerter = sum(len(s["text"].split()) for s in alle_saetze(folge))
    print(f"  {len(folge['abschnitte'])} Abschnitte, {woerter} Woerter "
          f"(~{woerter/150:.0f} Min)")

    if a.trocken:
        print(json.dumps(folge, ensure_ascii=False, indent=2)[:3000])
        return

    slug = schreibe(folge, thema)
    if slug not in q["used"]:
        q["used"].append(slug)
    q["offen"] = [t for t in q["offen"] if slugify(t) != slug]
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    QUEUE.write_text(json.dumps(q, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Abgelegt: episodes_lang/{slug}/  ({len(q['offen'])} Themen offen)")


if __name__ == "__main__":
    main()
