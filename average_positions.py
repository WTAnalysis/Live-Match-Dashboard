"""Starter event-location averages, following the Club World Cup dashboard."""
import base64
import html
import pandas as pd
import plotly.graph_objects as go


def average_positions(events,roster,teams,minute_range):
    e=events.copy()
    valid=~e.typeId.astype(str).str.lower().isin(['player on','player off'])
    minute=pd.to_numeric(e['minute'],errors='coerce')
    for axis in ['x','y']:e[axis]=pd.to_numeric(e[axis],errors='coerce')
    e=e.loc[valid & minute.between(*minute_range) & e.x.between(0,100) & e.y.between(0,100)]
    starters=roster.loc[roster.is_starter.astype(str).str.lower().isin(['yes','true','1','1.0'])].copy()
    rows=[]
    for team in teams:
        squad=starters.loc[starters.team_name.eq(team)]
        locations=e.loc[e.team.eq(team)].groupby('playerName').agg(x=('x','mean'),y=('y','mean'),actions=('x','size'))
        result=squad.merge(locations,left_on='player_name',right_index=True,how='inner')
        result['team']=team
        if team==teams[1]:result[['x','y']]=100-result[['x','y']]
        rows.append(result)
    return pd.concat(rows,ignore_index=True) if rows else pd.DataFrame()


def average_figure(positions,teams,colours,outlines,badges,brand_path,minute_range):
    fig=go.Figure();line=dict(color='#827985',width=1.2)
    def shape(kind,**kw):fig.add_shape(type=kind,line=line,layer='below',**kw)
    def rect(x0,y0,x1,y1):shape('rect',x0=x0,y0=y0,x1=x1,y1=y1)
    rect(0,0,105,68)
    shape('line',x0=52.5,x1=52.5,y0=0,y1=68)
    shape('circle',x0=43.35,x1=61.65,y0=24.85,y1=43.15)
    for left in [True,False]:
        rect(0 if left else 88.5,13.84,16.5 if left else 105,54.16)
        rect(0 if left else 99.5,24.84,5.5 if left else 105,43.16)
        rect(-1.5 if left else 105,30.34,0 if left else 106.5,37.66)
        x=11 if left else 94
        shape('circle',x0=x-.18,x1=x+.18,y0=33.82,y1=34.18,fillcolor=line['color'])
    for i,team in enumerate(teams):
        p=positions.loc[positions.team.eq(team)]
        numbers=p.squad_number.map(lambda n:str(n).strip().removesuffix('.0') if pd.notna(n) else '—')
        fig.add_trace(go.Scatter(x=p.x*1.05,y=p.y*.68,mode='markers+text',
            text=['<b>'+html.escape(n)+'</b>' for n in numbers],textposition='middle center',
            textfont=dict(color=outlines[i],size=12),
            marker=dict(size=31,color=colours[i],line=dict(color=outlines[i],width=1.5)),
            customdata=list(zip(p.player_name,p.actions,p.x,p.y)),name=team,
            hovertemplate=team+'<br>%{customdata[0]}<br>%{customdata[1]} events<br>Average location: %{customdata[2]:.1f}, %{customdata[3]:.1f}<extra></extra>'))
        if badges.get(team):fig.add_layout_image(source=badges[team],xref='x',yref='y',x=2 if i==0 else 103,y=2,
            sizex=8,sizey=8,xanchor='left' if i==0 else 'right',yanchor='bottom',sizing='contain',opacity=.5,layer='below')
    brand='data:image/png;base64,'+base64.b64encode(brand_path.read_bytes()).decode()
    fig.add_layout_image(source=brand,xref='x',yref='y',x=52.5,y=34,sizex=12,sizey=12,
        xanchor='center',yanchor='middle',sizing='contain',opacity=.5,layer='below')
    title=f'{teams[0]} v {teams[1]} · Average Positions · {minute_range[0]}′–{minute_range[1]}′'
    fig.update_layout(template='plotly_white',title=dict(text='<b>'+html.escape(title)+'</b>',x=.5,font=dict(size=21)),
        height=680,paper_bgcolor='white',plot_bgcolor='white',showlegend=False,
        font=dict(family='Comic Neue, cursive',color='#24202b'),margin=dict(l=25,r=25,t=70,b=15),
        hoverlabel=dict(bgcolor='white',font_color='#24202b'))
    fig.update_xaxes(range=[-3,108],visible=False,fixedrange=True)
    fig.update_yaxes(range=[-13,71],visible=False,scaleanchor='x',scaleratio=1,fixedrange=True)
    fig.add_annotation(x=52.5,y=-7,text=html.escape(f'{teams[0]} →     ← {teams[1]}'),showarrow=False)
    return fig
