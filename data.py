"""Local match catalogue and notebook-compatible event calculations."""
from pathlib import Path
from difflib import SequenceMatcher
import math
import json
import numpy as np
import pandas as pd
import streamlit as st

BASE = Path(__file__).resolve().parent/'live_store'
LOGS = BASE/'Processed Matches'/'Season Match Logs'
MATCHES = BASE/'Processed Matches'/'Matches'
NUMERIC = ['periodId','timeMin','timeSec','expectedGoals','expectedGoalsOnTarget','possession_chain_time','owngoal','isOwnGoal']

def leagues():
    codes = {p.name for p in MATCHES.iterdir() if p.is_dir()}
    codes |= {p.stem.removesuffix('_PAR') for p in LOGS.glob('*.csv') if '_formation' not in p.stem and '_faced' not in p.stem}
    return sorted(c for c in codes if len(c.split('_')) == 2)

def log_path(code):
    return next((p for p in [LOGS/(code+'_PAR.csv'),LOGS/(code+'.csv')] if p.exists()),None)

def signature(code):
    paths=[BASE/'Scoresway Schedules'/(code+'.csv'),log_path(code),MATCHES/code,BASE/'Fotmob Schedules'/(code.replace('_','-')+'_fotmobschedule.csv')]
    return tuple((str(p),p.stat().st_mtime_ns) for p in paths if p and p.exists())

@st.cache_data(show_spinner=False)
def catalogue(code, stamp):
    schedule=BASE/'Scoresway Schedules'/(code+'.csv')
    records={}
    if schedule.exists():
        s=pd.read_csv(schedule,dtype=str).fillna('')
        for _,r in s.iterrows():
            records[r['id']]={'id':r['id'],'home':r['Home_Team'],'away':r['Away_Team'],'date':r.get('date','')}
    files={}
    for p in sorted((MATCHES/code).glob('*processed*.xlsx')):
        key=p.name.split('_processed')[0]
        if key not in files or '_PAR' in p.stem: files[key]=str(p)
    lp=log_path(code)
    log_ids=set()
    if lp:
        cols=['match_id','Home_Team','Away_Team','date','team_name','venue']
        frame=pd.read_csv(lp,usecols=lambda c:c in cols,dtype=str).drop_duplicates()
        if 'match_id' in frame:
            for mid,g in frame.groupby('match_id'):
                log_ids.add(mid)
                if mid not in records:
                    row=g.iloc[0]
                    if 'Home_Team' in g and pd.notna(row['Home_Team']):
                        records[mid]={'id':mid,'home':row['Home_Team'],'away':row['Away_Team'],'date':row.get('date','')}
    result=[]
    for mid in set(files)|log_ids:
        if mid not in records:
            # Without venue metadata there is no safe way to assign home/away.
            continue
        result.append({**records[mid],'file':files.get(mid),'log':str(lp) if lp else None})
    result.sort(key=lambda r:pd.to_datetime(r['date'],dayfirst=True,errors='coerce') if r['date'] else pd.Timestamp.min,reverse=True)
    return result

@st.cache_data(show_spinner=False)
def load_match(file, log, mid, stamp):
    if file:
        return pd.read_excel(file)
    parts=[]
    for chunk in pd.read_csv(log,chunksize=100000,low_memory=False):
        selected=chunk.loc[chunk.match_id.astype(str).eq(mid)]
        if len(selected): parts.append(selected)
    return pd.concat(parts,ignore_index=True) if parts else pd.DataFrame()

