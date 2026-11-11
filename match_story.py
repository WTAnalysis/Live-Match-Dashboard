import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def box_entries(events):
    e=events.copy()
    for c in ['x','y','end_x','end_y']:e[c]=pd.to_numeric(e[c],errors='coerce')
    inside=lambda x,y:x.ge(83)&x.le(100)&y.between(21.1,78.9)
    valid=e[['x','y','end_x','end_y']].notna().all(axis=1)
    valid &= e[['x','y','end_x','end_y']].ge(0).all(axis=1)&e[['x','y','end_x','end_y']].le(100).all(axis=1)
    for flag in ['corner','throwin','freekick']:
        if flag in e:valid &= ~pd.to_numeric(e[flag],errors='coerce').eq(1)
    return e.loc[valid&e.typeId.isin(['Pass','Carry'])&e.outcome.eq('Successful')&
                 ~inside(e.x,e.y)&inside(e.end_x,e.end_y)].copy()


def period_bins(events):
    bins=pd.Series(0,index=events.index,dtype=int)
    for period,low,high,start in [(1,0,2,0),(2,3,5,45),(3,6,6,90),(4,7,7,105)]:
        mask=events.periodId.eq(period)
        minutes=pd.to_numeric(events.loc[mask,'timeMin'],errors='coerce').fillna(start)
        if len(minutes) and period>1 and minutes.min()<start-20:minutes=minutes+start
        bins.loc[mask]=np.floor(minutes/15).clip(low,high).astype(int)
    return bins


def story_figure(events,entries,teams,colours,outlines):
    e=events.copy();e['bin']=period_bins(e)
    b=entries.copy();b['bin']=period_bins(b) if len(b) else pd.Series(dtype=int)
    n=8 if e.periodId.eq(4).any() else 7 if e.periodId.eq(3).any() else 6
    labels=['0–15′','15–30′','30–45+′','45–60′','60–75′','75–90+′','90–105+′','105–120+′'][:n]
    use_xg=e.expectedGoals.notna().any()
    e['_chance']=e.xg if use_xg else pd.to_numeric(e.get('xT_value',pd.Series(0.,index=e.index)),errors='coerce').fillna(0).where(e.typeId.isin(['Pass','Carry']),0)
    fig=make_subplots(rows=3,cols=1,shared_xaxes=True,vertical_spacing=.07,subplot_titles=['<b>xG Created</b>' if use_xg else '<b>xThreat Created</b>','<b>Shots</b>','<b>Box Entries</b>'])
    for i,t in enumerate(teams):
        team=e.loc[e.team.eq(t)]
        metrics=[team.groupby('bin')._chance.sum(),team.groupby('bin').shot.sum(),b.loc[b.team.eq(t)].groupby('bin').size()]
        for row,values in enumerate(metrics,1):
            vals=values.reindex(range(n),fill_value=0)
            fig.add_trace(go.Bar(x=labels,y=vals,name=t,marker=dict(color=colours[i],line=dict(color=outlines[i],width=1.5)),
                                 offsetgroup=str(i),text=[f'{v:.2f}' if row==1 else str(int(v)) for v in vals],textposition='auto',
                                 hovertemplate=t+' · %{x}<br>%{y}<extra></extra>'),row=row,col=1)
    fig.update_layout(title=dict(text='<b>15-Minute Match Story</b>',x=.5),height=660,barmode='group',showlegend=False,
                      template='plotly_white',paper_bgcolor='white',plot_bgcolor='white',
                      font=dict(family='Comic Sans MS, cursive',color='#24202b'),margin=dict(l=40,r=25,t=95,b=45))
    return fig

