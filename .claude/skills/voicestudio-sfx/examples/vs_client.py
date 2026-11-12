#!/usr/bin/env python3
"""Batch sound effects from a local VoiceStudio (https://github.com/debpalash/voicestudio).

VoiceStudio runs on your machine; its backend listens on http://127.0.0.1:3900 with no key for loopback
callers. Sound effects come from its opt-in MOSS-SoundEffect v2.0 engine (Apache-2.0 weights, NVIDIA GPU
only, ~11 GB of VRAM): Tools -> Sound effects -> Install, once.

    python vs_client.py status
    python vs_client.py batch sounds.json out/            # every sound in the list -> out/<id>.wav + manifest.json
    python vs_client.py batch sounds.json out/ --ogg      # also out/<id>.ogg, loudness-normalised by tier (needs ffmpeg)
    python vs_client.py one "short metallic coin pickup chime" 1.5 out/coin.wav --seed 7

Standard library only. We call VoiceStudio over HTTP and copy none of its (AGPL-3.0) code.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

BASE = os.environ.get('VOICESTUDIO_URL', 'http://127.0.0.1:3900')
MIN_S, MAX_S, MAX_PROMPT = 1.0, 30.0, 500  # the engine's own limits (backend/engines/moss_sfx)

# Integrated loudness per hierarchy tier for single assets (house values; the mix target is -18 LUFS,
# docs/research/83-audio-hierarchy.md). Moments sit above everything, the world sits under it.
TIER_LUFS = {1: -14.0, 2: -16.0, 3: -20.0, 4: -24.0, 5: -24.0, 6: -26.0}


class VoiceStudioError(RuntimeError):
    pass


def _request(method, path, body=None, base=BASE, timeout=900):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, method=method,
                                 headers={'Content-Type': 'application/json', 'X-OmniVoice-Client-Id': 'aaa-kit'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode('utf-8', 'replace')
        try:
            detail = json.loads(detail).get('detail', detail)
        except (ValueError, AttributeError):
            pass
        raise VoiceStudioError(f'{method} {path} -> {e.code}: {detail}') from None
    except urllib.error.URLError as e:
        raise VoiceStudioError(f'VoiceStudio is not reachable at {base} ({e.reason}). Open the app first.') from None


def status(base=BASE):
    """GET /api/sfx/status: installed, available, supported, reason (why Generate is blocked, else None)."""
    return json.loads(_request('GET', '/api/sfx/status', base=base)[1])


def check_spec(prompt, duration):
    """Refuse what the engine would refuse, before spending GPU time."""
    if not prompt or not prompt.strip():
        raise ValueError('prompt is empty')
    if len(prompt) > MAX_PROMPT:
        raise ValueError(f'prompt is {len(prompt)} characters; the engine takes at most {MAX_PROMPT}')
    if not (MIN_S <= float(duration) <= MAX_S):
        raise ValueError(f'duration {duration} s is outside {MIN_S:g}-{MAX_S:g} s')


def generate(prompt, duration, out_path, seed=None, base=BASE):
    """POST /api/sfx/generate, then download the WAV. Returns the server's metadata (id, seed, gen_time_s...)."""
    check_spec(prompt, duration)
    body = {'prompt': prompt, 'duration': float(duration)}
    if seed is not None:
        body['seed'] = int(seed)
    meta = json.loads(_request('POST', '/api/sfx/generate', body, base=base)[1])
    url = meta['audio_url']
    _, wav = _request('GET', url if url.startswith('/') else '/' + url.split('/', 3)[-1], base=base)
    if wav[:4] != b'RIFF':
        raise VoiceStudioError(f'{url} did not return a WAV')
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, 'wb') as f:
        f.write(wav)
    return meta


def to_ogg(wav_path, tier):
    """WAV -> loudness-normalised OGG (EBU R128 loudnorm, true peak -1 dBTP) for a Roblox upload."""
    if not shutil.which('ffmpeg'):
        raise VoiceStudioError('ffmpeg not found; install it or drop --ogg')
    ogg = os.path.splitext(wav_path)[0] + '.ogg'
    lufs = TIER_LUFS.get(int(tier), -18.0)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', wav_path,
                    '-af', f'loudnorm=I={lufs}:TP=-1:LRA=11', '-ar', '48000', '-c:a', 'libvorbis', '-q:a', '6', ogg],
                   check=True)
    return ogg


def batch(spec_path, out_dir, ogg=False, base=BASE):
    """Generate every sound in a list; write manifest.json (prompt, seed, timings) so any take can be redone."""
    with open(spec_path, encoding='utf-8') as f:
        spec = json.load(f)
    for s in spec['sounds']:  # validate the whole list before the first (slow) generation
        check_spec(s['prompt'], s.get('duration', 3))
    st = status(base)
    if not st.get('available'):
        raise VoiceStudioError(f"sound effects unavailable: {st.get('reason') or 'engine not installed'}")
    manifest = []
    for s in spec['sounds']:
        variants = int(s.get('variants', 1))
        for v in range(variants):
            seed = s.get('seed', 1000) + v
            name = s['id'] if variants == 1 else f"{s['id']}_{v + 1}"
            wav = os.path.join(out_dir, name + '.wav')
            t0 = time.time()
            meta = generate(s['prompt'], s.get('duration', 3), wav, seed=seed, base=base)
            entry = {'id': name, 'prompt': s['prompt'], 'duration': s.get('duration', 3), 'seed': meta.get('seed', seed),
                     'tier': s.get('tier', 3), 'wav': os.path.basename(wav), 'gen_time_s': meta.get('gen_time_s'),
                     'wall_s': round(time.time() - t0, 2), 'engine': meta.get('engine')}
            if ogg:
                entry['ogg'] = os.path.basename(to_ogg(wav, entry['tier']))
            manifest.append(entry)
            print(f"ok {name} ({entry['wall_s']} s)")
    with open(os.path.join(out_dir, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump({'source': base, 'sounds': manifest}, f, indent=2)
    return manifest


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--url', default=BASE)
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('status')
    b = sub.add_parser('batch')
    b.add_argument('spec')
    b.add_argument('out')
    b.add_argument('--ogg', action='store_true')
    o = sub.add_parser('one')
    o.add_argument('prompt')
    o.add_argument('duration', type=float)
    o.add_argument('out')
    o.add_argument('--seed', type=int)
    a = p.parse_args(argv)
    try:
        if a.cmd == 'status':
            print(json.dumps(status(a.url), indent=2))
        elif a.cmd == 'batch':
            batch(a.spec, a.out, a.ogg, a.url)
        else:
            print(json.dumps(generate(a.prompt, a.duration, a.out, a.seed, a.url), indent=2))
    except (VoiceStudioError, ValueError) as e:
        print('error:', e, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