def prepare(raw,home,away):
    d=raw.copy()
    for col in NUMERIC:
        if col not in d: d[col]=np.nan
        d[col]=pd.to_numeric(d[col],errors='coerce')
    names=list(d.team_name.dropna().unique())
    if len(names)!=2: raise ValueError(f'Expected two event teams; found {names}')
    from itertools import permutations
    score=lambda a,b:SequenceMatcher(None,a.casefold(),b.casefold()).ratio()
    h,a=max(permutations(names),key=lambda p:score(p[0],home)+score(p[1],away))
    # Venue is stronger evidence than a team-name similarity when available.
    if 'venue' in d:
        hs=d.loc[d.venue.eq('Home'),'team_name'].dropna()
        if len(hs): h=hs.iloc[0];a=next(n for n in names if n!=h)
    d['team']=d.team_name.replace({h:home,a:away})
    d=d.loc[d.periodId.isin([1,2,3,4])].sort_values(['periodId','timeMin','timeSec'],kind='stable').reset_index(drop=True)
    if d.empty: raise ValueError('No usable match events in periods 1–4.')
    d['minute']=d.timeMin+d.timeSec.fillna(0)/60
    d['clock']=d.minute
    previous=None
    for period,start in {1:0,2:45,3:90,4:105}.items():
        mask=d.periodId.eq(period)
        if not mask.any():continue
        low=d.loc[mask,'minute'].min()
        if period>1 and low<start-20:d.loc[mask,'minute']+=start-low
        low=d.loc[mask,'minute'].min()
        if previous is not None and low<=previous:d.loc[mask,'minute']+=previous+1/60-low
        previous=d.loc[mask,'minute'].max()
    d['goal']=d.typeId.eq('Goal')|d.typeId.eq('Own Goal')
    own=d.typeId.eq('Own Goal')|d.owngoal.eq(1)|d.isOwnGoal.eq(1)
    d['scorer']=d.team.where(d.goal)
    d.loc[d.goal&own,'scorer']=np.where(d.loc[d.goal&own,'team'].eq(home),away,home)
    d['shot']=d.expectedGoals.notna()|d.typeId.isin(['Goal','Own Goal','Miss','Attempt Saved','Post','Shot','Saved Shot'])
    # Own goals affect the score, but are not a chance for the benefiting side.
    d['xg']=d.expectedGoals.fillna(0).clip(lower=0).where(~own,0)
    d['xgot']=d.expectedGoalsOnTarget.fillna(0).clip(lower=0).where(~own,0)
    for i,t in enumerate([home,away]):
        d[f'xg{i}']=d.xg.where(d.team.eq(t),0).cumsum()
        xt=pd.to_numeric(d['xT_value'],errors='coerce').fillna(0) if 'xT_value' in d else pd.Series(0.,index=d.index)
        d[f'xt{i}']=xt.where(d.team.eq(t)&d.typeId.isin(['Pass','Carry']),0).cumsum()
        d[f'poss{i}']=d.possession_chain_time.fillna(0).clip(lower=0).where(d.team.eq(t),0).cumsum()
    total=d.poss0+d.poss1
    d['share0']=np.where(total.gt(0),100*d.poss0/total,50)
    d['share1']=100-d.share0
    return d

@st.cache_data(show_spinner=False)
def simulate_shots(home_probs, away_probs, simulations=100000):
    """Replay each chance as an independent Bernoulli trial; stable across reruns."""
    rng=np.random.default_rng(20261019)
    scores=[]
    for chances in [home_probs,away_probs]:
        tally=np.zeros(simulations,dtype=int)
        for chance in chances:
            tally += rng.random(simulations)<np.clip(chance,0,1)
        scores.append(tally)
    h,a=scores
    grid=np.zeros((6,6))
    np.add.at(grid,(np.minimum(h,5),np.minimum(a,5)),1/simulations)
    pairs,counts=np.unique(np.column_stack(scores),axis=0,return_counts=True)
    likely=tuple(int(v) for v in pairs[counts.argmax()])
    return grid,(float(np.mean(h>a)),float(np.mean(h==a)),float(np.mean(h<a))),likely

