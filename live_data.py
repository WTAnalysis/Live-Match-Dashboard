"""Direct feed acquisition and isolated snapshots for the Live Match Dashboard."""
from pathlib import Path
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from difflib import SequenceMatcher
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
import contextlib
import io
import json
import re
import runpy
import unicodedata
import warnings
import uuid
import numpy as np
import pandas as pd
import streamlit as st

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'reference_data'
STORE=ROOT/'live_store'
EXAMPLE_OPTA='5k7bsvaizwp5ddq43obyh7vv8'
EXAMPLE_FOTMOB='6106333'
NO_XG_MODEL_VERSION='NO_XG_GP_CONTEXT_V2'

class FeedError(RuntimeError):pass

def normalise(value):
    value=unicodedata.normalize('NFKD',str(value)).encode('ascii','ignore').decode().lower()
    return re.sub(r'[^a-z0-9]','',value).replace('praha','prague')

def available_leagues():
    return sorted(p.stem for p in (SOURCE/'Scoresway Schedules').glob('*.csv') if re.fullmatch(r'[A-Za-z0-9]+_(?:2026|2627)',p.stem))

@st.cache_data(show_spinner=False)
def scoresway_schedule(code,mtime):
    frame=pd.read_csv(SOURCE/'Scoresway Schedules'/(code+'.csv'),dtype=str).fillna('')
    result=[]
    for _,r in frame.iterrows():
        if not r.get('id') or not r.get('Home_Team') or not r.get('Away_Team'):continue
        result.append(dict(id=r['id'],home=r['Home_Team'],away=r['Away_Team'],date=r.get('date',''),time=r.get('time','')))
    return sorted(result,key=lambda r:pd.to_datetime(r['date'],dayfirst=True,errors='coerce'),reverse=True)

def fotmob_file(code):
    path=SOURCE/'Fotmob Schedules'/(code.replace('_','-')+'_fotmobschedule.csv')
    return path if path.is_file() else None

@st.cache_data(show_spinner=False)
def fotmob_schedule(path,mtime):
    f=pd.read_csv(path,dtype=str).fillna('').rename(columns={'home.name':'home_team','away.name':'away_team','status.finished':'finished','status.scoreStr':'score'})
    result=[]
    for _,r in f.iterrows():
        mid=str(r.get('id','')).removesuffix('.0')
        if not mid.isdigit():continue
        date=pd.to_datetime(r.get('status.utcTime'),utc=True,errors='coerce')
        result.append(dict(id=mid,home=r.get('home_team',''),away=r.get('away_team',''),date=date.strftime('%d/%m/%Y') if pd.notna(date) else '',score=r.get('score','')))
    return result

def selectable_fixtures(matches,today=None):
    today=today or datetime.now(ZoneInfo('Europe/London')).date()
    return [m for m in matches if pd.notna(date:=pd.to_datetime(m['date'],dayfirst=True,errors='coerce')) and date.date()<=today]

def paired_index(fixture,matches):
    candidates=[]
    for i,m in enumerate(matches):
        if m['date']!=fixture['date']:continue
        similarities=[SequenceMatcher(None,normalise(m[k]),normalise(fixture[k])).ratio() for k in ['home','away']]
        if min(similarities)>=.48:candidates.append((sum(similarities),i))
    return max(candidates)[1] if candidates else None

def fetch_json(url,referer,jsonp=False):
    request=Request(url,headers={'User-Agent':'Mozilla/5.0','Accept':'application/json','Referer':referer,'Cache-Control':'no-cache'})
    try:
        with urlopen(request,timeout=25) as response:body=response.read().decode('utf-8')
    except HTTPError as error:
        raise FeedError(f'Feed returned HTTP {error.code}. The direct endpoint may be unavailable or require verification; no browser is launched.') from error
    except (URLError,TimeoutError,OSError) as error:
        raise FeedError(f'Could not reach the feed: {error}') from error
    if jsonp:
        left,right=body.find('('),body.rfind(')')
        if left>=0 and right>left:body=body[left+1:right]
    try:payload=json.loads(body)
    except ValueError as error:raise FeedError('The feed returned a non-JSON response.') from error
    if payload.get('code')=='TURNSTILE_REQUIRED':raise FeedError('FotMob requires interactive verification for this request. The dashboard will not open Chrome or bypass verification; the last successful snapshot is retained.')
    return payload

