"""voice.py — Texto a voz para que Muuk describa la UI generada.

Modelo eleven_flash_v2_5: el más barato, soporta español. Cachea por texto
para no regenerar audio idéntico mientras prueban (importa por el
presupuesto limitado de créditos).
"""

import os

from elevenlabs.client import ElevenLabs

_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "TU_VOICE_ID_AQUI")

_cache: dict[str, bytes] = {}


def synthesize_speech(texto: str) -> bytes:
    if texto in _cache:
        return _cache[texto]

    audio_stream = _client.text_to_speech.convert(
        text=texto,
        voice_id=_VOICE_ID,
        model_id="eleven_flash_v2_5",
        output_format="mp3_44100_128",
    )
    audio_bytes = b"".join(audio_stream)
    _cache[texto] = audio_bytes
    return audio_bytes