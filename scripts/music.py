#!/usr/bin/env python3
"""
Hintergrundbett, selbst erzeugt.

Warum synthetisiert und nicht heruntergeladen: Musik ist der haeufigste
Grund fuer Urheberrechtsansprueche auf YouTube, und "lizenzfrei" auf einer
beliebigen Seite bedeutet oft nur "der Uploader hat es nicht geprueft". Was
hier entsteht, stammt aus Zahlen in dieser Datei - die Rechte liegen damit
eindeutig beim Kanal. Siehe LICENSES.md.

Bewusst unauffaellig: ein langsamer Flaechenklang ohne Melodie und ohne
Schlagzeug. Bei einem Erklaervideo konkurriert alles Auffaellige mit der
Stimme, und die traegt den Inhalt.

  ./venv/bin/python scripts/music.py
"""

import pathlib
import wave

import numpy as np

SR = 44100
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "bett.wav"

# Vier Akkorde, je vier Sekunden, zweimal durch = 32 Sekunden. Remotion
# wiederholt das Bett, also muss der letzte Akkord in den ersten passen.
AKKORDE = [
    ("a2", "e3", "a3", "c4"),   # a-Moll
    ("f2", "c3", "f3", "a3"),   # F-Dur
    ("c3", "g3", "c4", "e4"),   # C-Dur
    ("g2", "d3", "g3", "b3"),   # G-Dur
]
TAKT = 4.0

HALBTON = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}


def freq(note: str) -> float:
    name, oktave = note[0], int(note[1])
    # A4 = 440 Hz, MIDI 69
    midi = 12 * (oktave + 1) + HALBTON[name]
    return 440.0 * 2 ** ((midi - 69) / 12)


def flaeche(f: float, dauer: float) -> np.ndarray:
    """Ein Ton mit weichem Ein- und Ausblenden.

    Die leichte Verstimmung der zweiten Schwingung (1.003) laesst den Ton
    atmen; exakt gleiche Frequenzen klingen tot.
    """
    n = int(SR * dauer)
    t = np.linspace(0, dauer, n, endpoint=False)
    ton = (
        np.sin(2 * np.pi * f * t)
        + 0.5 * np.sin(2 * np.pi * f * 1.003 * t)
        + 0.25 * np.sin(2 * np.pi * f * 2 * t)
        + 0.12 * np.sin(2 * np.pi * f * 3 * t)
    )
    # Halbe Sekunde auf, halbe Sekunde ab - die Akkorde ueberlappen sich
    # dadurch und es entsteht kein hoerbarer Schnitt.
    huelle = np.ones(n)
    rampe = int(SR * 0.6)
    huelle[:rampe] = np.linspace(0, 1, rampe)
    huelle[-rampe:] = np.linspace(1, 0, rampe)
    return ton * huelle


def bau() -> np.ndarray:
    laenge = int(SR * TAKT * len(AKKORDE) * 2)
    spur = np.zeros(laenge + int(SR * TAKT))
    pos = 0
    for _ in range(2):
        for akkord in AKKORDE:
            block = sum(flaeche(freq(n), TAKT + 0.6) for n in akkord)
            spur[pos:pos + len(block)] += block
            pos += int(SR * TAKT)
    spur = spur[:laenge]
    # Der Ueberhang des letzten Akkords wandert an den Anfang, damit die
    # Schleife nahtlos schliesst.
    ueberhang = int(SR * 0.6)
    spur[:ueberhang] += spur[laenge - ueberhang:laenge] * 0.0
    return spur / (np.max(np.abs(spur)) + 1e-9) * 0.5


def speichern(pfad: pathlib.Path, audio: np.ndarray):
    pfad.parent.mkdir(parents=True, exist_ok=True)
    daten = (np.clip(audio, -1, 1) * 32767).astype("<i2")
    with wave.open(str(pfad), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes(daten.tobytes())


if __name__ == "__main__":
    speichern(OUT, bau())
    print(f"{OUT}  {OUT.stat().st_size / 1024:.0f} KB")
