from pathlib import Path
import pandas as pd
import streamlit as st
from data import BASE

@st.cache_data(show_spinner=False)
def formation_labels(code,mid,stamp):
    labels={}
    raw_path=BASE/'Match Data'/code/(mid+'.csv')
    dictionary=BASE/'Excel Files'/'formation_dict.xlsx'
    if raw_path.exists() and dictionary.exists():
        raw=pd.read_csv(raw_path,low_memory=False)
        lookup=pd.read_excel(dictionary).set_index('formation_code').formation.to_dict()
        types=pd.to_numeric(raw.typeId,errors='coerce')
        snapshots=raw.loc[types.isin([34,40])].copy()
        snapshots['_phase']=pd.to_numeric(snapshots.periodId,errors='coerce').where(~pd.to_numeric(snapshots.typeId,errors='coerce').eq(34),-1)
        snapshots=snapshots.sort_values(['_phase','timeMin','timeSec'],kind='stable')
        for _,row in snapshots.iterrows():
            for col in raw:
                if not col.endswith('/qualifierId') or pd.to_numeric(row[col],errors='coerce')!=130:continue
                value=pd.to_numeric(row.get(col.replace('qualifierId','value')),errors='coerce')
                formation=lookup.get(value)
                if pd.isna(formation):continue
                text='-'.join(str(formation).removesuffix('.0'))
                club=str(row.contestantId)
                labels.setdefault(club,{'start':text,'end':text})
                labels[club]['end']=text
    # Processed formation stints provide a backup when raw snapshots are absent.
    for suffix in ['_formation_PAR.csv','_formation.csv']:
        path=BASE/'Processed Matches'/'Formation Logs'/code/(mid+suffix)
        if not path.exists():continue
        frame=pd.read_csv(path)
        if {'team_name','formation_label'}.issubset(frame):
            order=[c for c in ['periodId','start_event_order','stint_number'] if c in frame]
            if order:frame=frame.sort_values(order,kind='stable')
            for team,g in frame.dropna(subset=['formation_label']).groupby('team_name'):
                labels[team]={'start':str(g.iloc[0].formation_label),'end':str(g.iloc[-1].formation_label)}
        break
    return labels