def block_story(events,teams,colours,outlines,kind,badges,brand_path):
    import base64
    e=events.copy();e['bin']=period_bins(e)
    n=8 if e.periodId.eq(4).any() else 7 if e.periodId.eq(3).any() else 6
    labels=['0–15′','15–30′','30–45+′','45–60′','60–75′','75–90+′','90–105+′','105–120+′'][:n]
    possession=kind=='poss'
    if possession:
        e['_value']=pd.to_numeric(e.possession_chain_time,errors='coerce').fillna(0).clip(lower=0)
    elif kind=='xg':e['_value']=e.xg
    else:e['_value']=pd.to_numeric(e.get('xT_value',pd.Series(0.,index=e.index)),errors='coerce').fillna(0).where(e.typeId.isin(['Pass','Carry']),0)
    sums=[e.loc[e.team.eq(t)].groupby('bin')._value.sum().reindex(range(n),fill_value=0) for t in teams]
    total=sums[0]+sums[1]
    fig=go.Figure()
    for i,t in enumerate(teams):
        values=100*sums[i]/total.where(total.gt(0)) if possession else sums[i]
        fig.add_trace(go.Bar(x=labels,y=values,name=t,offsetgroup=str(i),
                             marker=dict(color=colours[i],line=dict(color=outlines[i],width=1.5)),
                             text=[f'{v:.1f}%' if possession and pd.notna(v) else '' if pd.isna(v) else f'{v:.2f}' for v in values],textposition='auto',
                             hovertemplate=t+' · %{x}<br>%{y:.1f}%<extra></extra>' if possession else t+' · %{x}<br>%{y:.2f}<extra></extra>'))
    title='True Possession · 15-Minute Blocks' if possession else 'xG · 15-Minute Blocks' if kind=='xg' else 'xThreat · 15-Minute Blocks'
    fig.update_layout(title=dict(text=f'<b>{title}</b>',x=.5,xanchor='center',y=.935,yanchor='middle',font=dict(size=22)),height=360,
                      barmode='group',showlegend=False,template='plotly_white',paper_bgcolor='white',plot_bgcolor='white',
                      font=dict(family='Comic Sans MS, cursive',color='#24202b'),margin=dict(l=45,r=25,t=60,b=45))
    fig.update_xaxes(title='Minutes',showgrid=False)
    fig.update_yaxes(title='True Possession Share' if possession else 'Total Expected Goals' if kind=='xg' else 'Total xThreat',
                     range=[0,100] if possession else None,gridcolor='#eee9ed')
    for i,team in enumerate(teams):
        if badges.get(team):fig.add_layout_image(source=badges[team],xref='paper',yref='paper',x=i*.09,y=1.14,sizex=.075,sizey=.14,xanchor='left',yanchor='middle',sizing='contain')
    brand='data:image/png;base64,'+base64.b64encode(brand_path.read_bytes()).decode()
    fig.add_layout_image(source=brand,xref='paper',yref='paper',x=1,y=1.14,sizex=.1,sizey=.14,xanchor='right',yanchor='middle',sizing='contain')
    return fig


def entries_figure(entries,teams,colours,outlines,badges):
    fig=make_subplots(rows=1,cols=2,subplot_titles=[f'<b>{t} · {sum(entries.team.eq(t))} Entries</b>' for t in teams],horizontal_spacing=.12)
    for i,t in enumerate(teams):
        suffix='' if i==0 else '2';xr,yr='x'+suffix,'y'+suffix
        def shape(kind,**kw):fig.add_shape(type=kind,xref=xr,yref=yr,line=dict(color='#827985',width=1),**kw)
        shape('rect',x0=0,x1=68,y0=0,y1=105,fillcolor='white',layer='below')
        shape('line',x0=0,x1=68,y0=52.5,y1=52.5)
        shape('circle',x0=24.85,x1=43.15,y0=43.35,y1=61.65)
        for low in [True,False]:
            shape('rect',x0=14.35,x1=53.65,y0=0 if low else 87.15,y1=17.85 if low else 105)
            shape('rect',x0=24.84,x1=43.16,y0=0 if low else 99.5,y1=5.5 if low else 105)
        for _,e in entries.loc[entries.team.eq(t)].iterrows():
            x0,y0=(100-e.y)*.68,e.x*1.05;x1,y1=(100-e.end_y)*.68,e.end_x*1.05
            fig.add_annotation(x=x1,y=y1,ax=x0,ay=y0,xref=xr,yref=yr,axref=xr,ayref=yr,text='',showarrow=True,
                               arrowhead=3,arrowwidth=1.5,arrowcolor=colours[i],opacity=.8)
            fig.add_trace(go.Scatter(x=[x0,x1],y=[y0,y1],mode='markers',marker=dict(size=5,color=colours[i],line=dict(color=outlines[i],width=1)),
                                     hovertemplate=f'{e.playerName} · {e.typeId} · {int(e.timeMin)}′<extra></extra>',showlegend=False),row=1,col=i+1)
        if badges.get(t):fig.add_layout_image(source=badges[t],xref=xr,yref=yr,x=34,y=52.5,sizex=14,sizey=14,opacity=.3,xanchor='center',yanchor='middle',sizing='contain')
        fig.update_xaxes(range=[-3,71],visible=False,row=1,col=i+1)
        fig.update_yaxes(range=[-3,108],visible=False,scaleanchor=xr,scaleratio=1,row=1,col=i+1)
    fig.update_layout(title=dict(text='<b>Box Entries</b>',x=.5),height=610,template='plotly_white',showlegend=False,
                      font=dict(family='Comic Sans MS, cursive',color='#24202b'),margin=dict(l=15,r=15,t=95,b=20),paper_bgcolor='white',plot_bgcolor='white')
    return fig