def get_opta(mid):
    if not re.fullmatch(r'[A-Za-z0-9]+',mid):raise FeedError('Invalid Opta match ID.')
    url=f'https://api.performfeeds.com/soccerdata/matchevent/ft1tiv1inq7v1sk3y9tv12yh5/{mid}?_rt=c&_lcl=en&_fmt=jsonp&sps=widgets&_clbk=liveMatch'
    data=fetch_json(url,'https://www.scoresway.com/',True)
    if str(data.get('matchInfo',{}).get('id'))!=mid:raise FeedError('Opta returned a different match ID.')
    return data

def get_fotmob(mid):
    if not str(mid).isdigit():raise FeedError('Invalid FotMob match ID.')
    data=fetch_json(f'https://www.fotmob.com/api/data/matchDetails?matchId={mid}','https://www.fotmob.com/')
    returned=data.get('general',{}).get('matchId')
    if str(returned)!=str(mid):raise FeedError('FotMob returned a different match ID.')
    return data

def flatten_events(opta):
    rows=[]
    for event in opta.get('liveData',{}).get('event',[]):
        row={k:v for k,v in event.items() if k!='qualifier'}
        for i,q in enumerate(event.get('qualifier') or []):
            for k,v in q.items():row[f'qualifier/{i}/{k}']=v
        rows.append(row)
    frame=pd.DataFrame(rows)
    for c in ['playerId','playerName','assist','keyPass','periodId','timeMin','timeSec']:
        if c not in frame:frame[c]=np.nan
    return frame

def qualifiers(row):
    result={}
    for c in row.index:
        if c.endswith('/qualifierId') and pd.notna(row[c]):
            key=pd.to_numeric(row[c],errors='coerce')
            if pd.notna(key):result[int(key)]=str(row.get(c.replace('qualifierId','value'),''))
    return result

def squad_rows(raw,opta,fotmob):
    """Recover full named squads, including players with no event yet."""
    clubs=opta['matchInfo']['contestant']
    names=json.loads((ROOT/'assets/player_names.json').read_text(encoding='utf-8'))
    names.update(raw.dropna(subset=['playerId','playerName']).drop_duplicates('playerId').set_index('playerId').playerName.to_dict())
    lineup=fotmob.get('content',{}).get('lineup') or {}
    rows=[]
    fm_lookups={}
    for side in ['home','away']:
        squad=lineup.get(side+'Team') or {}
        fm_lookups[side]={str(p.get('shirtNumber')):p.get('name') for key in ['starters','subs','substitutes'] for p in squad.get(key,[]) or []}
    formation_dict=pd.read_excel(STORE/'Excel Files/formation_dict.xlsx').set_index('formation_code')
    formation_dict.columns=formation_dict.columns.map(str)
    for _,r in raw.loc[pd.to_numeric(raw.typeId,errors='coerce').eq(34)].iterrows():
        club=next((c for c in clubs if c['id']==r.contestantId),None)
        if not club:continue
        q=qualifiers(r)
        ids=[v.strip() for v in q.get(30,'').split(',')]
        nums=[v.strip() for v in q.get(59,'').split(',')]
        slots=[pd.to_numeric(v.strip(),errors='coerce') for v in q.get(131,'').split(',')]
        fcode=pd.to_numeric(q.get(130),errors='coerce')
        for i,(pid,number) in enumerate(zip(ids,nums)):
            slot=slots[i] if i<len(slots) else 0
            name=names.get(pid) or fm_lookups.get(club.get('position'),{}).get(number) or f'Name Unavailable (#{number})'
            names[pid]=name
            pos=formation_dict.loc[fcode].get(str(int(slot))) if fcode in formation_dict.index and pd.notna(slot) and slot>0 else np.nan
            rows.append(dict(player_id=pid,player_name=name,squad_number=number,contestant_id=club['id'],team_name=club['name'],formation_position=slot,
                             position=pos,position1=pos,is_starter='yes' if pd.notna(slot) and slot>0 else 'no',minutes_played=0,subbed_on='no',time_on=np.nan))
    return pd.DataFrame(rows).drop_duplicates('player_id') if rows else pd.DataFrame(),names

