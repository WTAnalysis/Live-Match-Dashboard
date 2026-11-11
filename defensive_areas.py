"""Defensive actions and Pressing 12 on team-oriented vertical pitches."""
import base64
import html
import math
import numpy as np
import pandas as pd
import plotly.graph_objects as go

DEFENSIVE_TYPES=['Interception','Tackle','Ball recovery','Defensive Duel','Challenge','Clearance']

def defensive_data(events,team):
    pressing=pd.to_numeric(events['pressing_action_12'],errors='coerce').eq(1) if 'pressing_action_12' in events else pd.Series(False,index=events.index)
    e=events.loc[events.team.eq(team)&(events.typeId.isin(DEFENSIVE_TYPES)|pressing)].copy()
    e['_pressing12']=pressing.loc[e.index]
    for field in ['playing_position','playing_positon']:
        if field in e:e=e.loc[~e[field].astype(str).str.strip().str.upper().eq('GK')]
    e['x']=pd.to_numeric(e.x,errors='coerce');e['y']=pd.to_numeric(e.y,errors='coerce')
    e=e.loc[e.x.between(0,100)&e.y.between(0,100)]
    lanes=np.where(e.x<33.33,0,np.where(e.x<66.6,1,2))
    counts=np.bincount(lanes,minlength=3)
    shares=counts/counts.sum() if counts.sum() else np.zeros(3)
    return e,counts,shares

def defensive_figure(events,team,base,outline,badge,brand_path):
    e,counts,shares=defensive_data(events,team)
    fig=go.Figure();line=dict(color='#928b93',width=1)
    def shape(kind,**kw):fig.add_shape(type=kind,line=line,layer='below',**kw)
    shape('rect',x0=0,x1=68,y0=0,y1=105,fillcolor='white')
    shape('line',x0=0,x1=68,y0=52.5,y1=52.5)
    shape('circle',x0=24.85,x1=43.15,y0=43.35,y1=61.65)
    shape('circle',x0=33.8,x1=34.2,y0=52.3,y1=52.7,fillcolor='#928b93')
    for low in [True,False]:
        shape('rect',x0=13.84,x1=54.16,y0=0 if low else 88.5,y1=16.5 if low else 105)
        shape('rect',x0=24.84,x1=43.16,y0=0 if low else 99.5,y1=5.5 if low else 105)
        shape('rect',x0=30.34,x1=37.66,y0=-1.5 if low else 105,y1=0 if low else 106.5)
        spot=11 if low else 94
        shape('circle',x0=33.8,x1=34.2,y0=spot-.2,y1=spot+.2,fillcolor='#928b93')
        angle=math.asin(5.5/9.15)
        points=[]
        for i in range(41):
            t=angle+(math.pi-2*angle)*i/40
            x=34+9.15*math.cos(t);y=11+9.15*math.sin(t)
            points.append((x,y if low else 105-y))
        shape('path',path='M '+' L '.join(f'{x:.5f},{y:.5f}' for x,y in points))
    for boundary in [33.33,66.6]:
        fig.add_shape(type='line',x0=0,x1=68,y0=boundary*1.05,y1=boundary*1.05,line=dict(color='#c5bfc6',width=1,dash='dash'),layer='below')
    brand='data:image/png;base64,'+base64.b64encode(brand_path.read_bytes()).decode()
    fig.add_layout_image(source=brand,xref='x',yref='y',x=34,y=52.5,sizex=15,sizey=15,opacity=.35,xanchor='center',yanchor='middle',sizing='contain',layer='below')
    for pressing in [False,True]:
        points=e.loc[e._pressing12.eq(pressing)]
        fig.add_trace(go.Scatter(x=(100-points.y)*.68,y=points.x*1.05,mode='markers',
                                 marker=dict(size=9 if pressing else 7,color=base,opacity=.8 if pressing else .4,
                                             line=dict(color=outline,width=2 if pressing else .7)),
                                 text=[f'{p.playerName} · {int(p.timeMin)}′ · {p.typeId}'+(' · Pressing 12' if pressing else '') for _,p in points.iterrows()],
                                 hovertemplate='%{text}<extra></extra>',showlegend=False))
    for bottom,label,share,count in zip([0,33.33,66.6],['Own Third','Middle Third','Final Third'],shares,counts):
        fig.add_annotation(x=34,y=(bottom+1)*1.05,yanchor='bottom',text=f'<b>{label}<br>{share:.1%}</b>',showarrow=False,font=dict(size=20,color='#000000'),
                           bgcolor='rgba(255,255,255,0.85)',borderpad=3,hovertext=f'{int(count)} of {len(e)} Plotted Defensive Actions')
    if badge:fig.add_layout_image(source=badge,xref='x',yref='y',x=2,y=103,sizex=8,sizey=8,xanchor='left',yanchor='top',sizing='contain')
    fig.update_layout(title=dict(text=f'<b>{html.escape(team)} · Defensive Actions</b>',x=.5,font=dict(size=22)),height=740,
                      template='plotly_white',paper_bgcolor='white',plot_bgcolor='white',showlegend=False,
                      font=dict(family='Comic Neue, cursive',color='#24202b'),margin=dict(l=15,r=15,t=65,b=15))
    fig.update_xaxes(range=[-2,70],visible=False,fixedrange=True)
    fig.update_yaxes(range=[-2,108],visible=False,scaleanchor='x',scaleratio=1,fixedrange=True)
    return fig,len(e),int(e._pressing12.sum())
