#!/usr/bin/env python3
"""
Skripte fuer das Vergleichsformat erzeugen: "A vs B - what's the difference?"

  ./venv/bin/python scripts/versus_gen.py --next
  ./venv/bin/python scripts/versus_gen.py --thema "Stocks vs Bonds"

WARUM AUSGERECHNET DIESES FORMAT
Auf dem Schwesterkanal Strichrechnung wurde genau eine Folge zu 89,9 %
zu Ende gesehen: "Anleihe vs. Aktie - was ist der Unterschied?". Alle
anderen lagen zwischen 3,9 und 27,9 %, und der Median bei 11,8 %. Diese
eine Folge holte 39 % aller Kanalaufrufe.

Der Grund ist keine Magie: Ein Vergleich baut eine offene Frage auf, die
sich erst am Ende schliesst. "Warum passiert X" beantwortet sich in der
Ueberschrift halb von selbst - es gibt keinen Grund zu bleiben.

Deshalb ist die Vergleichsstruktur hier nicht empfohlen, sondern
erzwungen: pruefe() verwirft jede Folge, die nicht beide Begriffe nennt
und keinen Unterscheidungssatz hat.

DIE INHALTLICHE GRENZE
Der Kanal erklaert, er empfiehlt nicht - dieselbe Regel wie beim
deutschen Kanal, und aus demselben Grund: Anlageberatung ist
erlaubnispflichtig. Die Liste VERBOTEN wird mechanisch geprueft, nicht
nur im Prompt erbeten. Ein Modell haelt sich meistens an eine Regel im
Prompt. "Meistens" reicht bei sechs unbeaufsichtigten Uploads am Tag
nicht.
"""

import argparse
import json
import os
import pathlib
import re
import sys
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
EPISODES = ROOT / "episodes"
QUEUE = EPISODES / "queue.json"

MODELL = "claude-sonnet-5"
PLAN_VERSION = 2

POSEN = ["stehen", "denken", "zeigen", "jubeln", "sitzen", "achselzucken"]
ICONS = ["muenze", "stapel", "hoch", "runter", "kurve", "balken",
         "uhr", "haus", "korb", "bank", "prozent", "schere", "waage"]

MIN_SAETZE, MAX_SAETZE = 8, 11
MAX_SATZ_ZEICHEN = 110
MAX_UEBERSCHRIFT = 42
MAX_HOOK = 90
MAX_THUMB = 24

# Mechanisch geprueft, nicht nur erbeten. Kleinschreibung, Teilstring-Suche.
VERBOTEN = [
    "you should buy", "you should invest", "invest in", "buy now",
    "best investment", "guaranteed return", "guaranteed profit",
    "get rich", "make you rich", "financial freedom in",
    "double your money", "secret", "hack", "this one trick",
    "don't miss", "act now", "limited time", "i recommend",
    "my advice", "you must buy", "sell your", "hot tip",
]

# Ein erster Satz, der so anfaengt, ist kein Einstieg, sondern eine Ansage.
VERBOTENER_EINSTIEG = [
    "in this video", "today we", "let's talk about", "welcome",
    "have you ever wondered", "many people ask", "in this short",
    "hi ", "hey ", "so, ", "let me explain",
]

HINWEIS = ("This video explains two terms and how they differ. "
           "It is not financial advice and not a recommendation to buy or "
           "sell anything.")