def validate_pair(opta,fotmob):
    clubs=opta['matchInfo']['contestant'];general=fotmob.get('general') or {}
    for side in ['home','away']:
        a=next((c['name'] for c in clubs if c.get('position')==side),'')
        b=(general.get(side+'Team') or {}).get('name','')
        if a and b and SequenceMatcher(None,normalise(a),normalise(b)).ratio()<.48:
            raise FeedError(f'The selected feeds do not appear to be the same fixture: {a} / {b}. Choose the matching FotMob fixture.')
    a=pd.to_datetime(opta['matchInfo'].get('date','').removesuffix('Z'),utc=True,errors='coerce')
    b=pd.to_datetime(general.get('matchTimeUTCDate') or general.get('matchTimeUTC'),utc=True,errors='coerce')
    if pd.notna(a) and pd.notna(b) and abs((a-b).total_seconds())>48*3600:raise FeedError('The selected feeds have different match dates.')

def process_feeds(opta,fotmob):
    no_xg=fotmob is None
    fotmob=fotmob or {}
    validate_pair(opta,fotmob)
    raw=flatten_events(opta)
    if raw.empty:
        return raw,pd.DataFrame(),pd.DataFrame(),pd.DataFrame(),['Waiting for recorded match events.']
    full_squad,names=squad_rows(raw,opta,fotmob)
    if not pd.to_numeric(raw.periodId,errors='coerce').isin([1,2,3,4]).any():
        note='Starting lineups announced. Match has not started yet.' if not full_squad.empty else 'Waiting for the announced starting lineups.'
        return raw,pd.DataFrame(),full_squad,pd.DataFrame(),[note]
    if full_squad.empty:raise FeedError('Opta has not published the starting lineup yet. Try Refresh when the lineups are available.')
    shots=pd.DataFrame((fotmob.get('content',{}).get('shotmap') or {}).get('shots') or [])
    for col in ['id','eventType','isBlocked','isOnTarget','expectedGoals','expectedGoalsOnTarget','situation','shotType','isOwnGoal']:
        if col not in shots:shots[col]=pd.Series(dtype='float64' if col in ['id','expectedGoals','expectedGoalsOnTarget'] else 'object')
    from physical_functions import physical_performance_from_matchdetails
    physical=physical_performance_from_matchdetails(fotmob,int(fotmob.get('general',{}).get('matchId',0)))
    teamdata=pd.DataFrame(opta['matchInfo']['contestant'])[['id','name']]
    seed=dict(df=raw.copy(),teamdata=teamdata,formation_dict=pd.read_excel(STORE/'Excel Files/formation_dict.xlsx'),
              matchlink=opta['matchInfo']['id'],matchinfo=opta['matchInfo'],shots=shots,physical_performance=physical,
              pd=pd,np=np,re=re,display=lambda *a:None,_live_name_lookup=names,_live_no_xg=no_xg,
              _live_finished=str(opta.get('liveData',{}).get('matchDetails',{}).get('matchStatus','')).lower() in ['played','finished','fulltime','full time'])
    with warnings.catch_warnings(),contextlib.redirect_stdout(io.StringIO()):
        warnings.simplefilter('ignore')
        output=runpy.run_path(str(ROOT/'notebook_processing.py'),init_globals=seed)
    events=output['df'];players=output['starting_lineups']
    if 'onGoalShot' in events:events['onGoalShot']=events.onGoalShot.map(lambda value:json.dumps(value) if isinstance(value,(dict,list)) else value)
    # The notebook can omit untouched bench players; retain the original squad.
    known=set(players.player_id.astype(str))
    players=pd.concat([players,full_squad.loc[~full_squad.player_id.isin(known)]],ignore_index=True)
    players['player_name']=players.player_id.map(names).fillna(players.player_name)
    players['squad_number']=players.squad_number.map(lambda n:str(n).strip().removesuffix('.0') if pd.notna(n) else np.nan)
    # Correct zero-minute, unused and late-substitute status using actual events.
    end=float((pd.to_numeric(raw.loc[raw.periodId.isin([1,2,3,4]),'timeMin'],errors='coerce')*60+
               pd.to_numeric(raw.loc[raw.periodId.isin([1,2,3,4]),'timeSec'],errors='coerce').fillna(0)).max())
    for idx,p in players.iterrows():
        mine=raw.loc[raw.playerId.astype(str).eq(str(p.player_id))]
        on=mine.loc[pd.to_numeric(mine.typeId,errors='coerce').eq(19)]
        off=mine.loc[pd.to_numeric(mine.typeId,errors='coerce').eq(18)]
        starter=str(p.get('is_starter')).lower()=='yes'
        start=0 if starter else float(on.iloc[0].timeMin*60+on.iloc[0].timeSec) if len(on) else None
        finish=float(off.iloc[0].timeMin*60+off.iloc[0].timeSec) if len(off) else end
        players.at[idx,'minutes_played']=max(0,(finish-start)/60) if start is not None else 0
        players.at[idx,'time_on']=start/60 if start is not None else np.nan
        players.at[idx,'subbed_on']='yes' if len(on) else 'no'
    notes=[]
    if no_xg:notes.append('This competition has no xG coverage. Using Opta only, with xThreat, Most Shots and Threat Value rankings.')
    elif shots.empty:notes.append('FotMob has no shot-map data yet. xG is unavailable until published; xThreat is shown meanwhile.')
    if not physical.empty:
        # ID -> shirt/team matching is reliable even for abbreviated player names.
        fm_stats=fotmob.get('content',{}).get('playerStats') or {}
        stat_by_id={str(p.get('id',k)):p for k,p in fm_stats.items()}
        fm_general=fotmob.get('general') or {}
        opta_clubs={c['position']:c for c in opta['matchInfo']['contestant']}
        team_map={str((fm_general.get(side+'Team') or {}).get('id')):opta_clubs.get(side,{}) for side in ['home','away']}
        lookup={(str(p.contestant_id),str(p.squad_number).removesuffix('.0')):p.player_name for _,p in players.iterrows()}
        physical['scoresway_name']=[lookup.get((str(team_map.get(str(row.teamId),{}).get('id')),str(stat_by_id.get(str(row.playerId),{}).get('shirtNumber')).removesuffix('.0'))) for _,row in physical.iterrows()]
        physical['scoresway_team']=[team_map.get(str(row.teamId),{}).get('name') for _,row in physical.iterrows()]
    if no_xg:
        from no_xg_model import prepare_no_xg_match
        clubs={c['position']:c['name'] for c in opta['matchInfo']['contestant']}
        match_id=opta['matchInfo']['id']
        schedule=pd.DataFrame([dict(id=match_id,Home_Team=clubs['home'],Away_Team=clubs['away'],
                                  date=opta['matchInfo'].get('date'))]).set_index('id')
        events,players,_=prepare_no_xg_match(events,players,match_id,schedule)
    return raw,events,players,physical,notes

