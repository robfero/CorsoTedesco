#!/usr/bin/env python3
"""Genera gli MP3 delle frasi tedesche del corso con edge-tts.

Perché serve
------------
La sintesi vocale del browser (Web Speech API) su Safari/iPad espone solo una
voce di sistema: non si possono scegliere voci migliori. Pre-generando dei file
audio MP3 con un motore neural, l'ascolto funziona in modo identico ovunque —
iPad compreso — e anche offline. Le pagine usano automaticamente questi MP3 se
presenti, e ripiegano sulla voce del browser se mancano.

Requisiti
---------
- Python 3
- edge-tts (gratuito, nessuna API key):  pip install edge-tts
- Connessione a Internet, con orologio di sistema corretto.

Uso
---
    python3 generate_audio.py                 # voce predefinita (Katja, f)
    python3 generate_audio.py --voice de-DE-ConradNeural   # voce maschile
    python3 generate_audio.py --force         # rigenera anche i file già presenti

I file vengono scritti in ./audio/ con lo stesso schema di nomi usato da
generate.py (audio_file), quindi le pagine li trovano senza altra configurazione.
Dopo la generazione: git add audio/ && commit & push.

Voci tedesche neural utili: de-DE-KatjaNeural (f), de-DE-ConradNeural (m),
de-DE-AmalaNeural (f), de-DE-KillianNeural (m). Elenco completo: edge-tts --list-voices
"""

import argparse
import asyncio
import json
import os
import sys

from generate import BASE, AUDIO_DIR, audio_file, german_phrases

try:
    import edge_tts
except ImportError:
    sys.exit("Manca edge-tts. Installa con:  pip install edge-tts")


async def synth_one(text, path, voice, rate):
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
    await communicate.save(path)


async def main_async(args):
    with open(os.path.join(BASE, "course.json"), encoding="utf-8") as f:
        course = json.load(f)

    out_dir = os.path.join(BASE, AUDIO_DIR)
    os.makedirs(out_dir, exist_ok=True)

    phrases = german_phrases(course)
    todo = []
    for text in phrases:
        rel = audio_file(text)                       # es. audio/de-<hash>.mp3
        path = os.path.join(BASE, rel)
        if args.force or not os.path.exists(path) or os.path.getsize(path) == 0:
            todo.append((text, path))

    print(f"Frasi totali: {len(phrases)} · da generare: {len(todo)} · voce: {args.voice}")
    if not todo:
        print("Tutto già presente. (usa --force per rigenerare)")
        return

    ok = 0
    for i, (text, path) in enumerate(todo, 1):
        try:
            await synth_one(text, path, args.voice, args.rate)
            ok += 1
            print(f"  [{i}/{len(todo)}] ✓ {text[:48]}")
        except Exception as e:  # noqa: BLE001 - vogliamo continuare sugli altri
            print(f"  [{i}/{len(todo)}] ✗ {text[:48]} → {e}")

    print(f"Fatto: {ok}/{len(todo)} file in {AUDIO_DIR}/")
    print("Ora:  git add audio/ && git commit -m 'Audio MP3' && git push origin main")


def main():
    ap = argparse.ArgumentParser(description="Genera gli MP3 tedeschi del corso (edge-tts).")
    ap.add_argument("--voice", default="de-DE-KatjaNeural", help="voce edge-tts (default: de-DE-KatjaNeural)")
    ap.add_argument("--rate", default="-10%", help="velocità di sintesi, es. -10%% per più lento (default: -10%%)")
    ap.add_argument("--force", action="store_true", help="rigenera anche i file già esistenti")
    args = ap.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