def probabilities(home_rate,away_rate):
    # Analytic independent Poisson model; retain the entire tail in 5+.
    def pmf(rate):
        n=max(30,int(rate+12*math.sqrt(rate+1)))
        p=np.array([math.exp(-rate+k*math.log(rate)-math.lgamma(k+1)) if rate else float(k==0) for k in range(n)])
        return p/p.sum()
    h,a=pmf(home_rate),pmf(away_rate)
    joint=np.outer(h,a)
    wins=(float(np.tril(joint,-1).sum()),float(np.trace(joint)),float(np.triu(joint,1).sum()))
    grid=np.outer(np.r_[h[:5],h[5:].sum()],np.r_[a[:5],a[5:].sum()])
    return grid,wins

def player_log_path(code,mid):
    candidates=[BASE/'Processed Matches'/'Player Logs'/code/(mid+'_playerlog_PAR.xlsx'),
                BASE/'Processed Matches'/'Player Logs'/code/(mid+'_playerlog.xlsx'),
                BASE/'Processed Matches'/'Season Player Logs'/(code+'_PAR.csv'),
                BASE/'Processed Matches'/'Season Player Logs'/(code+'.csv')]
    return next((p for p in candidates if p.is_file()),None)

@st.cache_data(show_spinner=False)
def match_players(path,mid,mtime,include_unused=False):
    p=Path(path)
    if p.suffix=='.xlsx':
        try:
            frame=pd.read_excel(p)
        except (OSError,ValueError):
            # Individual workbooks can be locked by Excel or unavailable in
            # OneDrive. The season CSV contains the same match records.
            code=p.parent.name
            fallback=next((f for f in [BASE/'Processed Matches'/'Season Player Logs'/(code+'_PAR.csv'),BASE/'Processed Matches'/'Season Player Logs'/(code+'.csv')] if f.is_file()),None)
            if fallback is None:return pd.DataFrame()
            p=fallback
    if p.suffix=='.csv':
        columns=['match_id','contestant_id','player_id','player_name','playerName','team_name','squad_number','PAR','Threat Value','minutes_played','position','position1','position2','position3','position4','position5','formation_position','time_on','is_starter','subbed_on']
        frame=pd.read_csv(p,usecols=lambda c:c in columns,low_memory=False)
        if 'match_id' not in frame:return pd.DataFrame()
        frame=frame.loc[frame.match_id.astype(str).eq(mid)].copy()
    if 'PAR' in frame:frame['PAR']=pd.to_numeric(frame['PAR'],errors='coerce')
    if not include_unused and 'minutes_played' in frame:frame=frame.loc[pd.to_numeric(frame.minutes_played,errors='coerce').gt(0)]
    identity=['player_id'] if 'player_id' in frame else ['team_name','player_name']
    frame=frame.drop_duplicates(identity)
    return frame

def top_players(path,mid,mtime,metric="PAR"):
    frame=match_players(path,mid,mtime)
    if metric not in frame:return pd.DataFrame()
    frame=frame.copy()
    frame[metric]=pd.to_numeric(frame[metric],errors='coerce')
    return frame.dropna(subset=[metric]).sort_values(metric,ascending=False,kind='stable').head(5)

@st.cache_data(show_spinner=False)
def recover_bench(roster,code,mid,source_stamp,season_stamp):
    raw=BASE/'Match Data'/code/(mid+'.csv')
    if not raw.is_file():return roster
    events=pd.read_csv(raw,low_memory=False)
    if not {'typeId','contestantId'}.issubset(events):return roster
    rows=events.loc[pd.to_numeric(events.typeId,errors='coerce').eq(34)]
    season=BASE/'Processed Matches'/'Season Player Logs'/(code+'_PAR.csv')
    name_index=Path(__file__).parent/'assets'/'player_names.json'
    lookup=json.loads(name_index.read_text(encoding='utf-8')) if name_index.exists() else {}
    if season.is_file():
        names=pd.read_csv(season,usecols=lambda c:c in ['player_id','player_name']).dropna()
        if {'player_id','player_name'}.issubset(names):lookup.update(dict(zip(names.player_id.astype(str),names.player_name)))
    result=roster.copy();existing=set(result.player_id.astype(str)) if 'player_id' in result else set()
    additions=[]
    for _,row in rows.iterrows():
        q={int(row[c]):str(row.get(c.replace('qualifierId','value'),'')) for c in events if c.endswith('/qualifierId') and pd.notna(row[c])}
        if 30 not in q or 59 not in q:continue
        club=roster.loc[roster.contestant_id.astype(str).eq(str(row.contestantId))] if 'contestant_id' in roster else pd.DataFrame()
        if club.empty:continue
        ids=[v.strip() for v in q[30].split(',')];numbers=[v.strip() for v in q[59].split(',')]
        for player_id,number in zip(ids[11:],numbers[11:]):
            if player_id in existing:continue
            additions.append(dict(player_id=player_id,player_name=lookup.get(player_id,f'Name Unavailable (#{number})'),
                                  team_name=club.iloc[0].team_name,contestant_id=row.contestantId,squad_number=number,
                                  is_starter='no',minutes_played=0,subbed_on='no'))
            existing.add(player_id)
    if additions:result=pd.concat([result,pd.DataFrame(additions)],ignore_index=True)
    return result