SYSTEM = f"""You write scripts for an English explainer channel about money and
economics. Format: vertical video, 30 to 50 seconds, one voice over simple
stick-figure drawings.

THE FORMAT IS FIXED: EVERY EPISODE COMPARES EXACTLY TWO THINGS
The whole channel is "A vs B - what's the difference?". Not "why does X
happen", not "what is X". Two things, side by side, and the line that
separates them.

THE MOST IMPORTANT RULE
You explain, you never advise. Allowed: how something works and why.
Forbidden: any form of recommendation, urging or promise.
  FORBIDDEN: telling anyone to buy or sell, naming specific securities,
             tickers or ISINs, promising returns, "get rich", secrets,
             urgency ("act now").
  ALLOWED:   explaining terms, showing mechanisms, working through number
             examples, naming common misconceptions, historical context.
A sentence may say: "Someone who buys a share owns a piece of the company."
It may not say: "You should buy shares."

TONE
Calm and concrete. No ad-speak, no exclamation chains, no "crazy" or
"insane". You are talking to someone smart who simply hasn't met the topic
yet. Address them as "you".

THE FIRST SENTENCE DECIDES EVERYTHING
A vertical video is swiped away if the first sentence doesn't hold. At most
{MAX_HOOK} characters, and it must do one of three things:
  a) name the confusion itself
     "Most people use these two words for the same thing. Banks don't."
  b) put the two things in direct opposition
     "One pays you to lend. The other pays you to own."
  c) ask the question the viewer has quietly had
     "Why does one of them make money while you sleep, and the other doesn't?"

FORBIDDEN as a first sentence, without exception:
  "In this video..." / "Today we..." / "Let's talk about..." / "Welcome..."
  "Have you ever wondered..." / a definition. A definition is the answer,
  and the answer does not belong at the start.

Sentence 2 does not resolve the hook. It promises the resolution.

THE STRUCTURE AFTER THAT
  - two to three sentences on the first thing
  - two to three sentences on the second thing
  - ONE sentence that names the difference plainly. It must begin with
    "The difference" or "The real difference" - this is the sentence the
    whole video exists for.
  - one sentence on where the difference actually matters
  - a closing sentence that sums up and sells nothing

SENTENCES
{MIN_SAETZE} to {MAX_SAETZE} sentences. Each at most {MAX_SATZ_ZEICHEN}
characters, spoken English, one thought per sentence. No bullet points, no
brackets, no emojis. Write numbers as they are spoken ("a hundred dollars",
not "$100").

DRAWINGS
Each sentence gets one pose from this list, there are no others:
{", ".join(POSEN)}

Optionally one drawn symbol appearing beside the figure. Only these exist:
  muenze (money in general), stapel (savings, wealth), hoch (rise),
  runter (fall, loss), kurve (growth over time), balken (comparison,
  distribution), uhr (time, duration), haus (property, rent), korb
  (consumption, prices), bank (bank, central bank, state), prozent
  (interest rate, share), schere (fees, deductions), waage (weighing one
  against the other)
Use "waage" on the sentence that names the difference - that is what it is
for. Set a symbol only where it genuinely supports the sentence. A wrong
symbol is worse than none. About half the sentences need one.
Optionally one bold word drawn into the picture: at most twelve characters,
capitals or a number. Only where it sharpens the sentence - rather leave
half of them without.
"stimmung" is a number from minus one to one and drives the mouth.

CHARTS
Where a sentence lives on numbers, give a chart instead of pose and symbol.
It then fills the frame.
  "diagramm": {{"art": "balken", "werte": [1000, 700],
               "achse": ["Stocks", "Bonds"], "einheit": "$"}}
  "diagramm": {{"art": "linie", "werte": [1000, 1340, 1790, 2400],
               "achse": ["year one", "year twenty"], "einheit": "$"}}
Rules:
  - "balken" for a comparison, two to four values. This is the natural one
    for this format.
  - "linie" for a development over time, four to eight values.
  - The numbers must match what the sentence says. Invent no number that
    does not appear in the text or contradicts it.
  - At most TWO charts per episode.
  - A sentence with a chart still needs a pose (it is not shown, but the
    format requires it).

TITLE
The YouTube title. Unlike the headline it may be longer and should carry the
words people actually search for. Always end it with the question:
  "Stocks vs Bonds - What's the Difference?"

HEADLINE
Stands above the whole video. At most {MAX_UEBERSCHRIFT} characters - that is
tight, keep it short. It names the two things, nothing else.
  good: "Stocks vs Bonds"   good: "Saving vs Investing"
  bad:  "The complete difference between stocks and bonds explained"

THUMBNAIL
Often only 210 pixels wide in the YouTube overview. Very few, very large words.
  "thumbnail": {{"zeile": "who pays whom", "zahl": null, "icon": "waage"}}
  - "zeile": two to four words, at most {MAX_THUMB} characters. It does NOT
    repeat the title, it adds the angle.
  - "zahl": the one number the episode turns on, short. Leave it out when
    there is none - an invented one is worse than none.
  - "icon": one from the symbol list above.
No exclamation marks, no all-caps, no "SHOCKING".

HASHTAGS
Three to five, no spaces, English, lower case. They name the topic, they
advertise nothing.
  good:     ["#stocks", "#bonds", "#personalfinance"]
  bad:      ["#getrich", "#secret", "#trading"]
No "#shorts" - the pipeline sets that itself.

Answer with JSON ONLY, no text before or after:
{{"ueberschrift": "...", "titel": "...", "beschreibung": "...",
  "tags": ["...", "..."], "hashtags": ["#...", "#..."],
  "begriffe": ["A", "B"],
  "thumbnail": {{"zeile": "...", "zahl": null, "icon": "waage"}},
  "saetze": [{{"text": "...", "pose": "denken", "icon": "waage",
              "wort": "OWN", "stimmung": 0}}]}}
"""

