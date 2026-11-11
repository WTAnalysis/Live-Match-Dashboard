"""Reep ID crosswalk and cached, validated player headshots.

Crosswalk: https://github.com/withqwerty/reep/blob/main/data/people.csv (CC0).
Photos remain the property of their respective providers.
"""
import base64
import json
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd
from PIL import Image
import streamlit as st

ROOT = Path(__file__).parent

def transparent_headshot(payload):
    """Remove border-connected near-white background, preserving interior whites."""
    with Image.open(BytesIO(payload)) as source:
        photo=source.convert('RGBA')
    photo.thumbnail((128,128))
    if photo.getchannel('A').getextrema()[0] == 255:
        pixels=photo.load()
        width,height=photo.size
        queue=deque([(x,y) for x in range(width) for y in (0,height-1)] +
                    [(x,y) for y in range(height) for x in (0,width-1)])
        visited=set()
        while queue:
            x,y=queue.popleft()
            if (x,y) in visited: continue
            visited.add((x,y))
            r,g,b,a=pixels[x,y]
            if min(r,g,b)<240 or max(r,g,b)-min(r,g,b)>15: continue
            pixels[x,y]=(r,g,b,0)
            for nx,ny in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
                if 0<=nx<width and 0<=ny<height: queue.append((nx,ny))
    output=BytesIO()
    photo.save(output,format='PNG')
    return output.getvalue()

def identity_map():
    # Include the override contents in the cache key so verified fixes apply immediately.
    overrides=(ROOT / 'assets' / 'headshot-overrides.json').read_text(encoding='utf-8')
    return _identity_map(overrides)

@st.cache_data(show_spinner=False)
def _identity_map(override_contents):
    data = pd.read_csv(ROOT / 'assets' / 'headshot-ids.csv', dtype=str).fillna('')
    # Reject conflicting mappings rather than risk showing the wrong person.
    mapping = {opta: {column: values[0] if len(values := group[column].loc[group[column].ne('')].unique()) == 1 else ''
                   for column in ['key_fotmob', 'key_sofascore']}
            for opta, group in data.groupby('key_opta')}
    # Verified local IDs missing from the downloaded Reep snapshot.
    overrides=json.loads(override_contents)
    for opta,entry in overrides.items():
        mapping[opta]={column:entry.get(column,'') for column in ['key_fotmob','key_sofascore']}
    return mapping

@st.cache_data(ttl=3600, max_entries=10000, show_spinner=False)
def player_photo(fotmob_id, sofascore_id):
    for provider, identifier, template in [
        ('fotmob', fotmob_id, 'https://images.fotmob.com/image_resources/playerimages/{}.png'),
        ('sofascore', sofascore_id, 'https://img.sofascore.com/api/v1/player/{}/image'),
    ]:
        if not str(identifier).isdigit():
            continue
        cache = ROOT / '.headshot-cache' / 'transparent-v1' / f'{provider}-{identifier}.png'
        original = ROOT / '.headshot-cache' / f'{provider}-{identifier}.png'
        try:
            if cache.exists():
                content = cache.read_bytes()
            else:
                if original.exists():
                    payload=original.read_bytes()
                else:
                    request = Request(template.format(identifier), headers={'User-Agent': 'WTAnalysis-PlayerExplorer/1.0'})
                    with urlopen(request, timeout=6) as response:
                        payload = response.read(5_000_001)
                if len(payload) > 5_000_000:
                    continue
                content=transparent_headshot(payload)
                cache.parent.mkdir(parents=True,exist_ok=True)
                cache.write_bytes(content)
            return 'data:image/png;base64,' + base64.b64encode(content).decode('ascii')
        except Exception:
            # Missing photos, HTTP failures and invalid images try the next provider.
            continue
    return None

def load_headshots(players):
    if 'player_id' not in players:
        return {}
    mapping = identity_map()
    ids = players.player_id.dropna().astype(str).unique()
    def fetch(opta):
        entry = mapping.get(opta, {})
        return opta, player_photo(entry.get('key_fotmob', ''), entry.get('key_sofascore', ''))
    with ThreadPoolExecutor(max_workers=8) as pool:
        photos = dict(pool.map(fetch, ids))
    return {row['_player_label']: photos[str(row['player_id'])]
            for _, row in players.iterrows() if photos.get(str(row['player_id']))}