def snapshot_metadata(opta,fotmob,mid,fid):
    fotmob=fotmob or {}
    details=opta.get('liveData',{}).get('matchDetails') or {}
    status=str(details.get('matchStatus','Unknown'))
    finished=status.lower() in ['played','finished','fulltime','full time']
    if status=='Unknown':finished=bool((fotmob.get('header',{}).get('status') or {}).get('finished'))
    clubs=opta['matchInfo']['contestant']
    h=next(c for c in clubs if c.get('position')=='home');a=next(c for c in clubs if c.get('position')=='away')
    score=(details.get('scores') or {}).get('total') or (details.get('scores') or {}).get('ft') or {}
    return dict(opta_id=mid,fotmob_id=str(fid),home=h['name'],away=a['name'],home_id=h['id'],away_id=a['id'],
                date=pd.to_datetime(opta['matchInfo'].get('date','').removesuffix('Z')).strftime('%d/%m/%Y'),
                status=status,finished=finished,score=score,period=details.get('periodId'),
                fetched_at=datetime.now(timezone.utc).isoformat(),opta_updated=opta['matchInfo'].get('lastUpdated'),
                fotmob_status=fotmob.get('header',{}).get('status',{}))

def cache_folder(code,mid,fid):return STORE/'snapshots'/code/(mid+'_'+str(fid))