SEED = [
    "Stocks vs Bonds", "Saving vs Investing", "Debit card vs Credit card",
    "Gross vs Net", "Interest vs Compound interest", "Inflation vs Deflation",
    "ETF vs Mutual fund", "Rent vs Buy", "Fixed rate vs Variable rate",
    "Income vs Wealth", "Assets vs Liabilities", "Bull market vs Bear market",
    "Central bank vs Commercial bank", "Recession vs Depression",
    "Nominal vs Real return", "Tax deduction vs Tax credit",
    "Insurance vs Warranty", "Loan vs Lease", "Salary vs Hourly wage",
    "Budget vs Forecast", "Cash flow vs Profit", "Revenue vs Profit",
    "Value stock vs Growth stock", "Dividend vs Capital gain",
    "Credit score vs Credit report", "Emergency fund vs Investment",
    "Pension vs Annuity", "Term vs Whole life insurance",
    "Checking account vs Savings account", "Gold vs Cash",
    "Supply vs Demand", "Price vs Value", "Cost vs Expense",
    "Bond yield vs Bond price", "Liquidity vs Solvency",
    "Micro vs Macro economics", "Tariff vs Quota", "Import vs Export",
    "GDP vs GNP", "Fixed cost vs Variable cost",
]


# ------------------------------------------------------------------ Modell

def client():
    import anthropic
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY fehlt.")
    return anthropic.Anthropic()


def ask(prompt: str, system: str, max_tokens: int = 8000) -> str:
    m = client().messages.create(
        model=MODELL, max_tokens=max_tokens, system=system,
        messages=[{"role": "user", "content": prompt}])
    return "".join(b.text for b in m.content if b.type == "text")


def parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\n|\n```$", "", text)
    i, j = text.find("{"), text.rfind("}")
    if i < 0 or j < 0:
        raise ValueError("Keine JSON-Struktur in der Antwort.")
    return json.loads(text[i:j + 1])


# ------------------------------------------------------------------ Pruefung

def pruefe(folge: dict) -> list[str]:
    """Alles, was eine Folge unbrauchbar macht. Leere Liste = in Ordnung."""
    m = []
    saetze = folge.get("saetze") or []

    if not (MIN_SAETZE <= len(saetze) <= MAX_SAETZE):
        m.append(f"{len(saetze)} Saetze, erlaubt sind {MIN_SAETZE}-{MAX_SAETZE}")

    volltext = " ".join(s.get("text", "") for s in saetze).lower()
    for wort in VERBOTEN:
        if wort in volltext:
            m.append(f"verbotene Wendung im Text: '{wort}'")

    if saetze:
        hook = saetze[0].get("text", "").strip()
        if len(hook) > MAX_HOOK:
            m.append(f"Einstieg {len(hook)} Zeichen, erlaubt sind {MAX_HOOK}")
        for anfang in VERBOTENER_EINSTIEG:
            if hook.lower().startswith(anfang):
                m.append(f"Einstieg beginnt mit '{anfang}'")

    for i, s in enumerate(saetze):
        t = (s.get("text") or "").strip()
        if len(t) > MAX_SATZ_ZEICHEN:
            m.append(f"Satz {i+1}: {len(t)} Zeichen, erlaubt sind {MAX_SATZ_ZEICHEN}")
        if s.get("pose") not in POSEN:
            m.append(f"Satz {i+1}: Pose '{s.get('pose')}' gibt es nicht")
        if s.get("icon") and s["icon"] not in ICONS:
            m.append(f"Satz {i+1}: Symbol '{s['icon']}' gibt es nicht")

    # Das Format selbst - hier wird es erzwungen, nicht erbeten.
    begriffe = [str(b).strip() for b in (folge.get("begriffe") or []) if str(b).strip()]
    if len(begriffe) != 2:
        m.append("Es muessen genau zwei Begriffe verglichen werden")
    else:
        for b in begriffe:
            # Auf den Wortstamm pruefen, nicht auf die exakte Form: "Stocks"
            # im Titel und "a stock" im Text sind dasselbe Ding. Sonst
            # verwirft die Pruefung brauchbare Folgen und kostet einen
            # zweiten API-Aufruf fuer nichts.
            stamm = b.lower().split()[0].rstrip("s")
            if stamm not in volltext:
                m.append(f"Begriff '{b}' kommt im gesprochenen Text nicht vor")

    if not any(s.get("text", "").strip().lower().startswith("the difference")
               or s.get("text", "").strip().lower().startswith("the real difference")
               for s in saetze):
        m.append("Kein Satz, der mit 'The difference' beginnt")

    u = (folge.get("ueberschrift") or "").strip()
    if not u or len(u) > MAX_UEBERSCHRIFT:
        m.append(f"Ueberschrift {len(u)} Zeichen, erlaubt sind {MAX_UEBERSCHRIFT}")

    tn = folge.get("thumbnail") or {}
    z = str(tn.get("zeile") or "").strip()
    if not z or len(z) > MAX_THUMB:
        m.append(f"Thumbnail-Zeile {len(z)} Zeichen, erlaubt sind {MAX_THUMB}")
    if tn.get("icon") and tn["icon"] not in ICONS:
        m.append(f"Thumbnail-Symbol '{tn['icon']}' gibt es nicht")

    anzahl = sum(1 for s in saetze if s.get("diagramm"))
    if anzahl > 2:
        m.append(f"{anzahl} Diagramme, hoechstens zwei")
    return m


def erzeuge(thema: str, versuche: int = 3) -> dict:
    """Schreiben lassen, pruefen, bei Maengeln mit der Mangelliste neu bitten."""
    letzte = []
    for versuch in range(1, versuche + 1):
        prompt = f'Write the episode for: "{thema}".'
        if letzte:
            prompt += ("\n\nThe previous attempt was rejected for these reasons. "
                       "Fix all of them:\n- " + "\n- ".join(letzte))
        folge = parse_json(ask(prompt, SYSTEM))
        letzte = pruefe(folge)
        if not letzte:
            return folge
        print(f"  Versuch {versuch} verworfen: {'; '.join(letzte[:4])}")
    raise SystemExit(f"Nach {versuche} Versuchen keine saubere Folge fuer '{thema}'.")


# ------------------------------------------------------------------ Ablage

def slugify(thema: str) -> str:
    t = unicodedata.normalize("NFKD", thema.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t[:48]


def lade_queue() -> dict:
    """
    Schluessel heissen 'offen' und 'used', und in 'used' stehen SLUGS.
    Genau so liest es der Workflow: er nimmt used[-1] als Ordnernamen fuer
    make_episode. Ein anderer Schluessel oder das Thema statt des Slugs
    laesst den Lauf nach der Skripterzeugung auflaufen - Geld fuer den
    API-Aufruf ausgegeben, kein Video dabei.
    """
    if QUEUE.exists():
        q = json.loads(QUEUE.read_text(encoding="utf-8"))
        q.setdefault("offen", [])
        q.setdefault("used", [])
        return q
    return {"offen": list(SEED), "used": []}


def neue_themen(vorhanden: list[str], anzahl: int = 40) -> list[str]:
    """
    Nachschub, bevor die Liste leer ist. Nachfuellen ist ein API-Aufruf,
    der scheitern kann - und dann steht die Produktion. Deshalb frueh.
    """
    schon = "\n".join(f"- {t}" for t in vorhanden[-120:])
    text = ask(
        f"Give me {anzahl} new comparison topics for an English channel about "
        f"money and economics. Format strictly \"A vs B\", two things people "
        f"genuinely confuse. No duplicates of these:\n{schon}\n\n"
        f"Answer with a JSON array of strings, nothing else.",
        "You return only valid JSON. No prose.", max_tokens=2000)
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-z]*\n|\n```$", "", t)
    i, j = t.find("["), t.rfind("]")
    roh = json.loads(t[i:j + 1]) if i >= 0 else []
    bekannt = {x.lower() for x in vorhanden}
    return [x for x in roh if isinstance(x, str) and x.lower() not in bekannt]