@st.cache_data(show_spinner=False)
def ending_roster(roster,events,code,mid,stamp):
    """Replay formation snapshots and substitutions, preserving dismissals."""
    result=roster.copy()
    result['is_starter']='no'
    result['_exit_order']=float('inf')
    result['_ending_status']=''
    raw_path=BASE/'Match Data'/code/(mid+'.csv')
    raw=pd.read_csv(raw_path,low_memory=False) if raw_path.exists() else pd.DataFrame()
    dictionary=BASE/'Excel Files'/'formation_dict.xlsx'
    formations=pd.read_excel(dictionary).set_index('formation_code') if dictionary.exists() else pd.DataFrame()
    formations.columns=formations.columns.map(str)
    notes=[]
    for team,players in roster.groupby('team_name'):
        team_indices=players.index
        flags=players.is_starter.astype(str).str.lower().isin(['yes','true','1','1.0']) if 'is_starter' in players else pd.to_numeric(players.time_on,errors='coerce').eq(0)
        active=set(players.loc[flags,'player_id'].astype(str))
        positions={}
        for _,p in players.iterrows():
            final=next((p.get('position'+str(i)) for i in range(5,0,-1) if pd.notna(p.get('position'+str(i)))),p.get('position'))
            positions[str(p.player_id)]=final
        club=str(players.contestant_id.dropna().iloc[0]) if 'contestant_id' in players and players.contestant_id.notna().any() else None
        snapshots=raw.loc[raw.contestantId.astype(str).eq(club)] if club and 'contestantId' in raw else pd.DataFrame()
        if len(snapshots):
            pending=[]
            # Starting formation rows use period 16; replay them before play.
            snapshots=snapshots.copy()
            snapshots['_phase']=pd.to_numeric(snapshots.periodId,errors='coerce').where(~pd.to_numeric(snapshots.typeId,errors='coerce').eq(34),-1)
            snapshots=snapshots.sort_values(['_phase','timeMin','timeSec'],kind='stable')
            for _,e in snapshots.iterrows():
                kind=pd.to_numeric(e.typeId,errors='coerce');pid=str(e.get('playerId',''))
                if kind in [34,40]:
                    q={int(e[c]):str(e.get(c.replace('qualifierId','value'),'')) for c in raw if c.endswith('/qualifierId') and pd.notna(e[c])}
                    if not {30,131,130}.issubset(q):continue
                    ids=[x.strip() for x in q[30].split(',')]
                    slots=[pd.to_numeric(x.strip(),errors='coerce') for x in q[131].split(',')]
                    fcode=pd.to_numeric(q[130],errors='coerce')
                    snapshot={pid:int(slot) for pid,slot in zip(ids,slots) if pd.notna(slot) and 1<=slot<=11}
                    if not snapshot:continue
                    active=set(snapshot)
                    for pid,slot in snapshot.items():
                        if fcode in formations.index:
                            pos=formations.loc[fcode].get(str(slot))
                            # Repair the known duplicated striker slot.
                            if fcode==18 and slot==11:pos='LCF(2)'
                            # Generic CF/CF slots in these two-striker shapes
                            # need separate display locations (slot convention).
                            if fcode in [2,3] and slot in [9,10]:
                                pos='LCF(2)' if slot==9 else 'RCF(2)'
                            if pd.notna(pos):positions[pid]=pos
                elif kind==18:
                    active.discard(pid)
                    pending.append((e.periodId,float(e.timeMin)*60+float(e.timeSec),positions.get(pid)))
                elif kind==19:
                    active.add(pid)
                    clock=float(e.timeMin)*60+float(e.timeSec)
                    inherited=next((k for k,item in enumerate(pending) if item[0]==e.periodId and 0<=clock-item[1]<=10 and pd.notna(item[2])),None)
                    if inherited is not None:
                        positions[pid]=pending.pop(inherited)[2]
                        continue
                    # Player log position stints resolve later substitutions.
                    p=players.loc[players.player_id.astype(str).eq(pid)]
                    if len(p):
                        r=p.iloc[0]
                        positions[pid]=next((r.get('position'+str(i)) for i in range(5,0,-1) if pd.notna(r.get('position'+str(i)))),r.get('position'))
        else:notes.append(team+': final shape uses player-log position stints; original formation snapshots unavailable.')
        canonical=events.loc[events.team_name.eq(team),'team']
        display=canonical.iloc[0] if len(canonical) else team
        ev=events.loc[events.team.eq(display)]
        # Event names bridge roster IDs when processed event IDs are absent.
        for _,e in ev.iterrows():
            match=players.loc[players.player_name.eq(e.playerName)]
            if match.empty:continue
            pid=str(match.iloc[0].player_id);idx=match.index[0]
            if e.typeId=='Player on' and snapshots.empty:active.add(pid)
            dismissed=e.typeId=='Card' and any(pd.to_numeric(e.get(k,0),errors='coerce')==1 for k in ['redcard','yellowcard2'])
            if e.typeId=='Player off' or dismissed:
                active.discard(pid)
                result.loc[idx,'_exit_order']=float(e.minute)
                result.loc[idx,'_ending_status']=('Sent Off' if dismissed else 'Off')+f' {int(e.timeMin)}′'
        for idx,p in players.iterrows():
            pid=str(p.player_id)
            result.loc[idx,'is_starter']='yes' if pid in active else 'no'
            if pid in active:result.loc[idx,'position1']=positions.get(pid,p.get('position1'))
    # Keep the full squad so unused substitutes remain available to the sidebar.
    result.loc[result.is_starter.ne('yes')&result._ending_status.eq(''),'_ending_status']='Unused'
    return result,notes
