"""Use the same team log and Opta badge source as laptopdashboard.py."""
from pathlib import Path
import csv
import io
import base64
import re
import unicodedata
from urllib.request import urlopen
from urllib.parse import urlencode
from PIL import Image
import streamlit as st

TEAMLOG=Path(__file__).resolve().parent/'Excel Files/teamlog.csv'
if not TEAMLOG.is_file():TEAMLOG=Path(__file__).resolve().parent/'assets'/'teamlog.csv'

def normalise(name):
    text=unicodedata.normalize('NFKD',str(name).casefold())
    return re.sub(r'[^a-z0-9]','',text.encode('ascii','ignore').decode())

ALIASES={
    'heart of midlothian':'hearts','dundee united':'dundee utd',
    'leeds united':'leeds','bournemouth':'afc bournemouth','coventry city':'coventry',
    'auxerre':'aj auxerre','bayer 04 leverkusen':'leverkusen','bayern münchen':'bayern munich',
    'borussia dortmund':'dortmund',"borussia m'gladbach":'monchengladbach',
    'hamburger sv':'hamburg','internazionale':'inter milan','milan':'ac milan',
    'mainz 05':'mainz','monaco':'as monaco','olympique lyonnais':'lyon',
    'olympique marseille':'marseille','paris saint-germain':'psg','köln':'fc koln',
    'schalke 04':'fc schalke','villarreal':'villareal',
}

def badge_urls(teams,team_ids=None):
    with TEAMLOG.open(encoding='utf-8-sig',newline='') as f:
        mapping={normalise(r['name']):r['id'].strip() for r in csv.DictReader(f)}
    aliases={normalise(k):normalise(v) for k,v in ALIASES.items()}
    result={}
    for team in teams:
        name=normalise(team)
        teamid=(team_ids or {}).get(team) or mapping.get(name) or mapping.get(aliases.get(name,''))
        if teamid:
            result[team]='https://omo.akamai.opta.net/image.php?'+urlencode(dict(h='www.scoresway.com',sport='football',entity='team',description='badges',dimensions=150,id=teamid))
    return result

@st.cache_data(ttl=86400,show_spinner=False)
def embedded_badge(url):
    """Self-contained images survive browser canvas / PNG export."""
    with urlopen(url,timeout=12) as response:
        data=response.read()
    picture=Image.open(io.BytesIO(data)).convert('RGBA')
    output=io.BytesIO()
    picture.save(output,format='PNG')
    return 'data:image/png;base64,'+base64.b64encode(output.getvalue()).decode('ascii')

def badge_sources(teams,team_ids=None):
    sources={};failed=[]
    for team,url in badge_urls(teams,team_ids).items():
        try:sources[team]=embedded_badge(url)
        except Exception:
            sources[team]=url
            failed.append(team)
    return sources,failed

@st.cache_resource(ttl=3600,show_spinner=False)
def load_team_badge(team,teamlog_mtime):
    url=badge_urls([team]).get(team)
    if not url:return None
    try:
        with urlopen(url,timeout=8) as response:data=response.read()
        return Image.open(io.BytesIO(data)).convert('RGBA')
    except Exception:return None
