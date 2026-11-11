"""Four longest team-specific possession chains on vertical pitches."""
import base64
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def longest_chains(events,team):
    if 'possession_chain' not in events:return []
    e=events.loc[events.team.eq(team)&events.possession_chain.notna()].copy()
    chains=[]
    # IDs are local to each team. Period separates feeds which restart IDs.
    for key,g in e.groupby(['periodId','possession_chain'],sort=False):
        if not g.typeId.isin(['Pass','Carry']).any():continue
        # Stored chain time can start at the award of a set piece, counting
        # the wait to take it. Use the actual recorded on-ball span instead.
        dead=g.typeId.isin(['Foul','Out','Corner Awarded','Foul throw-in','Offside','Offside Pass'])
        restart=pd.Series(False,index=g.index)
        for flag in ['corner','freekick','throwin','goalkick']:
            if flag in g:restart |= pd.to_numeric(g[flag],errors='coerce').eq(1)
        segments=(restart|dead.shift(fill_value=False)).cumsum()
        for segment,part in g.groupby(segments,sort=False):
            live=part.loc[part.typeId.isin(['Pass','Carry','Ball recovery','Ball touch','Take On','Good Skill'])|part.shot]
            live=supported_carries(live)
            if len(live)<2 or not live.typeId.isin(['Pass','Carry']).any():continue
            seconds=pd.to_numeric(live.timeMin,errors='coerce')*60+pd.to_numeric(live.timeSec,errors='coerce').fillna(0)
            duration=float(seconds.iloc[-1]-seconds.iloc[0])
            if not np.isfinite(duration) or duration<=0:continue
            chains.append(dict(events=live,duration=duration,
                               minute=int(live.iloc[0].timeMin),start=float(live.iloc[0].minute),key=(*key,int(segment))))
    return sorted(chains,key=lambda c:(-c['duration'],c['start']))[:4]


def supported_carries(g):
    """Reject synthetic carries contradicted by the next recorded on-ball action."""
    rejected=set()
    rows=list(g.iterrows())
    for pos,(idx,event) in enumerate(rows):
        if event.typeId!='Carry':continue
        following=next((r for _,r in rows[pos+1:] if r.typeId in ['Pass','Carry'] or bool(r.get('shot',False))),None)
        if following is None:continue
        coords=pd.to_numeric(pd.Series([event.get('end_x'),event.get('end_y'),following.get('x'),following.get('y')]),errors='coerce')
        if coords.isna().any():continue
        mismatch=pd.notna(event.get('playerName')) and pd.notna(following.get('playerName')) and event.playerName!=following.playerName
        gap=float(np.hypot(coords.iloc[0]-coords.iloc[2],coords.iloc[1]-coords.iloc[3]))
        if mismatch or gap>5:rejected.add(idx)
    return g.loc[~g.index.isin(rejected)]