def load_snapshot(code,mid,fid):
    root=cache_folder(code,mid,fid);pointer=root/'latest.json'
    if not pointer.exists():return None
    try:
        generation=json.loads(pointer.read_text())['generation'];folder=root/generation
        meta=json.loads((folder/'metadata.json').read_text(encoding='utf-8'))
        if str(fid)=='opta-only' and meta.get('no_xg_model_version')!=NO_XG_MODEL_VERSION:
            opta=json.loads((folder/'opta.json').read_text(encoding='utf-8'))
            return save_snapshot(code,mid,fid,opta,None)
        return dict(metadata=meta,raw=pd.read_pickle(folder/'raw.pkl'),events=pd.read_pickle(folder/'events.pkl'),
                    players=pd.read_pickle(folder/'players.pkl'),physical=pd.read_pickle(folder/'physical.pkl'),folder=folder)
    except (OSError,ValueError,KeyError):return None

def refresh_snapshot(code,mid,fid):
    from league_lookup import league_has_xg
    if not league_has_xg(code):return save_snapshot(code,mid,'opta-only',get_opta(mid),None)
    with ThreadPoolExecutor(max_workers=2) as pool:
        opta_future=pool.submit(get_opta,mid);fotmob_future=pool.submit(get_fotmob,fid)
        opta=opta_future.result();fotmob=fotmob_future.result()
    return save_snapshot(code,mid,fid,opta,fotmob)

def save_snapshot(code,mid,fid,opta,fotmob):
    raw,events,players,physical,notes=process_feeds(opta,fotmob)
    meta=snapshot_metadata(opta,fotmob,mid,fid);meta['notes']=notes
    if fotmob is None:meta['no_xg_model_version']=NO_XG_MODEL_VERSION
    root=cache_folder(code,mid,fid);generation=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'_'+uuid.uuid4().hex[:8]
    folder=root/generation;folder.mkdir(parents=True,exist_ok=False)
    for name,frame in [('raw',raw),('events',events),('players',players),('physical',physical)]:frame.to_pickle(folder/(name+'.pkl'))
    (folder/'opta.json').write_text(json.dumps(opta,ensure_ascii=False),encoding='utf-8')
    (folder/'fotmob.json').write_text(json.dumps(fotmob,ensure_ascii=False),encoding='utf-8')
    (folder/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False),encoding='utf-8')
    # The existing formation/lineup code reads this isolated raw snapshot only.
    raw_folder=STORE/'Match Data'/code;raw_folder.mkdir(parents=True,exist_ok=True)
    temp=raw_folder/(mid+'.tmp.csv');raw.to_csv(temp,index=False);temp.replace(raw_folder/(mid+'.csv'))
    # Publish only once the entire refresh has processed successfully.
    pointer=root/'latest.tmp.json';pointer.write_text(json.dumps({'generation':generation}));pointer.replace(root/'latest.json')
    import shutil
    generations=sorted((p for p in root.iterdir() if p.is_dir()),key=lambda p:p.name,reverse=True)
    for old in generations[2:]:
        shutil.rmtree(old,ignore_errors=True)
    return load_snapshot(code,mid,fid)
