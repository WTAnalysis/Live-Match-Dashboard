"""Shared competition names for selectors, tables, HTML and exports."""
from pathlib import Path
from functools import lru_cache
import json
import pandas as pd

ROOT=Path(__file__).resolve().parent
WORKBOOK=ROOT/'reference_data/Excel Files/league_dict.xlsx'
PORTABLE=ROOT/'assets'/'league_names.json'
ALIASES={'EUROPA':'EUL'}
DEFAULT_NAMES={'ARG1':'Argentine Primera Division','BRA1':'Brazilian Serie A','USA1':'Major League Soccer'}

def season_code(value):
    text=str(value).strip().removesuffix('.0')
    if '/' in text:
        first,last=text.split('/',1)
        return first[-2:]+last[-2:]
    return text

@lru_cache(maxsize=3)
def read_lookup(path,mtime):
    path=Path(path)
    if path.suffix=='.json':return json.loads(path.read_text(encoding='utf-8'))
    frame=pd.read_excel(path,dtype=str).dropna(subset=['Competition','leagueid'])
    exact={};fallback={};logos={};logo_fallback={};xg={};xg_fallback={}
    for _,row in frame.sort_values('Season',ascending=False).iterrows():
        code=row['leagueid'].strip().upper();name=row['Competition'].strip()
        fallback.setdefault(code,name)
        flag=str(row.get('xG','')).strip().lower()
        enabled=flag not in ['no','false','0','n']
        xg_fallback.setdefault(code,enabled)
        if pd.notna(row['Season']):xg.setdefault(code+'_'+season_code(row['Season']),enabled)
        if pd.notna(row['Season']):exact.setdefault(code+'_'+season_code(row['Season']),name)
        if pd.notna(row.get('logo')) and str(row['logo']).strip():
            logo=str(row['logo']).strip()
            logo_fallback.setdefault(code,logo)
            if pd.notna(row['Season']):logos.setdefault(code+'_'+season_code(row['Season']),logo)
    return {'exact':exact,'fallback':fallback,'logos':logos,'logo_fallback':logo_fallback,'xg':xg,'xg_fallback':xg_fallback}

def lookup():
    path=WORKBOOK if WORKBOOK.is_file() else PORTABLE
    return read_lookup(str(path),path.stat().st_mtime_ns) if path.is_file() else {'exact':{},'fallback':{}}

def league_metadata(source):
    competition,season,*_=Path(source).stem.split('_')
    mapping=lookup();code=competition.upper()
    canonical=ALIASES.get(code,code)
    name=mapping['exact'].get(code+'_'+season,mapping['exact'].get(canonical+'_'+season,
         mapping['fallback'].get(code,mapping['fallback'].get(canonical,DEFAULT_NAMES.get(code,competition)))))
    label=season if season.startswith('20') else '20'+season[:2]+'/'+season[2:]
    return {'league_name':name,'season_label':label}

def league_label(source):
    info=league_metadata(source)
    return info['league_name']+' · '+info['season_label']

def league_logo(source):
    competition,season,*_=Path(source).stem.split('_')
    code=competition.upper();canonical=ALIASES.get(code,code);mapping=lookup()
    exact=mapping.get('logos',{});fallback=mapping.get('logo_fallback',{})
    return exact.get(code+'_'+season) or exact.get(canonical+'_'+season) or fallback.get(code) or fallback.get(canonical)

def league_has_xg(source):
    competition,season,*_=Path(source).stem.split('_')
    code=competition.upper();canonical=ALIASES.get(code,code);mapping=lookup()
    exact=mapping.get('xg',{});fallback=mapping.get('xg_fallback',{})
    return exact.get(code+'_'+season,exact.get(canonical+'_'+season,fallback.get(code,fallback.get(canonical,True))))

def save_portable_lookup():
    PORTABLE.parent.mkdir(exist_ok=True)
    PORTABLE.write_text(json.dumps(lookup(),ensure_ascii=False,indent=2),encoding='utf-8')
