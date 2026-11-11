"""Shared transparent Reep/FotMob/Sofascore portraits from Player Data Explorer."""
import base64
import importlib.util
import sys
from functools import lru_cache
from io import BytesIO
from pathlib import Path

from PIL import Image
import pandas as pd

@lru_cache(maxsize=1)
def photo_service():
    source=Path(__file__).resolve().parent/'headshots.py'
    name='wt_shared_player_headshots'
    if name not in sys.modules:
        spec=importlib.util.spec_from_file_location(name,source)
        module=importlib.util.module_from_spec(spec)
        sys.modules[name]=module
        spec.loader.exec_module(module)
    return sys.modules[name]

def player_faces(roster):
    if 'player_id' not in roster: return {}
    players=roster.dropna(subset=['player_id']).drop_duplicates('player_id').copy()
    players['player_id']=players.player_id.astype(str)
    players['_player_label']=players.player_id
    return photo_service().load_headshots(players)

def portrait(roster):
    """Resolve by exact player ID; never guess between multiple identities."""
    if 'player_id' not in roster: return None
    ids=roster.player_id.dropna().astype(str).unique()
    if len(ids)!=1: return None
    source=player_faces(roster).get(ids[0])
    if source:
        with Image.open(BytesIO(base64.b64decode(source.split(',',1)[1]))) as image:
            return image.convert('RGBA')
    return None

def show_face_lineup(*args, **kwargs):
    import streamlit as st
    from lineups import lineup_figure
    with st.expander('Player faces · lineup and bench'):
        with st.spinner('Loading player faces…'):
            faces=player_faces(args[0])
        fig,missing,total=lineup_figure(*args,**kwargs,player_faces=faces)
        st.plotly_chart(fig,width='content',theme=None,key='face-lineup-'+str(args[1])+'-'+str(kwargs.get('ending',False)))
        st.caption('FotMob faces via Reep, with Sofascore fallback. Shirts identify players without available photos.')
