from typography import embed_svg_font
import base64
import html
import json
import math
import pandas as pd
import plotly.graph_objects as go


def shirt(number,base,outline):
    number='—' if pd.isna(number) else str(number).removesuffix('.0')
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 90"><path d="M30 5 L15 12 L2 31 L20 44 L27 34 L27 85 L73 85 L73 34 L80 44 L98 31 L85 12 L70 5 Q50 22 30 5 Z" fill="{base}" stroke="{outline}" stroke-width="3"/><text x="50" y="59" text-anchor="middle" font-family="Comic Neue,cursive" font-size="30" font-weight="bold" fill="{outline}">{html.escape(number)}</text></svg>'
    return 'data:image/svg+xml;base64,'+base64.b64encode(embed_svg_font(svg).encode()).decode()


def player_icons(events,team,name,star=False):
    if events is None:return ['star'] if star else []
    from data import goal_details
    e=events.loc[events.team.eq(team)&events.playerName.eq(name)]
    flags=lambda key:pd.to_numeric(e[key],errors='coerce').eq(1) if key in e else pd.Series(False,index=e.index)
    cards=e.typeId.eq('Card')
    icons=['off'] if e.typeId.eq('Player off').any() else []
    goals=events.loc[events.playerName.eq(name)&events.scorer.eq(team)&events.typeId.eq('Goal')]
    icons+=['goal']*len(goals)
    own=e.typeId.eq('Own Goal') | (e.typeId.eq('Goal') & (flags('owngoal') | flags('isOwnGoal')))
    icons+=['own_goal']*int(own.sum())
    icons+=['assist']*sum(g['assist']==name and not g['own_goal'] for g in goal_details(events,team))
    icons+=['yellow']*int((cards&(flags('yellowcard')|flags('yellowcard2'))).sum())
    icons+=['red']*int((cards&(flags('redcard')|flags('yellowcard2'))).sum())
    if star:icons.append('star')
    return icons

def icon_source(icons):
    drawings={
      'off':'<path d="M2 10 H16 M11 4 L17 10 L11 16" fill="none" stroke="#d92b36" stroke-width="3"/>',
      'on':'<path d="M18 10 H4 M9 4 L3 10 L9 16" fill="none" stroke="#168c43" stroke-width="3"/>',
      'goal':'<circle cx="10" cy="10" r="8" fill="white" stroke="#24202b"/><path d="M10 5 L15 8 L13 14 H7 L5 8 Z" fill="#24202b"/><path d="M10 2 V5 M18 8 L15 8 M15 17 L13 14 M5 17 L7 14 M2 8 L5 8" stroke="#24202b"/>',
      'own_goal':'<circle cx="10" cy="10" r="8" fill="white" stroke="#d92b36"/><path d="M10 5 L15 8 L13 14 H7 L5 8 Z" fill="#d92b36"/><path d="M10 2 V5 M18 8 L15 8 M15 17 L13 14 M5 17 L7 14 M2 8 L5 8" stroke="#d92b36"/>',
      'assist':'<circle cx="10" cy="10" r="8" fill="white" stroke="#24202b"/><text x="10" y="14" text-anchor="middle" font-size="12" font-family="Comic Neue" font-weight="bold">A</text>',
      'yellow':'<rect x="6" y="1" width="9" height="18" rx="1" fill="#f2cf29" stroke="#514958"/>',
      'red':'<rect x="6" y="1" width="9" height="18" rx="1" fill="#e32e3a" stroke="#514958"/>',
      'star':'<path d="M10 1 L13 7 L20 8 L15 13 L16 20 L10 16 L4 20 L5 13 L0 8 L7 7 Z" fill="#e5b52c" stroke="#8c6500" stroke-width=".7"/>'}
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {22*len(icons)} 22">'+''.join(f'<g transform="translate({22*i},0)">{drawings[k]}</g>' for i,k in enumerate(icons))+'</svg>'
    return 'data:image/svg+xml;base64,'+base64.b64encode(embed_svg_font(svg).encode()).decode()

