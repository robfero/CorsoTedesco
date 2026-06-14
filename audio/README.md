# audio/

File MP3 delle frasi tedesche, generati da `generate_audio.py` (edge-tts, voci neural).

Le pagine usano questi file se presenti e li riproducono anche su iPad; se un file
manca, ripiegano automaticamente sulla sintesi vocale del browser.

Per generarli (su una macchina con Python e Internet):

```bash
pip install edge-tts
python3 generate_audio.py        # voce femminile (Katja)
git add audio/ && git commit -m "Audio MP3" && git push origin main
```

I nomi file (`de-<hash>.mp3`) sono calcolati da `audio_file()` in `generate.py`,
così generatore HTML e generatore audio restano sempre allineati.
