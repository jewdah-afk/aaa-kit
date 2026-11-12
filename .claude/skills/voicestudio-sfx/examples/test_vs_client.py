#!/usr/bin/env python3
"""Tests vs_client.py against a mock VoiceStudio backend (same routes and status codes as
backend/api/routers/sfx.py), so the client is checked without a GPU or the real app."""
import io
import json
import os
import struct
import sys
import tempfile
import threading
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vs_client as vs  # noqa: E402

STATE = {'available': True, 'calls': []}


def tiny_wav(seconds):
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(48000)
        w.writeframes(struct.pack('<h', 0) * int(48000 * seconds))
    return buf.getvalue()


class Mock(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body, ctype='application/json'):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == '/api/sfx/status':
            ok = STATE['available']
            return self.send(200, {'installed': ok, 'available': ok, 'supported': True,
                                   'reason': None if ok else 'Sound effects are not installed.', 'license': 'Apache-2.0'})
        if self.path.startswith('/audio/'):
            return self.send(200, tiny_wav(0.1), 'audio/wav')
        self.send(404, {'detail': 'not found'})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        STATE['calls'].append(body)
        if not STATE['available']:
            return self.send(409, {'detail': 'Sound effects are not installed.'})
        if not (1 <= body['duration'] <= 30):
            return self.send(422, {'detail': 'duration must be 1 to 30 seconds'})
        seed = body.get('seed', 4242)
        self.send(200, {'id': f'sfx{len(STATE["calls"])}', 'audio_url': f'/audio/sfx{len(STATE["calls"])}.wav',
                        'duration_s': body['duration'], 'gen_time_s': 0.01, 'seed': seed, 'engine': 'moss-soundeffect'})


def run():
    srv = ThreadingHTTPServer(('127.0.0.1', 0), Mock)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{srv.server_address[1]}'
    passed = failed = 0

    def check(name, cond):
        nonlocal passed, failed
        if cond:
            passed += 1
        else:
            failed += 1
            print('FAIL', name)

    with tempfile.TemporaryDirectory() as tmp:
        st = vs.status(base)
        check('status reports available', st['available'] is True and st['reason'] is None)

        meta = vs.generate('a coin chime', 1.5, os.path.join(tmp, 'coin.wav'), seed=7, base=base)
        check('generate returns metadata', meta['seed'] == 7 and meta['engine'] == 'moss-soundeffect')
        with open(os.path.join(tmp, 'coin.wav'), 'rb') as f:
            check('generate writes a WAV', f.read(4) == b'RIFF')
        check('generate sends seed and duration', STATE['calls'][-1] == {'prompt': 'a coin chime', 'duration': 1.5, 'seed': 7})

        for bad, why in [(('', 2), 'empty prompt'), (('x' * 501, 2), 'prompt over 500'), (('ok', 0.5), 'duration under 1'),
                         (('ok', 31), 'duration over 30')]:
            n = len(STATE['calls'])
            try:
                vs.generate(*bad, os.path.join(tmp, 'x.wav'), base=base)
                check(f'refuses {why}', False)
            except ValueError:
                check(f'refuses {why} before calling the server', len(STATE['calls']) == n)

        spec = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sounds.json')
        out = os.path.join(tmp, 'batch')
        manifest = vs.batch(spec, out, base=base)
        with open(spec, encoding='utf-8') as f:
            sounds = json.load(f)['sounds']
        expected = sum(int(s.get('variants', 1)) for s in sounds)
        check('batch renders every variant', len(manifest) == expected)
        check('batch writes a manifest', os.path.exists(os.path.join(out, 'manifest.json')))
        check('variants get consecutive seeds', [m['seed'] for m in manifest if m['id'].startswith('ui_click')] == [11, 12, 13])
        check('variant files are numbered', os.path.exists(os.path.join(out, 'ui_click_3.wav')))
        check('single sounds keep their id', os.path.exists(os.path.join(out, 'chest_open.wav')))
        check('manifest keeps the tier', next(m for m in manifest if m['id'] == 'chest_open')['tier'] == 1)

        STATE['available'] = False
        try:
            vs.batch(spec, os.path.join(tmp, 'b2'), base=base)
            check('batch stops when the engine is missing', False)
        except vs.VoiceStudioError as e:
            check('batch stops when the engine is missing', 'not installed' in str(e))
        try:
            vs.generate('a coin chime', 2, os.path.join(tmp, 'y.wav'), base=base)
            check('409 surfaces as an error', False)
        except vs.VoiceStudioError as e:
            check('409 surfaces as an error', '409' in str(e))

        try:
            vs.status('http://127.0.0.1:9')
            check('unreachable app gives a clear error', False)
        except vs.VoiceStudioError as e:
            check('unreachable app gives a clear error', 'not reachable' in str(e))

    srv.shutdown()
    print(f'{passed} passed, {failed} failed')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(run())