def add_substitutions(fig,events,teams,kind):
    import base64
    svg='<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 40 40"><circle cx="20" cy="20" r="19" fill="white" stroke="#dedade"/><path d="M8 19 A12 12 0 0 1 29 12" fill="none" stroke="#168c43" stroke-width="4"/><path d="M25 7 L33 14 L23 15 Z" fill="#168c43"/><path d="M32 21 A12 12 0 0 1 11 28" fill="none" stroke="#d92b36" stroke-width="4"/><path d="M15 33 L7 26 L17 25 Z" fill="#d92b36"/></svg>'
    icon='data:image/svg+xml;base64,'+base64.b64encode(svg.encode()).decode()
    span=100 if kind=='poss' else max(float(events[f'{kind}0'].max()),float(events[f'{kind}1'].max()),.3)*1.15
    if kind in ['xg','xt']:
        low=min(float(events[f'{kind}0'].min()),float(events[f'{kind}1'].min()),0)
        fig.update_yaxes(range=[low-span*.055,span])
    else:fig.update_yaxes(range=[-5,105])
    width=max(90,float(events.minute.max())+1)
    subs=events.loc[events.typeId.isin(['Player on','Player off'])]
    for (team,period,minute),g in subs.groupby(['team','periodId','timeMin'],sort=False):
        if team not in teams:continue
        off=', '.join(g.loc[g.typeId.eq('Player off'),'playerName'].dropna().astype(str)) or 'Not Recorded'
        on=', '.join(g.loc[g.typeId.eq('Player on'),'playerName'].dropna().astype(str)) or 'Not Recorded'
        label=f'{team} · {int(minute)}′<br>Off: {off}<br>On: {on}'
        event=g.iloc[0];i=teams.index(team)
        x=float(event.minute);y=float(event[f'{kind}{i}' if kind in ['xg','xt'] else f'share{i}'])
        fig.add_layout_image(source=icon,xref='x',yref='y',x=x,y=y,sizex=width*.026,sizey=span*.085,
                             xanchor='center',yanchor='middle',sizing='contain',layer='above')
        fig.add_trace(go.Scatter(x=[x],y=[y],mode='markers',marker=dict(size=21,color='rgba(0,0,0,0)'),
                                 text=[label],hovertemplate='%{text}<extra></extra>',name='Substitution',showlegend=False))
    cards=events.loc[events.typeId.eq('Card')]
    flag=lambda row,key:pd.to_numeric(pd.Series([row.get(key,0)]),errors='coerce').fillna(0).iloc[0]==1
    for _,event in cards.iterrows():
        if event.team not in teams:continue
        red=flag(event,'redcard');second=flag(event,'yellowcard2');yellow=flag(event,'yellowcard')
        if not (red or second or yellow):continue
        i=teams.index(event.team);x=float(event.minute);y=float(event[f'{kind}{i}' if kind in ['xg','xt'] else f'share{i}'])
        label='Second Yellow / Red Card' if second else 'Red Card' if red else 'Yellow Card'
        colour='#e32e3a' if red or second else '#f2cf29'
        card_svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 12 20"><rect x="1" y="1" width="10" height="18" rx="1" fill="{colour}" stroke="#514958" stroke-width="1"/></svg>'
        card_uri='data:image/svg+xml;base64,'+base64.b64encode(card_svg.encode()).decode()
        fig.add_layout_image(source=card_uri,xref='x',yref='y',x=x,y=y,sizex=width*.022,sizey=span*.09,
                             xanchor='center',yanchor='middle',sizing='contain',layer='above')
        fig.add_trace(go.Scatter(x=[x],y=[y],mode='markers',marker=dict(size=16,color='rgba(0,0,0,0)'),
                                 text=[f'{event.team} · {event.get("playerName", "")} · {int(event.timeMin)}′<br>{label}'],
                                 hovertemplate='%{text}<extra></extra>',name=label,showlegend=False))
    return fig
