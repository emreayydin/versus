"""Lokale Vergleichsskripte fuer den englischen versus-Kanal.

Die Vorlagen halten das Format und die Sicherheitsgrenzen ein, ohne einen
externen Textdienst zu benoetigen. Sie erklaeren Unterschiede, geben aber
keine Kauf- oder Verkaufsanweisungen.
"""

from __future__ import annotations

import re


POSEN = ["stehen", "denken", "zeigen", "jubeln", "sitzen", "achselzucken"]
ICONS = ["muenze", "stapel", "hoch", "runter", "kurve", "balken",
         "uhr", "haus", "korb", "bank", "prozent", "schere", "waage"]

DIMENSIONS = [
    "What it actually is", "Who pays whom", "Risk", "Time",
    "Taxes and costs", "Who each one suits",
]

# Reihenfolge nach gemessener Leistung (20.09.2026): Themen aus dem Alltag
# ("Salary vs Hourly wage", "Rent vs Buy") erreichen im Median 58 Aufrufe,
# Buchhaltungsbegriffe ("Working capital vs Net worth") nur 42. Die besten
# Videos des Kanals sind Supply vs Demand (1.100), Income vs Wealth (1.000),
# Bear trap vs Bull trap (968), Debit vs Credit (481).
LOCAL_TOPICS = [
    # Alltag: Gehalt, Miete, Karte, Sparen, Steuern, Versicherung
    "Salary vs Hourly wage", "Rent vs Buy", "Debit card vs Credit card",
    "Gross vs Net", "Saving vs Investing", "Need vs Want",
    "Saving vs Spending", "Tax deduction vs Tax credit",
    "Checking account vs Savings account", "Insurance vs Warranty",
    "Loan vs Lease", "Emergency fund vs Investment", "Credit score vs Credit report",
    "Interest vs Compound interest", "Income vs Wealth", "Price vs Value",
    "Term vs Whole life insurance", "Pension vs Annuity", "Gold vs Cash",
    "Fixed rate vs Variable rate", "Inflation vs Deflation",
    # Maerkte und Wirtschaft: immer noch anschaulich
    "Supply vs Demand", "Bull market vs Bear market", "Stocks vs Bonds",
    "ETF vs Mutual fund", "Recession vs Depression", "Value stock vs Growth stock",
    "Dividend vs Capital gain", "Nominal vs Real return", "Import vs Export",
    "Central bank vs Commercial bank", "Tariff vs Quota",
    # Fachbegriffe: laufen messbar schlechter, bleiben als Reserve hinten
    "Assets vs Liabilities", "Revenue vs Profit", "Cash flow vs Profit",
    "Budget vs Forecast", "Fixed cost vs Variable cost", "Cost vs Expense",
    "Liquidity vs Solvency", "Bond yield vs Bond price", "Revenue vs Cash flow",
    "Micro vs Macro economics", "GDP vs GNP", "Risk vs Uncertainty",
    "Price vs Cost", "Salary vs Wage",
]


def terms(topic: str) -> tuple[str, str]:
    """Beide Begriffe eines Themas, auch aus einer Slug-Schreibweise.

    In episodes/queue.json stehen Themen teils als "mortgage-vs-rent". Ohne
    Leerzeichen griff die Trennung nicht, und die lokale Fassung machte daraus
    den Titel "The first term vs The second term". Aufgefallen am 20.09.2026.
    """
    text = topic.strip()
    if not re.search(r"\s+vs\.?\s+", text, re.IGNORECASE) and re.search(r"-vs-", text, re.IGNORECASE):
        text = re.sub(r"-vs-", " vs ", text, flags=re.IGNORECASE).replace("-", " ")
        abkuerzungen = {"etf", "gdp", "gnp", "ira", "apr", "roi", "apy", "cd",
                        "hsa", "llc", "ipo", "reit", "etn", "pe", "npv", "irr"}
        text = " ".join(w.upper() if w.lower() in abkuerzungen
                        else (w if w.isupper() else w.capitalize())
                        for w in text.split())
        text = re.sub(r"\bVs\b", "vs", text)
    parts = re.split(r"\s+vs\.?\s+", text, maxsplit=1, flags=re.IGNORECASE)
    if len(parts) == 2 and all(part.strip() for part in parts):
        return parts[0].strip(), parts[1].strip()
    return "The first term", "The second term"