def schreibe_queue(q: dict) -> None:
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    QUEUE.write_text(json.dumps(q, ensure_ascii=False, indent=2), encoding="utf-8")


def schreibe(folge: dict, thema: str) -> str:
    slug = slugify(thema)
    ordner = EPISODES / slug
    ordner.mkdir(parents=True, exist_ok=True)
    saetze = folge["saetze"]

    (ordner / "script_en.txt").write_text(
        "\n".join(s["text"].strip() for s in saetze) + "\n", encoding="utf-8")

    tags_zeile = " ".join(["#shorts"] + [str(h).lower()
                                         for h in folge.get("hashtags", [])][:4])
    beschreibung = "\n\n".join([folge["beschreibung"].strip(), tags_zeile, HINWEIS])

    plan = {
        "version": PLAN_VERSION,
        "slug": slug,
        "thema": thema,
        "begriffe": folge.get("begriffe", []),
        "ueberschrift": folge["ueberschrift"].strip(),
        "titel": folge["titel"].strip(),
        "beschreibung": beschreibung,
        "tags": folge.get("tags", [])[:15],
        "hashtags": [str(h).lower() for h in folge.get("hashtags", [])][:5],
        "thumbnail": {
            "zeile": (folge.get("thumbnail") or {}).get("zeile", "").strip(),
            # str() ist Pflicht: Das Modell liefert die Zahl mal als "1.200 $",
            # mal als 1200 - und .strip() auf einem int wirft AttributeError
            # mitten im Lauf. Eine Folge kostet dann API-Aufruf und Renderzeit
            # fuer nichts.
            "zahl": str((folge.get("thumbnail") or {}).get("zahl") or "").strip() or None,
            "icon": (folge.get("thumbnail") or {}).get("icon") or None,
        },
        "bilder": [
            {
                "pose": s["pose"],
                "icon": s.get("icon") or None,
                "diagramm": s.get("diagramm") or None,
                "wort": (s.get("wort") or "").strip() or None,
                "stimmung": float(s.get("stimmung") or 0),
                "haare": bool(s.get("haare")),
            }
            for s in saetze
        ],
    }
    (ordner / "plan.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    return slug


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--thema")
    ap.add_argument("--next", action="store_true", help="naechstes offenes Thema")
    ap.add_argument("--trocken", action="store_true",
                    help="nur pruefen und ausgeben, nichts ablegen")
    args = ap.parse_args()

    q = lade_queue()
    if args.next:
        if len(q["offen"]) < 15:
            print("Themenliste wird nachgefuellt ...")
            try:
                nachschub = neue_themen(q["offen"] + q["used"])
                q["offen"].extend(nachschub)
                print(f"  {len(nachschub)} neue Themen")
            except Exception as fehler:
                # Kein Abbruch: Solange noch offene Themen da sind, ist ein
                # gescheitertes Nachfuellen kein Grund, den Lauf zu killen.
                print(f"  Nachfuellen fehlgeschlagen ({type(fehler).__name__}), weiter mit dem Vorrat")
        if not q["offen"]:
            raise SystemExit("Themenvorrat leer.")
        thema = q["offen"][0]
    elif args.thema:
        thema = args.thema
    else:
        raise SystemExit("--thema oder --next angeben.")

    print(f"Thema: {thema}")
    folge = erzeuge(thema)

    if args.trocken:
        print(json.dumps(folge, ensure_ascii=False, indent=2))
        return

    slug = schreibe(folge, thema)

    # Kein blindes append: Wird ein Thema neu erzeugt, stuende der Slug
    # sonst zweimal drin und used[-1] koennte auf die falsche Folge zeigen.
    if slug not in q["used"]:
        q["used"].append(slug)
    q["offen"] = [t for t in q["offen"] if slugify(t) != slug]
    schreibe_queue(q)
    print(f"Abgelegt: episodes/{slug}/  ({len(q['offen'])} Themen offen)")


if __name__ == "__main__":
    main()
