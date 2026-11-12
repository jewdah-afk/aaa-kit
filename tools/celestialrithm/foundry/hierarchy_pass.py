"""Hierarchy pass for a material board, using the kit's own auditor (tools/hierarchy/hierarchy.py).

    python3 -m tools.celestialrithm.foundry.hierarchy_pass --board media/celestialrithm/frontier/board-core12 \
        --out media/celestialrithm/frontier/hierarchy/board-core12

Four questions, each with the house thresholds from HIERARCHY.md / research ch. 85:
  A. Activation ownership: at each key's press peak, is that key the first predicted fixation,
     with lift >= 1.5 and no competitor >= 0.9 of its peak?  (one owner per moment)
  B. Calm at rest: before any press, does any key accidentally own the board?  Per-key salience
     share vs the median key; an "accidental owner" holds > 1.8x the median.
  C. Colour-vision distinctness: OKLab distance between every pair of face means, normal and under
     deutan / protan / tritan simulation (Machado 2009). Pairs closer than 0.04 collide (the
     rarity-ladder threshold, HIERARCHY.md s7).
  D. Flash safety: WCAG 2.3.1 general + red flash over the whole render at its real 60 fps cadence.
"""
from __future__ import annotations

import argparse
import itertools
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from .qa import board_rects, read_mp4

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/hierarchy'))
import hierarchy as HA  # noqa: E402

PEAK_OFFSET = .18 + .10 + .15          # anticipation + activation + mid-peak (board.press_curve)


def frame_at(mp4, t):
    pr = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
                                    '-of', 'json', str(mp4)], capture_output=True, text=True, check=True).stdout)['streams'][0]
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.4f}', '-i', str(mp4), '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(pr['height'], pr['width'], 3).astype(float) / 255.0


def key_box(r, pad=10):
    x0, y0, x1, y1 = r
    return [x0 - pad, y0 - pad, x1 - x0 + 2 * pad, y1 - y0 + 2 * pad]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--board', required=True); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    meta = json.loads(Path(a.board + '.json').read_text())
    mp4 = Path(a.board + '.mp4'); out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    ids = meta['ids']; rects = board_rects(meta)
    rep = {'board': str(Path(a.board).relative_to(ROOT)) if Path(a.board).is_absolute() else a.board, 'ids': ids}

    # A. activation ownership
    A = []
    for i, mid in enumerate(ids):
        t = meta['press_starts_s'][i][0] + PEAK_OFFSET
        img = frame_at(mp4, t)
        r, sal = HA.audit(img, [key_box(rects[i])])
        A.append({'id': mid, 't': round(t, 2), 'first_in_focus': r['fixations'][0]['in_focus'], 'lift': r['lift'],
                  'competitor': r['competitor']['ratio'], 'verdict': r['verdict'],
                  'deutan': r['cvd']['deutan']['first_fixation_in_focus'], 'protan': r['cvd']['protan']['first_fixation_in_focus']})
        if i in (0, 7):
            HA.overlay(img, sal, r).save(out.parent / f'{out.name}-press-{mid}.png')
    rep['A_activation'] = A

    # B. calm at rest (before the first press)
    t0 = min(s[0] for s in meta['press_starts_s']) - .5
    img = frame_at(mp4, t0)
    sal = HA.salience_map(img)
    shares = []
    for r in rects:
        m = HA._mask(sal.shape, [key_box(r)])
        shares.append(float(sal[m].sum() / sal.sum()) / float(m.mean()))
    med = float(np.median(shares))
    rb, salb = HA.audit(img, [])
    rep['B_rest'] = {'t': round(t0, 2), 'lift_per_key': dict(zip(ids, [round(s, 2) for s in shares])),
                     'max_over_median': round(max(shares) / med, 2), 'loudest': ids[int(np.argmax(shares))],
                     'quietest': ids[int(np.argmin(shares))], 'accidental_owner': max(shares) / med > 1.8,
                     'first_fixation': rb['fixations'][0]}
    HA.overlay(img, salb, rb).save(out.parent / f'{out.name}-rest.png')

    # C. colour-vision distinctness of the materials (mean over 1 s of frames)
    frames = read_mp4(mp4, every=6)[:10]
    C = {}
    for kind in ('normal', 'deutan', 'protan', 'tritan'):
        means = []
        for r in rects:
            crop = np.concatenate([f[r[1]:r[3], r[0]:r[2]].reshape(-1, 3) for f in frames]).astype(float) / 255
            if kind != 'normal':
                crop = HA.simulate_cvd(crop[None], kind)[0]
            means.append(HA.oklab(crop[None])[0].mean(0))
        pairs = sorted(((float(np.linalg.norm(means[i] - means[j])), ids[i], ids[j]) for i, j in itertools.combinations(range(len(ids)), 2)))
        C[kind] = {'min_pair': [round(pairs[0][0], 4), pairs[0][1], pairs[0][2]],
                   'collisions_below_0.04': [[round(d, 4), x, y] for d, x, y in pairs if d < .04]}
    rep['C_cvd'] = C

    # D. flash safety at the true cadence (every frame, 60 fps)
    allf = read_mp4(mp4, every=1)
    small = [np.asarray(Image.fromarray(f).resize((64, 36), Image.BOX), float) / 255 for f in allf]
    rep['D_flash'] = HA.flash_check(small, [1000 / 60] * len(small))

    ok_a = sum(x['first_in_focus'] for x in A)
    rep['summary'] = {'activation_owner_pass': f'{ok_a}/{len(A)}', 'activation_full_PASS': sum(x['verdict'] == 'PASS' for x in A),
                      'rest_accidental_owner': rep['B_rest']['accidental_owner'], 'rest_max_over_median': rep['B_rest']['max_over_median'],
                      'cvd_collisions': {k: len(v['collisions_below_0.04']) for k, v in C.items()}, 'flash': rep['D_flash']['verdict']}
    out.with_suffix('.json').write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep['summary'], indent=1))
    for x in A:
        print(f"  {x['id']:15s} first={x['first_in_focus']!s:5s} lift={x['lift']:5.2f} comp={x['competitor']:.2f} {x['verdict']}")


if __name__ == '__main__':
    main()