def event_leaders(events):
    e=events.loc[events.playerName.notna()].copy()
    flag=lambda col:pd.to_numeric(e[col],errors='coerce').eq(1) if col in e else pd.Series(False,index=e.index)
    e['xG']=e.xg
    e['Most Shots']=(e.shot&~e.typeId.eq('Own Goal')&~flag('owngoal')&~flag('isOwnGoal')).astype(int)
    e['Chances Created']=(flag('keyPass')|flag('assist')).astype(int)
    e['Defensive Actions']=e.typeId.isin(['Interception','Tackle','Ball recovery','Defensive Duel','Challenge','Clearance']).astype(int)
    e['Completed Passes']=(e.typeId.eq('Pass')&e.outcome.eq('Successful')).astype(int)
    metrics=['xG','Most Shots','Chances Created','Defensive Actions','Completed Passes']
    totals=e.groupby(['team','playerName'],as_index=False)[metrics].sum()
    return {metric:totals.loc[totals[metric].gt(0)].sort_values([metric,'playerName'],ascending=[False,True],kind='stable').head(3) for metric in metrics}

def xgot_status(events,teams):
    """No unblocked on-target attempts is a valid zero, not missing coverage."""
    number=lambda name:pd.to_numeric(events[name],errors='coerce') if name in events else pd.Series(float('nan'),index=events.index)
    eligible=events.shot & ((number('isOnTarget').eq(1)&~number('isBlocked').eq(1))|events.typeId.eq('Goal'))
    eligible &= ~number('owngoal').eq(1)&~number('isOwnGoal').eq(1)
    available=events.expectedGoalsOnTarget.notna().any() and all(
        events.loc[events.team.eq(team),'expectedGoalsOnTarget'].notna().any() or
        not eligible.loc[events.team.eq(team)].any() for team in teams)
    return available,eligible&events.expectedGoalsOnTarget.isna()

def goal_details(events,team):
    """Credit the latest eligible assist in the fifteen seconds before each goal."""
    assists=pd.to_numeric(events['assist'],errors='coerce').eq(1) if 'assist' in events else pd.Series(False,index=events.index)
    seconds=pd.to_numeric(events.timeMin,errors='coerce')*60+pd.to_numeric(events.timeSec,errors='coerce').fillna(0)
    details=[]
    for idx,goal in events.loc[events.scorer.eq(team)].iterrows():
        own=goal.typeId=='Own Goal' or goal.team!=team
        candidates=events.loc[assists & events.typeId.ne('Carry') & events.team.eq(team) &
                              events.periodId.eq(goal.periodId) & (events.index<idx) &
                              (seconds.loc[idx]-seconds).between(0,15)]
        assister=None if own or candidates.empty else candidates.iloc[-1].get('playerName')
        details.append(dict(minute=int(goal.timeMin),scorer=goal.get('playerName','Unknown'),
                            assist=assister if pd.notna(assister) else None,own_goal=own))
    return details
