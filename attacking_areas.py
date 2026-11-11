import base64
import math
import numpy as np
import pandas as pd
import plotly.graph_objects as go


def open_play(events):
    mask=pd.Series(True,index=events.index)
    for flag in ['corner','throwin','freekick']:
        if flag in events:mask &= ~pd.to_numeric(events[flag],errors='coerce').eq(1)
    return mask

def attacking_data(events,team):
    e=events.loc[events.team.eq(team)&events.typeId.eq('Pass')&events.outcome.eq('Successful')&open_play(events)].copy()
    for c in ['x','y','end_x','end_y']:e[c]=pd.to_numeric(e[c],errors='coerce')
    e=e.loc[e[['x','y','end_x','end_y']].notna().all(axis=1)&e[['x','y','end_x','end_y']].ge(0).all(axis=1)&e[['x','y','end_x','end_y']].le(100).all(axis=1)]
    entries=e.loc[e.x.lt(66.6)&e.end_x.gt(66.6)]
    lanes=np.where(entries.end_y<37.5,0,np.where(entries.end_y<62.5,1,2))
    counts=np.bincount(lanes,minlength=3)[::-1]
    shares=counts/counts.sum() if counts.sum() else np.zeros(3)
    return e.loc[e.x.ge(66.6)],counts,shares


def attacking_figure(events,team,base,outline,badge,brand_path):
    passes,counts,shares=attacking_data(events,team)
    fig=go.Figure();line=dict(color='#928b93',width=1)
    def shape(kind,**kw):fig.add_shape(type=kind,line=line,layer='below',**kw)
    shape('rect',x0=0,x1=68,y0=52.5,y1=105,fillcolor='white')
    shape('rect',x0=13.84,x1=54.16,y0=88.5,y1=105)
    shape('rect',x0=24.84,x1=43.16,y0=99.5,y1=105)
    shape('rect',x0=30.34,x1=37.66,y0=105,y1=106.5)
    shape('circle',x0=33.8,x1=34.2,y0=93.8,y1=94.2,fillcolor='#928b93')
    theta=math.asin(5.5/9.15)
    points=[(34+9.15*math.cos(theta+(math.pi-2*theta)*i/40),94-9.15*math.sin(theta+(math.pi-2*theta)*i/40)) for i in range(41)]
    shape('path',path='M '+' L '.join(f'{x:.5f},{y:.5f}' for x,y in points))
    for x in [(100-66.6)*.68,(100-33.33)*.68]:
        fig.add_shape(type='line',x0=x,x1=x,y0=52.5,y1=105,line=dict(color='#c5bfc6',width=1,dash='dash'),layer='below')
    fig.add_shape(type='line',x0=0,x1=68,y0=66.6*1.05,y1=66.6*1.05,line=dict(color='#d3cdd4',width=1,dash='dot'),layer='below')
    fig.add_trace(go.Scatter(x=(100-passes.y)*.68,y=passes.x*1.05,mode='markers',
                             marker=dict(size=6,color=base,opacity=.45,line=dict(color=outline,width=.6)),
                             text=[f'{p.playerName} · {int(p.timeMin)}′' for _,p in passes.iterrows()],
                             hovertemplate='%{text}<br>Successful Pass Location<extra></extra>',showlegend=False))
    shots=events.loc[events.team.eq(team)&events.shot&open_play(events)].copy()
    for field in ['x','y']:shots[field]=pd.to_numeric(shots[field],errors='coerce')
    shots=shots.loc[shots.x.between(50,100)&shots.y.between(0,100)]
    fig.add_trace(go.Scatter(x=(100-shots.y)*.68,y=shots.x*1.05,mode='markers',
                             marker=dict(size=10,color=base,opacity=.55,line=dict(color=outline,width=1.4)),
                             text=[f'{s.playerName} · {int(s.timeMin)}′ · {s.typeId}<br>xG {s.xg:.2f}' for _,s in shots.iterrows()],
                             hovertemplate='%{text}<extra></extra>',showlegend=False))
    # Percentages describe the exact dots displayed: pass starts plus shots.
    shown_y=pd.concat([passes.y,shots.y],ignore_index=True)
    lanes=np.where(shown_y<33.33,0,np.where(shown_y<66.6,1,2))
    counts=np.bincount(lanes,minlength=3)[::-1]
    shares=counts/counts.sum() if counts.sum() else np.zeros(3)
    for x,share,count in zip([(100-83.3)*.68,(100-49.965)*.68,(100-16.665)*.68],shares,counts):
        if count:
            top=62+8+24*share
            shaft=.55+.55*share;head=2.1+1.1*share
            coords=[(x-shaft,62),(x+shaft,62),(x+shaft,top-4),(x+head,top-4),(x,top),(x-head,top-4),(x-shaft,top-4)]
            fig.add_shape(type='path',path='M '+' L '.join(f'{px:.4f},{py:.4f}' for px,py in coords)+' Z',
                          fillcolor=base,line=dict(color=outline,width=1),layer='above')
        fig.add_annotation(x=x,y=59,text=f'<b>{share:.1%}</b>',showarrow=False,font=dict(size=18,color='#000000'),
                           hovertext=f'{int(count)} Plotted Actions (Pass Locations + Shots)')
    brand='data:image/png;base64,'+base64.b64encode(brand_path.read_bytes()).decode()
    fig.add_layout_image(source=brand,xref='x',yref='y',x=34,y=55.8,sizex=11,sizey=6,opacity=.35,xanchor='center',yanchor='middle',sizing='contain')
    if badge:fig.add_layout_image(source=badge,xref='x',yref='y',x=2,y=103,sizex=7,sizey=7,xanchor='left',yanchor='top',sizing='contain')
    fig.update_layout(title=dict(text=f'<b>{team} · Attacking Areas</b>',x=.5,font=dict(size=22)),height=520,
                      paper_bgcolor='white',plot_bgcolor='white',template='plotly_white',showlegend=False,
                      font=dict(family='Comic Sans MS, cursive',color='#24202b'),margin=dict(l=15,r=15,t=65,b=35))
    fig.update_xaxes(range=[-2,70],visible=False,fixedrange=True)
    fig.update_yaxes(range=[51,108],visible=False,scaleanchor='x',scaleratio=1,fixedrange=True)
    return fig,int(attacking_data(events,team)[1].sum()),len(passes)
