"""Fetch the VFX reference sets from NASA's public-domain image library (images-api.nasa.gov) and resize to 1024 px.
Each entry: set, file, query, nasa_id, title, and the VFX lesson we took from it.  python3 fetch_refs.py [set]
NASA imagery is generally not copyrighted (credit "NASA"); check each item's notes before using outside reference."""
import json, os, sys, urllib.request, urllib.parse, io
from PIL import Image

SETS = {
 'space': [
  ('pillars', 'Pillars of Creation Webb', 'layered dust with lit rims: dark mass + bright edge is the depth cue'),
  ('carina', 'Cosmic Cliffs Carina Webb', 'gas wall with glowing ridge line; stars in front sell the scale'),
  ('southern_ring', 'Southern Ring Nebula Webb', 'concentric shells, orange outer vs blue inner: temperature as colour'),
  ('crab', 'Crab Nebula Hubble', 'filament web over a soft glow: two frequencies of detail'),
  ('helix', 'Helix Nebula', 'eye shape: ring of knots pointing inward = radial streaks'),
  ('cats_eye', "Cat's Eye Nebula", 'nested ellipses offset from each other give spin'),
  ('eagle', 'Eagle Nebula Hubble', 'backlit plume silhouettes'),
  ('orion', 'Orion Nebula Hubble mosaic', 'core blown to white, colour only at mid-falloff'),
  ('m87_jet', 'M87 jet Hubble', 'one narrow jet beats a cone: thin and bright'),
  ('cartwheel', 'Cartwheel Galaxy Webb', 'ring galaxy: shockwave as the structure itself'),
  ('whirlpool', 'Whirlpool Galaxy M51 Hubble', 'spiral arms = dust lanes inside the glow, not on top'),
  ('sombrero', 'Sombrero Galaxy', 'edge-on disc with dark lane across a bright bulge'),
  ('black_hole_sim', 'black hole accretion disk illustration', 'lensed far side of the disc arcs over the horizon'),
  ('supernova', 'supernova remnant Cassiopeia A', 'shredded shell, knots of hot colour'),
  ('stephan', "Stephan's Quintet Webb", 'shock front glow between objects'),
  ('tarantula', 'Tarantula Nebula Webb', 'cavity carved by a hot core: bright centre, walls lit from inside'),
  ('butterfly', 'Butterfly Nebula Hubble', 'twin lobes from a pinched waist: bipolar burst'),
  ('lagoon', 'Lagoon Nebula Hubble', 'twisted dark ribbons through bright gas'),
  ('veil', 'Veil Nebula Hubble', 'thin filaments like hair: wisps for trails'),
 ],
 'sun': [
  ('prominence', 'solar prominence eruption SDO', 'plasma loops: arcs anchored at both ends'),
  ('coronal_loops', 'coronal loops TRACE', 'many thin glowing strands in one arch bundle'),
  ('flare_x', 'X-class solar flare SDO', 'a flare blooms white then cools to orange'),
  ('cme', 'coronal mass ejection SOHO', 'expanding bubble with bright leading edge'),
  ('eclipse_corona', 'total solar eclipse corona', 'black disc with feathered rays: the perfect aura silhouette'),
  ('filament', 'solar filament SDO', 'dark thread in front of bright plasma'),
  ('sunspot', 'sunspot close up', 'radial penumbra filaments'),
  ('sdo_304', 'SDO 304 angstrom sun', 'fuzzy limb: soft halo past a hard edge'),
  ('parker', 'Parker Solar Probe corona WISPR', 'streamers converge to the source'),
  ('diamond_ring', 'eclipse diamond ring', 'one point of light breaking the rim = the impact frame'),
  ('plasma_rain', 'coronal rain sun', 'material falling back along the loop'),
  ('aia_composite', 'SDO AIA multiwavelength composite', 'stacking colour channels for layered heat'),
  ('flare_loops', 'solar flare post-flare loops', 'loops lit in sequence after the burst'),
  ('euv_sun', 'sun extreme ultraviolet SDO full disk', 'hot active regions glow, quiet sun dim'),
  ('helioseismic', 'sun magnetic field lines', 'field lines as ribbon paths'),
 ],
 'atmosphere': [
  ('aurora_iss', 'aurora from space station', 'curtains with sharp lower edge, faded top'),
  ('aurora_corona', 'aurora corona overhead', 'rays converging to one point overhead'),
  ('red_sprite', 'red sprite lightning', 'jellyfish-like discharge: tendrils hanging down'),
  ('blue_jet', 'blue jet lightning from orbit', 'cone of discharge rising from a cloud top'),
  ('lightning_iss', 'lightning from the space station', 'cloud lit from inside: glow beneath a surface'),
  ('airglow', 'airglow limb earth', 'thin layered band on the curve: rim light'),
  ('noctilucent', 'noctilucent clouds', 'rippled glowing filaments in the dark'),
  ('volcano_iss', 'volcano eruption from space station', 'plume with rolling heads'),
  ('hurricane_eye', 'hurricane eye from space station', 'spiral bands around a clear eye: a vortex that reads'),
  ('city_lights', 'city lights at night from space', 'networks of points: sparse sparkle texture'),
  ('sunrise_limb', 'orbital sunrise atmosphere', 'thin bright arc, colour bands'),
  ('rocket_plume', 'rocket launch exhaust plume night', 'core white, shock diamonds, smoke catching light'),
  ('reentry', 'spacecraft reentry plasma trail', 'streak with hot head and cooling tail'),
  ('star_trails', 'star trails from space station', 'circular streaks = motion over time'),
  ('glint', 'sun glint ocean from space', 'specular hot spot over a dark surface'),
 ],
}

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'refbot/1.0'}), timeout=40).read()

BLOCK = ('First Full-Color Images', 'Mars', 'Benefit from', 'Space Science', 'Waking Black Hole')  # wrong hits seen on the contact sheet

def best(query):
    j = json.loads(get('https://images-api.nasa.gov/search?' + urllib.parse.urlencode({'q': query, 'media_type': 'image'})))
    for it in j['collection']['items'][:6]:
        d = it['data'][0]
        if any(b in d.get('title', '') for b in BLOCK): continue
        links = json.loads(get(it['href']))
        pick = [u for u in links if u.lower().endswith(('~large.jpg', '~medium.jpg', '~orig.jpg'))]
        pick.sort(key=lambda u: (0 if '~large' in u else 1 if '~medium' in u else 2))
        if pick: return d, pick[0].replace('http://', 'https://')
    return None, None

if __name__ == '__main__':
    only = sys.argv[1:]; manifest = json.load(open('manifest.json')) if os.path.exists('manifest.json') else []
    have = {m['file'] for m in manifest}
    for s, items in SETS.items():
        if only and s not in only: continue
        os.makedirs(s, exist_ok=True)
        for key, q, lesson in items:
            f = f'{s}/{key}.jpg'
            if f in have: continue
            try:
                d, url = best(q)
                if not url: print('none', q); continue
                im = Image.open(io.BytesIO(get(url))).convert('RGB'); im.thumbnail((1024, 1024)); im.save(f, quality=85)
                manifest.append({'set': s, 'file': f, 'query': q, 'nasa_id': d['nasa_id'], 'title': d.get('title', ''), 'credit': 'NASA (images.nasa.gov)', 'lesson': lesson})
                print('ok', f, '|', d.get('title', '')[:60])
            except Exception as e: print('fail', q, e)
    json.dump(manifest, open('manifest.json', 'w'), indent=1)
