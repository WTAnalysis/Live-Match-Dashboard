"""Successful-action control on a fixed home-attacks-right pitch."""
import base64
import numpy as np
import pandas as pd
import plotly.graph_objects as go


def zone_counts(events,home,away):
    required={'x','y','outcome','typeId','team'}
    if not required.issubset(events):
        raise ValueError('Pitch control requires event coordinates, outcomes and teams.')
    e=events.copy()
    valid=e.outcome.eq('Successful') & ~e.typeId.isin(['Player on','Player off','Card']) & e.team.isin([home,away])
    for flag in ['corner','freekick','goalkick','throwin']:
        if flag in e:valid &= ~pd.to_numeric(e[flag],errors='coerce').eq(1)
    x=pd.to_numeric(e.x,errors='coerce');y=pd.to_numeric(e.y,errors='coerce')
    valid &= x.between(0,100)&y.between(0,100)
    e=e.loc[valid].copy();x=x.loc[valid];y=y.loc[valid]
    away_mask=e.team.eq(away)
    x=x.where(~away_mask,100-x);y=y.where(~away_mask,100-y)
    e['col']=np.minimum((x/(100/15)).astype(int),14)
    e['row']=np.minimum((y/10).astype(int),9)
    counts=np.zeros((10,15,2),dtype=int)
    for i,team in enumerate([home,away]):
        selected=e.loc[e.team.eq(team)]
        np.add.at(counts[:,:,i],(selected.row.to_numpy(),selected.col.to_numpy()),1)
    return counts


def control_figure(counts,teams,colours,badges,brand_path):
    fig=go.Figure()
    neutral='#dedede' if any(c.lower()=='#ffffff' for c in colours) else 'white'
    centres=[];hover=[]
    for row in range(10):
        for col in range(15):
            h,a=counts[row,col];total=h+a
            owner=0 if total and h/total>.6 else 1 if total and a/total>.6 else None
            colour=neutral
            if owner is not None:
                code=colours[owner].lstrip('#')
                rgb=tuple(int(code[i:i+2],16) for i in [0,2,4])
                colour=f'rgba({rgb[0]},{rgb[1]},{rgb[2]},0.5)'
            fig.add_shape(type='rect',x0=col*7,x1=(col+1)*7,y0=row*6.8,y1=(row+1)*6.8,
                          line=dict(color='#d3cfd2',width=.6),fillcolor=colour,layer='below')
            centres.append((col*7+3.5,row*6.8+3.4))
            shares=f'{teams[0]}: {h} ({h/total:.1%})<br>{teams[1]}: {a} ({a/total:.1%})' if total else 'No qualifying successful actions'
            hover.append(f'Zone {col+1}, {row+1}<br>{shares}<br>Control: {teams[owner] if owner is not None else "Neither Team"}')
    line=dict(color='#514958',width=1.5)
    def rect(x0,y0,x1,y1):fig.add_shape(type='rect',x0=x0,y0=y0,x1=x1,y1=y1,line=line)
    rect(0,0,105,68)
    fig.add_shape(type='line',x0=52.5,x1=52.5,y0=0,y1=68,line=line)
    fig.add_shape(type='circle',x0=52.5-9.15,x1=52.5+9.15,y0=34-9.15,y1=34+9.15,line=line)
    for left in [True,False]:
        rect(0 if left else 88.5,13.84,16.5 if left else 105,54.16)
        rect(0 if left else 99.5,24.84,5.5 if left else 105,43.16)
        rect(-1.5 if left else 105,30.34,0 if left else 106.5,37.66)
        spot=11 if left else 94
        fig.add_shape(type='circle',x0=spot-.2,x1=spot+.2,y0=33.8,y1=34.2,line=line,fillcolor='#514958')
    fig.add_trace(go.Scatter(x=[p[0] for p in centres],y=[p[1] for p in centres],mode='markers',
                             marker=dict(size=32,color='rgba(0,0,0,0)'),text=hover,
                             hovertemplate='%{text}<extra></extra>',showlegend=False))
    for team,x,anchor in [(teams[0],2,'left'),(teams[1],103,'right')]:
        if badges.get(team):fig.add_layout_image(source=badges[team],xref='x',yref='y',x=x,y=2,
                                                 sizex=8,sizey=8,xanchor=anchor,yanchor='bottom',
                                                 sizing='contain',opacity=.5)
    brand='data:image/png;base64,'+base64.b64encode(brand_path.read_bytes()).decode()
    fig.add_layout_image(source=brand,xref='x',yref='y',x=52.5,y=34,sizex=12,sizey=12,
                         xanchor='center',yanchor='middle',sizing='contain',opacity=.5)
    fig.update_layout(template='plotly_white',title=dict(text='<b>Pitch Control Map</b>',x=.5),height=680,
                      font=dict(family='Comic Sans MS, cursive',color='#24202b'),paper_bgcolor='white',plot_bgcolor='white',
                      margin=dict(l=25,r=25,t=70,b=15),showlegend=False,hoverlabel=dict(bgcolor='white',font_color='#24202b'))
    fig.update_xaxes(range=[-3,108],visible=False,fixedrange=True)
    fig.update_yaxes(range=[-13,71],visible=False,scaleanchor='x',scaleratio=1,fixedrange=True)
    fig.add_annotation(x=52.5,y=-7,xref='x',yref='y',text=f'{teams[0]} →     ← {teams[1]}',showarrow=False)
    return fig