def _tags(a: str, b: str) -> tuple[list[str], list[str]]:
    words = []
    for term in (a, b):
        tag = re.sub(r"[^a-z0-9]", "", term.lower())
        if len(tag) >= 3 and tag not in words:
            words.append(tag[:24])
    hashtags = [f"#{word}" for word in words]
    hashtags.extend(["#personalfinance", "#economics", "#comparison"])
    return [a, b, "Personal finance", "Economics", "Comparison"], hashtags[:5]


def _entry(text: str, index: int, icon: str | None = None) -> dict:
    return {
        "text": text,
        "pose": POSEN[index % len(POSEN)],
        "icon": icon if icon in ICONS else None,
        "wort": "",
        "stimmung": round(-0.1 + (index % 5) * 0.05, 2),
    }


def generate_short(topic: str) -> dict:
    a, b = terms(topic)
    tags, hashtags = _tags(a, b)
    title = f"{a} vs {b} - What's the Difference?"
    if len(title) > 90:
        title = f"{a} vs {b}: What's the Difference?"[:90]
    sentences = [
        (f"{a} and {b} sound similar. They are not.", "waage"),
        (f"{a} starts with a different question.", "zeigen"),
        (f"{b} starts with another question.", "zeigen"),
        ("Their timing, risk, or purpose can differ.", "balken"),
        (f"{a} can be understood through its own mechanism.", "kurve"),
        (f"{b} follows a different mechanism.", "stapel"),
        (f"The difference is how {a} and {b} work.", "waage"),
        ("That distinction matters when real situations are compared.", None),
        ("The right label depends on context, not a promise.", "denken"),
    ]
    return {
        "ueberschrift": f"{a} vs {b}"[:42],
        "titel": title,
        "beschreibung": (
            f"A calm comparison of {a} and {b}. "
            "The episode explains the mechanism, the timing, and the main distinction. "
            "It is educational content, not financial advice."
        ),
        "tags": tags,
        "hashtags": hashtags,
        "begriffe": [a, b],
        "thumbnail": {"zeile": "same label?", "zahl": None, "icon": "waage"},
        "saetze": [_entry(text, i, icon) for i, (text, icon) in enumerate(sentences)],
    }


FOCUS = {
    "What it actually is": ("its basic role", "a different basic role"),
    "Who pays whom": ("the payer and recipient", "a different money flow"),
    "Risk": ("uncertainty around the first term", "uncertainty around the second term"),
    "Time": ("the first timeline", "a different timeline"),
    "Taxes and costs": ("the first cost structure", "a different cost structure"),
    "Who each one suits": ("the setting where the first term appears", "a different setting"),
}


def _section_sentences(a: str, b: str, heading: str) -> list[str]:
    focus_a, focus_b = FOCUS[heading]
    h = heading.lower()
    return [
        f"Under {h}, {a} and {b} answer different questions.",
        f"{a} starts with one set of rules, while {b} starts with another.",
        f"The {h} question looks at {focus_a} for {a}.",
        f"For {b}, the same question looks at {focus_b}.",
        "That distinction matters because familiar labels can hide the mechanism.",
        "An example makes the relationship easier to follow.",
        f"With {a}, the first side of the comparison sets the starting point.",
        f"With {b}, the second side sets a different starting point.",
        "Neither label becomes more useful merely because it sounds familiar.",
        f"The words {a} and {b} describe different positions in the same map.",
        "A clear map separates the terms before it compares their effects.",
        f"If the question changes, {a} and {b} can lead to different answers.",
        "That is why a single number cannot tell the whole story.",
        f"The first term, {a}, needs its own explanation.",
        f"The second term, {b}, needs its own explanation too.",
        "Keeping both explanations visible prevents a false shortcut.",
        f"In practice, {a} may appear beside {b} without being the same thing.",
        "The comparison works best when the wording stays precise.",
        f"A viewer can then see where {a} ends and {b} begins.",
        "The next section can build on that boundary without changing it.",
    ]