def lineup_figure(roster,team,base,outline,badge,root,events=None,par_winner=None,ending=False,link_context=None,formation=None,current=False,pre_match=False,competition_logo=None,player_faces=None):
    from player_actions import linked_name
    positions=json.loads((root/'lineup_positions.json').read_text())
    if 'is_starter' in roster and roster.is_starter.notna().any():
        mask=roster.is_starter.astype(str).str.lower().isin(['yes','true','1','1.0'])
    elif 'time_on' in roster:mask=pd.to_numeric(roster.time_on,errors='coerce').eq(0)
    else:mask=pd.Series(False,index=roster.index)
    starters,bench=roster.loc[mask].copy(),roster.loc[~mask]
    starters['_plot_position']=starters.apply(lambda p:p.get('position1') if pd.notna(p.get('position1')) else p.get('position'),axis=1)
    # The source 3-4-1-2 dictionary duplicates RCF in slots 10 and 11.
    right=starters.loc[starters._plot_position.eq('RCF(2)')]
    if len(right)==2 and not starters._plot_position.eq('LCF(2)').any():
        ordered=right.assign(_slot=pd.to_numeric(right.get('formation_position'),errors='coerce')).sort_values('_slot',kind='stable')
        starters.loc[ordered.index[-1],'_plot_position']='LCF(2)'
    generic=starters.loc[starters._plot_position.eq('CF')]
    if len(generic)==2:
        ordered=generic.assign(_slot=pd.to_numeric(generic.get('formation_position'),errors='coerce')).sort_values('_slot',kind='stable')
        starters.loc[ordered.index[0],'_plot_position']='LCF(2)'
        starters.loc[ordered.index[1],'_plot_position']='RCF(2)'
    bench=bench.copy()
    for idx,p in bench.iterrows():
        name=str(p.get('player_name',p.get('playerName','Unknown')))
        incoming=events.loc[events.typeId.eq('Player on')&events.team.eq(team)&events.playerName.eq(name)] if events is not None else pd.DataFrame()
        minutes=pd.to_numeric(p.get('minutes_played'),errors='coerce')
        used=not incoming.empty or (pd.notna(minutes) and minutes>0)
        on=pd.to_numeric(p.get('time_on'),errors='coerce')
        entry=float(incoming.iloc[0].minute) if not incoming.empty else on
        bench.loc[idx,'_unused']=int(not used)
        bench.loc[idx,'_entry']=entry if used and pd.notna(entry) else float('inf')
        bench.loc[idx,'_number']=pd.to_numeric(p.get('squad_number'),errors='coerce')
    if len(bench):bench=bench.sort_values(['_unused','_entry','_number'],kind='stable',na_position='last')
    if ending and len(bench):bench=bench.sort_values(['_exit_order','_number'],kind='stable',na_position='last')
    fig=go.Figure();line=dict(color='#ffffff',width=1)
    def shape(kind,**kw):
        kw.setdefault('layer','below')
        fig.add_shape(type=kind,line=line,**kw)
    shape('rect',x0=0,x1=68,y0=0,y1=105,fillcolor='#c5dfa9',layer='below')
    shape('line',x0=0,x1=68,y0=52.5,y1=52.5)
    shape('circle',x0=24.85,x1=43.15,y0=43.35,y1=61.65)
    for low in [True,False]:
        shape('rect',x0=13.84,x1=54.16,y0=0 if low else 88.5,y1=16.5 if low else 105)
        shape('rect',x0=24.84,x1=43.16,y0=0 if low else 99.5,y1=5.5 if low else 105)
        spot=11 if low else 94
        shape('circle',x0=33.75,x1=34.25,y0=spot-.25,y1=spot+.25,fillcolor=line['color'])
        angle=math.asin(5.5/9.15)
        points=[]
        for step in range(41):
            theta=angle+(math.pi-2*angle)*step/40
            px=34+9.15*math.cos(theta);py=11+9.15*math.sin(theta)
            points.append((px,py if low else 105-py))
        path='M '+' L '.join(f'{px:.4f},{py:.4f}' for px,py in points)
        shape('path',path=path)
    shape('circle',x0=33.75,x1=34.25,y0=52.25,y1=52.75,fillcolor=line['color'])
    brand='data:image/png;base64,'+base64.b64encode((root/'assets/wtatransnew.png').read_bytes()).decode()
    fig.add_layout_image(source=brand,xref='x',yref='y',x=34,y=52.5,sizex=15,sizey=15,opacity=.65,xanchor='center',yanchor='middle')
    missing=[]
    for _,p in starters.iterrows():
        pos=p['_plot_position']
        pos={'AML(2)':'LAM(2)','AMR(2)':'RAM(2)'}.get(pos,pos)
        name=str(p.get('player_name',p.get('playerName','Unknown')))
        if pos not in positions:missing.append(name);continue
        longitudinal,lateral=positions[pos];x=(100-lateral)*.68;y=longitudinal*1.05
        source=(player_faces or {}).get(str(p.get('player_id'))) or shirt(p.get('squad_number'),base,outline)
        fig.add_layout_image(source=source,xref='x',yref='y',x=x,y=y,sizex=10,sizey=10,xanchor='center',yanchor='middle',sizing='contain',layer='above')
        fig.add_annotation(x=x,y=y-4.3,text=f'<b>{linked_name(name,team,link_context)}</b>',showarrow=False,font=dict(size=10),yanchor='top')
        icons=player_icons(events,team,name,par_winner==(team,name))
        if ending and events is not None and (events.team.eq(team)&events.playerName.eq(name)&events.typeId.eq('Player on')).any():icons.insert(0,'on')
        if icons:
            fig.add_layout_image(source=icon_source(icons),xref='x',yref='y',x=x,y=y-9.4,
                                 sizex=3.1*len(icons),sizey=3.1,xanchor='center',yanchor='middle',sizing='contain')
        fig.add_trace(go.Scatter(x=[x],y=[y],mode='markers',marker=dict(size=25,color='rgba(0,0,0,0)'),hovertemplate=f'{html.escape(name)}<br>{pos}<extra></extra>',showlegend=False))
    fig.add_annotation(x=74,y=104,text='<b>Off / Unused</b>' if ending else '<b>Bench</b>',showarrow=False,xanchor='left',font=dict(size=15))
    spacing=min(10,94/max(len(bench),1))
    for i,(_,p) in enumerate(bench.iterrows()):
        y=94-i*spacing;name=str(p.get('player_name',p.get('playerName','Unknown')))
        source=(player_faces or {}).get(str(p.get('player_id'))) or shirt(p.get('squad_number'),base,outline)
        fig.add_layout_image(source=source,xref='x',yref='y',x=76,y=y,sizex=7,sizey=7,xanchor='center',yanchor='middle',sizing='contain')
        minutes=pd.to_numeric(p.get('minutes_played'),errors='coerce');on=pd.to_numeric(p.get('time_on'),errors='coerce')
        appeared=False
        if events is not None:
            incoming=events.loc[events.typeId.eq('Player on')&events.team.eq(team)&events.playerName.eq(name)]
            appeared=not incoming.empty
            if appeared:on=incoming.iloc[0].timeMin
        used=appeared or (pd.notna(minutes) and minutes>0)
        detail='Substitute' if pre_match else f'On {int(on)}′' if used and pd.notna(on) else 'Used' if used else 'Unused' if minutes==0 else 'Status Unavailable'
        if ending:detail=str(p.get('_ending_status',''))
        icons=player_icons(events,team,name,par_winner==(team,name))
        if used and not ending:icons.insert(0,'on')
        if icons:
            strip=base64.b64decode(icon_source(icons).split(',')[1]).decode()
            icon_width=22*len(icons)
            padding=max(30,len(name)*11.6)+10
            total=padding+icon_width
            strip=strip.replace(f'viewBox="0 0 {icon_width} 22"',f'viewBox="0 0 {total} 22"')
            content=f'<text x="0" y="15" font-family="Comic Neue,cursive" font-size="20" font-weight="bold" fill="#24202b"></text><g transform="translate({padding},0)">'
            strip=strip.replace('><g ', '>'+content+'<g ',1).replace('</svg>','</g></svg>')
            source='data:image/svg+xml;base64,'+base64.b64encode(embed_svg_font(strip).encode()).decode()
            fig.add_layout_image(source=source,xref='x',yref='y',x=82,y=y+1.3,
                                 sizex=min(total*.12,27),sizey=2.64,
                                 xanchor='left',yanchor='middle',sizing='contain')
            fig.add_annotation(x=82,y=y+1.3,text=f'<b>{linked_name(name,team,link_context)}</b>',showarrow=False,xanchor='left',font=dict(size=10))
            fig.add_annotation(x=82,y=y-1.8,text=detail,showarrow=False,xanchor='left',font=dict(size=9))
        else:
            fig.add_annotation(x=82,y=y,text=f'<b>{linked_name(name,team,link_context)}</b><br>{detail}',showarrow=False,xanchor='left',align='left',font=dict(size=10))
    if badge:fig.add_layout_image(source=badge,xref='x',yref='y',x=0,y=114,sizex=12,sizey=12,xanchor='left',yanchor='middle',sizing='contain')
    header_logo=competition_logo
    if header_logo:fig.add_layout_image(source=header_logo,xref='x',yref='y',x=110,y=114,sizex=13,sizey=12,xanchor='right',yanchor='middle',sizing='contain')
    lineup_label=('Current Lineup' if current else 'Ending Lineup') if ending else 'Starting Lineup'
    heading=f'{team} - {lineup_label}'+(f' - {formation}' if formation else '')
    fig.add_annotation(x=53,y=114,text=f'<b>{html.escape(heading)}</b>',showarrow=False,font=dict(size=14 if len(heading)<=49 else 12),xanchor='center',yanchor='middle')
    fig.update_layout(width=578,height=650,showlegend=False,template='plotly_white',paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=8,r=8,t=12,b=12),font=dict(family='Comic Neue, cursive',color='#24202b'))
    fig.update_xaxes(range=[-2,112],visible=False,fixedrange=True,constrain='domain')
    fig.update_yaxes(range=[-5,122],visible=False,scaleanchor='x',scaleratio=1,fixedrange=True)
    return fig,missing,len(starters)