def chain_figure(chains,team,badge,brand_path):
    titles=[f"<b>{c['minute']}′ · {c['duration']:.0f} seconds</b>" for c in chains]
    titles+=['No Recorded Chain']*(4-len(titles))
    fig=make_subplots(rows=2,cols=2,subplot_titles=titles,horizontal_spacing=.12,vertical_spacing=.15)
    brand='data:image/png;base64,'+base64.b64encode(brand_path.read_bytes()).decode()
    for panel in range(4):
        row,col=panel//2+1,panel%2+1
        suffix='' if panel==0 else str(panel+1)
        xr,yr='x'+suffix,'y'+suffix
        line=dict(color='#827985',width=1)
        def shape(kind,**kwargs):fig.add_shape(type=kind,xref=xr,yref=yr,line=line,**kwargs)
        shape('rect',x0=0,x1=68,y0=0,y1=105,fillcolor='white',layer='below')
        shape('line',x0=0,x1=68,y0=52.5,y1=52.5)
        shape('circle',x0=24.85,x1=43.15,y0=43.35,y1=61.65)
        for low in [True,False]:
            shape('rect',x0=13.84,x1=54.16,y0=0 if low else 88.5,y1=16.5 if low else 105)
            shape('rect',x0=24.84,x1=43.16,y0=0 if low else 99.5,y1=5.5 if low else 105)
        fig.add_layout_image(source=brand,xref=xr,yref=yr,x=34,y=52.5,sizex=17,sizey=17,
                             opacity=.5,xanchor='center',yanchor='middle',sizing='contain',layer='above')
        if badge:
            fig.add_layout_image(source=badge,xref=xr,yref=yr,x=1,y=113,sizex=8,sizey=8,
                                 xanchor='left',yanchor='middle',sizing='contain')
        if panel<len(chains):
            g=chains[panel]['events']
            supported=supported_carries(g)
            drawn=supported.loc[supported.typeId.isin(['Pass','Carry'])].copy()
            passes=g.loc[g.typeId.eq('Pass')]
            last_pass=passes.index[-1] if len(passes) else None
            substantive=g.loc[~g.typeId.isin(['Card','Player on','Player off','goal_conceded'])]
            if len(substantive) and bool(substantive.iloc[-1].shot):
                drawn=pd.concat([drawn,substantive.iloc[[-1]]]).sort_index()
            for _,e in drawn.iterrows():
                x=pd.to_numeric(e.get('x'),errors='coerce');y=pd.to_numeric(e.get('y'),errors='coerce')
                if not all(pd.notna(v) and 0<=v<=100 for v in [x,y]):continue
                if e.typeId not in ['Pass','Carry']:
                    goal=e.typeId=='Goal'
                    fig.add_trace(go.Scatter(x=[(100-y)*.68],y=[x*1.05],mode='markers',
                                             marker=dict(size=21 if goal else 12.75,symbol='star' if goal else 'circle',
                                                         color='#e5b52c' if goal else '#1675db',
                                                         line=dict(color='#8c6500' if goal else '#114c8c',width=1.5)),
                                             showlegend=False,hovertemplate=f'{e.get("playerName", "")} · {e.typeId} · {int(e.timeMin)}′<extra></extra>'),row=row,col=col)
                    continue
                ex=pd.to_numeric(e.get('end_x'),errors='coerce');ey=pd.to_numeric(e.get('end_y'),errors='coerce')
                if not all(pd.notna(v) and 0<=v<=100 for v in [x,y,ex,ey]):continue
                failed_final_pass=e.typeId=='Pass' and e.name==last_pass and e.get('outcome')=='Unsuccessful'
                colour='#d92b36' if failed_final_pass else '#208b42' if e.typeId=='Pass' else '#8c45be'
                # Both teams retain their own attacking frame; attack goes up.
                fig.add_annotation(x=(100-ey)*.68,y=ex*1.05,ax=(100-y)*.68,ay=x*1.05,xref=xr,yref=yr,
                                   axref=xr,ayref=yr,text='',showarrow=True,arrowhead=3,arrowsize=1,
                                   arrowwidth=1.7,arrowcolor=colour)
                fig.add_trace(go.Scatter(x=[(100-y)*.68,(100-ey)*.68],y=[x*1.05,ex*1.05],mode='markers',
                                         marker=dict(size=5,color=colour),showlegend=False,
                                         hovertemplate=f'{e.get("playerName", "")} · {e.typeId} · {int(e.timeMin)}′<extra></extra>'),row=row,col=col)
        fig.update_xaxes(range=[-3,71],visible=False,fixedrange=True,row=row,col=col)
        fig.update_yaxes(range=[-3,119],visible=False,scaleanchor=xr,scaleratio=1,fixedrange=True,row=row,col=col)
    fig.update_layout(height=1020,margin=dict(l=6,r=6,t=40,b=12),paper_bgcolor='white',plot_bgcolor='white',
                      font=dict(family='Comic Neue, cursive',color='#24202b'),showlegend=False,
                      hoverlabel=dict(bgcolor='white',font_color='#24202b'))
    return fig