def generate_long(topic: str) -> dict:
    a, b = terms(topic)
    tags, hashtags = _tags(a, b)
    sections = []
    # Der erste Satz ist der Einstieg und darf hoechstens 110 Zeichen haben
    # (MAX_HOOK in versus_long_gen). Bei langen Begriffen wie "Debit card vs
    # Credit card" wurden es 111 - jede Sammelfolge scheiterte daran, weil das
    # Thema vorne in der Warteschlange stand. Darum die laengste Fassung
    # nehmen, die passt.
    einstiege = [
        f"People often treat {a} and {b} as interchangeable. That shortcut hides the important difference.",
        f"People often treat {a} and {b} as interchangeable. That hides the real difference.",
        f"{a} and {b} are not interchangeable. Here is the difference.",
        f"{a} vs {b}: the difference that matters.",
    ]
    einstieg = next((e for e in einstiege if len(e) <= 110), einstiege[-1][:110])
    opening = [
        einstieg,
        "They can appear together, but their roles are not identical.",
        "The first task is to name both terms clearly.",
        "A comparison becomes useful when the same question reaches two answers.",
        "This episode follows that question through six dimensions.",
        "We start with meaning, then follow the money.",
        "After that, we examine risk, time, and costs.",
        f"The final section returns to the line between {a} and {b}.",
        "Nothing here promises a result or gives a personal instruction.",
        "The goal is a clearer map of the two ideas.",
    ]
    sections.append({"ueberschrift": "Opening", "saetze": [_entry(text, i) for i, text in enumerate(opening)]})

    index = len(opening)
    for heading in DIMENSIONS:
        texts = _section_sentences(a, b, heading)
        sections.append({
            "ueberschrift": heading,
            "saetze": [_entry(text, index + i, "waage" if i in (0, 9, 18) else None)
                       for i, text in enumerate(texts)],
        })
        index += len(texts)

    closing = [
        f"The difference is not a label; it is the mechanism between {a} and {b}.",
        f"The real difference becomes visible when the same situation is described with {a} or {b}.",
        "One word can point to a different flow, timeline, or responsibility.",
        "That is why the comparison must keep the two terms separate.",
        f"When {a} and {b} appear together, ask which question each one answers.",
        "Then ask what is measured, who carries uncertainty, and when the result appears.",
        "Those questions create understanding without turning an explanation into a recommendation.",
        "A precise comparison leaves room for context and uncertainty.",
        f"In one sentence: {a} and {b} may meet, but they are not interchangeable.",
        "That is the boundary worth remembering.",
    ]
    sections.append({
        "ueberschrift": "The difference",
        "saetze": [_entry(text, index + i, "waage" if i in (0, 1, 8) else None)
                   for i, text in enumerate(closing)],
    })

    return {
        "titel": f"{a} vs {b} - What's the Difference?"[:90],
        "beschreibung": (
            f"A long-form comparison of {a} and {b}. "
            "The episode follows the same pair through meaning, money flow, risk, time, costs, and context. "
            "It explains the distinction without giving financial advice."
        ),
        "tags": tags,
        "hashtags": hashtags,
        "begriffe": [a, b],
        "abschnitte": sections,
    }


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")[:48]


def new_topics(vorhanden: list[str], count: int = 40) -> list[str]:
    """Nur echte, noch nicht benutzte Themen.

    `vorhanden` mischt Titel ("Saving vs Investing") und Slugs
    ("saving-vs-investing"). Frueher wurde nur klein geschrieben verglichen,
    dadurch kamen benutzte Themen zurueck in die Liste - am 16.09. wurde so
    eine Folge dreimal zusaetzlich hochgeladen. Ausserdem gab es Platzhalter
    wie "Concept 1 vs Context 1"; lieber ein leerer Vorrat als so ein Video.
    """
    known = {_slug(item) for item in vorhanden}
    result = []
    for topic in LOCAL_TOPICS:
        if len(result) >= count:
            break
        if _slug(topic) not in known:
            result.append(topic)
            known.add(_slug(topic))
    return result
