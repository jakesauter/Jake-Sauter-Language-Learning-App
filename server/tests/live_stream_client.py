"""Stream an audio file to /live in real time, like the phone does, and report latencies.

    python tests/live_stream_client.py <audio file> [ws://127.0.0.1:8000/live?lang=yue&target=en]
"""
import asyncio
import json
import subprocess
import sys
import time

import websockets

CHUNK_SAMPLES = 1600  # 100 ms at 16 kHz, the same size the phone sends


def pcm_from(audio_path):
    return subprocess.run(["ffmpeg", "-loglevel", "error", "-i", audio_path, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                          capture_output=True, check=True).stdout


async def stream(audio_path, socket_url, origin):
    pcm = pcm_from(audio_path)
    events = []
    async with websockets.connect(socket_url, origin=origin, max_size=2**20) as socket:
        started_at = time.time()

        async def receive():
            async for raw in socket:
                message = json.loads(raw)
                message["at"] = round(time.time() - started_at, 2)
                events.append(message)
                if message["type"] == "end":
                    return

        receiver = asyncio.create_task(receive())
        for offset in range(0, len(pcm), CHUNK_SAMPLES * 2):
            await socket.send(pcm[offset: offset + CHUNK_SAMPLES * 2])
            await asyncio.sleep(CHUNK_SAMPLES / 16000)
        await asyncio.sleep(2.5)
        await socket.send(json.dumps({"type": "stop"}))
        await asyncio.wait_for(receiver, 120)
    return events


def report(events):
    partials = [event for event in events if event["type"] == "partial" and event.get("text")]
    finals = [event for event in events if event["type"] == "final"]
    translations = {event["id"]: event for event in events if event["type"] == "translation" and event.get("done")}
    print(f"ready: {next((e for e in events if e['type'] == 'ready'), {})}")
    print(f"partials: {len(partials)}  (median compute {sorted(p['ms'] for p in partials)[len(partials)//2] if partials else '-'} ms)")
    for final in finals:
        done = translations.get(final["id"], {})
        stats = final["stats"]
        print(f"\n[{final['start']:6.2f}-{final['end']:6.2f}s] [{final.get('language')} {final.get('language_confidence')}] {final['text']}   (agree {final['agree']})")
        print(f"   EN: {done.get('text') or done.get('error')}")
        print(f"   final shown {stats['since_speech_end_ms']} ms after speech ended (ASR {stats['asr_ms']} ms {stats['engine_ms']});"
              f" translation first word {done.get('first_ms')} ms, done {done.get('ms')} ms via {done.get('provider')}")
    errors = [event for event in events if event["type"] == "error"]
    if errors:
        print("\nERRORS:", errors)


if __name__ == "__main__":
    url = sys.argv[2] if len(sys.argv) > 2 else "ws://127.0.0.1:8000/live?lang=yue&target=en"
    report(asyncio.run(stream(sys.argv[1], url, "https://coderx-legion-t730-28ico.tailf42501.ts.net")))
