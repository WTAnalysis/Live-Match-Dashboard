from typography import configure_fonts, page_font_css, embed_svg_font
configure_fonts()
from player_faces import show_face_lineup
from pathlib import Path
import base64
import html
import io
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image
import streamlit as st
from data import leagues,signature,catalogue,load_match,prepare,simulate_shots,player_log_path,top_players,match_players,event_leaders
from league_lookup import league_label
from team_badges import badge_sources
from match_story import box_entries,block_story,entries_figure,add_substitutions

plt.rcParams['font.family'] = ['Comic Neue', 'DejaVu Sans']
ROOT=Path(__file__).parent
st.set_page_config(page_title='Live Match Dashboard · WT Analysis',page_icon='⚽',layout='wide')
st.html(page_font_css())
st.markdown('''<style>.stApp,.stApp p,.stApp label,.stApp input,.stApp button,.stApp h1,.stApp h2,.stApp h3,.stApp table,.stApp [data-baseweb="select"]{font-family:"Comic Neue",cursive!important}
.stApp{background:#faf7f8;color:#24202b;color-scheme:light}
.stApp h1,.stApp h2,.stApp h3,.stApp p,.stApp label,.stApp [data-testid="stMetricValue"],.stApp [data-testid="stMetricLabel"],.stApp [data-testid="stMarkdownContainer"]{color:#24202b}
.stApp [data-testid="stCaptionContainer"] p{color:#615a67}
header[data-testid="stHeader"]{background:#faf7f8}
.stApp [data-baseweb="select"]>div,.stApp input,.stApp button,.stApp [data-testid="stExpander"] summary{background:#fff;color:#24202b}
 .block-container{max-width:1600px;padding-top:4.5rem} h1,h2,h3{letter-spacing:-.03em} .scoreboard{display:flex;align-items:flex-start;justify-content:center;gap:38px;padding:20px 24px 28px;background:#fff;border:1px solid #e4dce1;border-radius:18px;margin:10px 0 12px;color:#24202b}.team{color:#24202b;text-align:center;width:260px;font-size:24px;font-weight:750}.team-identity{height:156px;display:flex;flex-direction:column;align-items:center;justify-content:flex-start}.team-name{height:54px;display:flex;align-items:center;justify-content:center;line-height:1.15}.scoreboard .score{margin-top:24px}.team img{height:90px;max-width:110px;object-fit:contain;display:block;margin:0 auto 12px}.score{color:#17131d!important;font-size:clamp(48px,6vw,82px);font-weight:850;line-height:1.1;white-space:nowrap;background:#f4eff2;border-radius:14px;padding:18px 28px}.eyebrow{text-align:center;color:#777;font-size:12px;letter-spacing:2px} div[data-testid="stMetric"]{background:white;border:1px solid #ece5e8;border-radius:14px;padding:16px}</style>''',unsafe_allow_html=True)
header_logo='data:image/png;base64,'+base64.b64encode((ROOT/'assets/wtatransnew.png').read_bytes()).decode()
st.markdown(f'''<div style="display:flex;align-items:center;gap:28px;padding:12px 0 20px;overflow:visible">
<img src="{header_logo}" alt="WT Analysis" style="display:block;width:110px;height:auto;max-width:none;object-fit:contain;flex-shrink:0">
<div><h1 style="margin:0;padding:0 0 8px;line-height:1.25">Live Match Dashboard</h1>
<div style="font-size:14px;color:#615a67">Live match events, chances and lineups · Refresh when you want the latest snapshot.</div></div></div>''',unsafe_allow_html=True)
st.caption('Private hosted dashboard · Refresh Live Data fetches a new snapshot. Cached data can disappear when the server restarts.')
from live_data import (SOURCE,STORE,EXAMPLE_OPTA,EXAMPLE_FOTMOB,available_leagues,scoresway_schedule,
                       fotmob_file,fotmob_schedule,paired_index,selectable_fixtures,load_snapshot,refresh_snapshot,FeedError)
if st.sidebar.button('Refresh Schedule Lists'):
    scoresway_schedule.clear();fotmob_schedule.clear()
with st.sidebar.expander('Test hosted feed connections'):
    opta_test = st.text_input('Opta match ID', EXAMPLE_OPTA)
    fotmob_test = st.text_input('FotMob match ID', EXAMPLE_FOTMOB)
    if st.button('Test both feeds'):
        from live_data import get_opta, get_fotmob
        for provider, fetch, mid in [('Scoresway / Opta', get_opta, opta_test), ('FotMob', get_fotmob, fotmob_test)]:
            try:
                with st.spinner('Testing ' + provider):
                    fetch(mid)
                st.success(provider + ': valid match JSON received.')
            except Exception as error:
                st.error(provider + ': ' + str(error))
codes=available_leagues()
if not codes:st.error('No Scoresway schedule files found.');st.stop()
requested_code=st.query_params.get('league','UCL_2627')
code=st.selectbox('League / Season',codes,index=codes.index(requested_code) if requested_code in codes else 0,format_func=league_label)
schedule_path=SOURCE/'Scoresway Schedules'/(code+'.csv')
matches=selectable_fixtures(scoresway_schedule(code,schedule_path.stat().st_mtime_ns))
if not matches:st.info('No fixtures dated today or earlier in this schedule.');st.stop()
default_mid=st.query_params.get('match',EXAMPLE_OPTA)
match_index=next((i for i,m in enumerate(matches) if m['id']==default_mid),0)
match=st.selectbox('Match Details',matches,index=match_index,
                   format_func=lambda m:f"{m['date']} · {m['home']} v {m['away']} · {m['id']}",key='opta_fixture_'+code)
from league_lookup import league_has_xg
competition_has_xg=league_has_xg(code)
fotcode=code
fid='opta-only'
if competition_has_xg:
    fotcode=code
    fp=fotmob_file(fotcode)
    fmatches=selectable_fixtures(fotmob_schedule(str(fp),fp.stat().st_mtime_ns)) if fp else []
    if not fmatches:st.info('No FotMob fixtures dated today or earlier in this league’s schedule.');st.stop()
    fm_index=paired_index(match,fmatches)
    if fm_index is None:st.info('No matching FotMob fixture was found for these teams and date in this league’s schedule.');st.stop()
    pair_key='fot_fixture_'+code
    pair_selection=(code,match['id'])
    if st.session_state.get('live_pair_selection')!=pair_selection:
        st.session_state[pair_key]=fmatches[fm_index]
        st.session_state['live_pair_selection']=pair_selection
    fm=st.selectbox('xG Details',fmatches,
                    format_func=lambda m:f"{m['date']} · {m['home']} v {m['away']} · {m['id']}",
                    key=pair_key)
    fid=fm['id']
else:
    st.caption('Opta-only competition · xG Details are not required.')
refresh=st.button('Refresh Live Data',type='primary',help='Fetch the latest available match data and rebuild the visuals.')
key=(code,match['id'],fid)
memory=st.session_state.setdefault('live_bundles',{})
bundle=memory.get(key) or load_snapshot(*key)
if not competition_has_xg and bundle is not None:
    from live_data import NO_XG_MODEL_VERSION
    if bundle['metadata'].get('no_xg_model_version')!=NO_XG_MODEL_VERSION:
        bundle=load_snapshot(*key)
        memory[key]=bundle
if refresh or bundle is None:
    try:
        with st.spinner('Fetching Opta and FotMob, then processing the live snapshot…' if competition_has_xg else 'Fetching Opta and processing the live snapshot…'):
            bundle=refresh_snapshot(*key)
        memory[key]=bundle
    except Exception as error:
        if bundle is None:st.error(f'Unable to fetch this match: {error}');st.stop()
        st.warning(f'Refresh failed. Keeping the last successful snapshot: {error}')
meta=bundle['metadata']
from zoneinfo import ZoneInfo
fetched=pd.to_datetime(meta['fetched_at'],utc=True).tz_convert(ZoneInfo('Europe/London'))
match_finished=bool(meta['finished'])
status_label='Full Time' if match_finished else meta['status']
latest=bundle['raw'].loc[pd.to_numeric(bundle['raw'].get('periodId'),errors='coerce').isin([1,2,3,4])]
clock=int(pd.to_numeric(latest.timeMin,errors='coerce').max()) if len(latest) else 0
st.caption(f"{status_label} · Latest Recorded Minute: {clock}′ · Last Successful Fetch: {fetched:%d %b %Y %H:%M:%S %Z}")
for note in meta.get('notes',[]):st.info(note)
home,away=meta['home'],meta['away']
match={**match,'home':home,'away':away,'date':meta['date'],'file':str(bundle['folder']/'events.pkl'),'log':None}
pre_match=bundle['events'].empty
if pre_match and bundle['players'].empty:
    st.info('Lineups have not been published yet. Use Refresh Live Data to check again.');st.stop()
stamp=(str(bundle['folder']),)
from player_actions import query_colour
with st.expander('Team Colours',expanded=False):
    cols=st.columns(4)
    hc=cols[0].color_picker(home+' · base',query_colour(st.query_params.get('hc','#df343e'),'#df343e'),key=home+'base')
    ho=cols[1].color_picker(home+' · outline',query_colour(st.query_params.get('ho','#7b1020'),'#7b1020'),key=home+'outline')
    ac=cols[2].color_picker(away+' · base',query_colour(st.query_params.get('ac','#70b9e4'),'#70b9e4'),key=away+'base')
    ao=cols[3].color_picker(away+' · outline',query_colour(st.query_params.get('ao','#12385a'),'#12385a'),key=away+'outline')
from league_lookup import league_logo
from team_badges import embedded_badge
competition_logo=None
competition_url=league_logo(code)
if competition_url:
    try:competition_logo=embedded_badge(competition_url)
    except Exception:st.caption('Competition logo could not be loaded. Refresh to retry.')
if pre_match:
    from lineups import lineup_figure
    from ending_lineups import formation_labels
    roster=bundle['players']
    ids={team:str(group.contestant_id.iloc[0]) for team,group in roster.groupby('team_name')}
    badges,failures=badge_sources([home,away],ids)
    if failures:st.warning('Could not embed these badges for PNG export: '+', '.join(failures))
    original=STORE/'Match Data'/code/(match['id']+'.csv')
    formations=formation_labels(code,match['id'],original.stat().st_mtime_ns if original.exists() else 0)
    st.subheader('Starting Lineups')
    for column,team,base,outline in zip(st.columns(2),[home,away],[hc,ac],[ho,ao]):
        with column:
            selected=roster.loc[roster.team_name.eq(team)]
            if selected.empty:st.info('Lineup not announced for '+team);continue
            formation=formations.get(ids.get(team),{}).get('start')
            fig,missing,total=lineup_figure(selected,team,base,outline,badges.get(team),ROOT,formation=formation,pre_match=True,competition_logo=competition_logo)
            st.plotly_chart(fig,width='content',theme=None)
            show_face_lineup(selected,team,base,outline,badges.get(team),ROOT,formation=formation,pre_match=True,competition_logo=competition_logo)
            if total!=11:st.caption(f'{total} announced starters identified.')
            if missing:st.caption('Positions unavailable: '+', '.join(missing))
    st.caption('Announced teams before kickoff. Use Refresh Live Data for lineup changes and live match events once play begins.')
    st.stop()
try:
    raw=bundle['events']
    d=prepare(raw,home,away)
except Exception as error:st.error(f'Unable to prepare the live match: {error}');st.stop()
teams=[home,away];colours=[hc,ac];outlines=[ho,ao]
player_path=None
roster=bundle['players'].copy()
team_ids={}
if {'team_name','contestant_id'}.issubset(roster.columns):
    for source_team,group in roster.dropna(subset=['contestant_id']).groupby('team_name'):
        mapped=d.loc[d.team_name.eq(source_team),'team']
        target=mapped.iloc[0] if len(mapped) else source_team if source_team in teams else None
        if target:
            ids=group.contestant_id.astype(str).unique()
            if len(ids)==1:team_ids[target]=ids[0]
badges,badge_export_failures=badge_sources(teams,team_ids)
if badge_export_failures:
    st.warning('Could not embed these badges for PNG export: '+', '.join(badge_export_failures)+'. Refresh match data to retry.')
from player_actions import linked_name, match_rankings, overview_image
from match_par import match_par_inputs

roster, performance_metric, par_actions = match_par_inputs(d, roster, SOURCE, code, match['id'])
performance_rankings = match_rankings(roster, performance_metric)
player_link_context=dict(league=code,match=match['id'],fotmob=fid,fotleague=fotcode,hc=hc,ho=ho,ac=ac,ao=ao)
if st.query_params.get('view')=='player':
    if st.button('← Back to Live Match Dashboard'):
        for key in ['view','player','team']:st.query_params.pop(key,None)
        st.rerun()
    selected_team=st.query_params.get('team',home)
    selected_player=st.query_params.get('player','')
    if selected_team not in teams:
        st.error('This team is not part of the selected fixture.');st.stop()
    st.caption(f"{match['date']} · {home} v {away}")
    opponent = away if selected_team == home else home
    image, event_count, missing_shots = overview_image(
        d, selected_player, selected_team, opponent, badges.get(selected_team),
        ROOT/'assets/wtatransnew.png', roster, performance_rankings,
    )
    st.image(image, width='stretch')
    st.download_button('Download player overview', image, selected_player+'-player-overview.png', 'image/png')
    if missing_shots:
        st.caption('Goalkeeper shot placement is unavailable for this match.')
    if not event_count:st.info('No recorded on-ball events for this player in this match.')
    player_events=d.loc[d.team.eq(selected_team)&d.playerName.eq(selected_player)]
    from player_detail import detail_maps, performance_figure

    team_colours = dict(zip(teams, colours))
    team_outline = outlines[teams.index(selected_team)]
    for by_teammate in (False, True):
        if by_teammate:
            st.subheader('Pass Connections by Teammate')
        maps, outgoing, incoming, made_position, received_position, is_keeper = detail_maps(
            d, roster, selected_player, selected_team, team_colours[selected_team], team_outline,
            by_teammate=by_teammate,
        )
        st.image(maps, width='stretch')
        pass_key, receive_key, shot_key = st.columns(3)
        with pass_key:
            st.caption('Larger circles and thicker lines indicate more completed passes.')
            if by_teammate:
                st.caption('Selected-player markers and coordinates show the average pass origin for each recipient.')
            else:
                st.caption(f'Average origin of all passes (Opta) · {made_position}')
            if outgoing:
                st.text("\n".join(outgoing))
        with receive_key:
            st.caption('Each link runs from the teammate’s average pass origin to the selected player’s average reception.')
            if by_teammate:
                st.caption('Selected-player markers and coordinates show the average reception for each passer.')
            else:
                st.caption(f'Average reception (Opta) · {received_position}')
            if incoming:
                st.text("\n".join(incoming))
        with shot_key:
            if is_keeper:
                st.caption('Keeper actions are green for successful and red for unsuccessful. On the goal, green circles show saves and red stars show goals conceded.')
            else:
                st.caption('Marker sizes use xG on the pitch and xG on target on the goal. Filled stars show goals on the goalmouth.')

    timeline = performance_figure(d, performance_rankings, performance_metric, selected_player, selected_team, team_colours, dict(zip(teams, outlines)), par_actions)
    if timeline is not None:
        st.plotly_chart(
            timeline, width='stretch',
            config={"toImageButtonOptions": {
                "format": "png", "filename": selected_player + "-ongoing-match-ranking",
                "width": 1600, "height": 540, "scale": 2,
            }},
        )
        st.caption(
            ('Match PAR uses the recorded match actions. ' if performance_metric == 'Match PAR'
             else 'Published PAR sets the final score. Earlier PAR values are estimated from match actions. ') +
            'Players enter the rankings when they come on. Their score stays fixed after they go off, but their rank can change. '
            'The latest rank matches the pitch visual.'
        )
    else:
        st.info(f'No {performance_metric} ranking is available for this player.')
    with st.expander('Event Details'):
        columns=[c for c in ['timeMin','timeSec','typeId','outcome','x','y','end_x','end_y','expectedGoals','expectedGoalsOnTarget','xT_value'] if c in player_events]
        contributions = par_actions.get((selected_team, selected_player))
        tables = [("Player Events", player_events)]
        if is_keeper:
            assigned = d.get("playing_GK", pd.Series(pd.NA, index=d.index))
            faced = d.loc[d.team.ne(selected_team) & assigned.eq(selected_player)]
            tables.append(("Events Faced as Goalkeeper", faced))

        for heading, rows in tables:
            if is_keeper:
                st.markdown(f"**{heading}**")
            if rows.empty:
                st.caption("No events recorded.")
                continue
            event_details = rows[columns].copy()
            event_details.insert(2, "Event player", rows.playerName)
            if contributions is not None:
                event_details["Match PAR contribution"] = contributions.reindex(rows.index)
            st.dataframe(event_details, hide_index=True, width='stretch',
                         column_config={"Match PAR contribution": st.column_config.NumberColumn(format="%.5f")})
    st.stop()

goals=[int(d.scorer.eq(t).sum()) for t in teams]

score_source='Live Opta Feed'
if all(k in meta['score'] for k in ['home','away']):goals=[int(meta['score']['home']),int(meta['score']['away'])]
def badge(t):
    return f'<img src="{html.escape(badges[t],quote=True)}" alt="{html.escape(t)} badge">' if t in badges else '<div style="font-size:60px">⚽</div>'
from data import goal_details
def scorers_html(team):
    lines=[]
    for goal in goal_details(d,team):
        text=f'{goal["minute"]}′ {html.escape(str(goal["scorer"]))}'
        if goal['own_goal']:text+=' (OG)'
        elif goal['assist']:text+=f' (assisted by {html.escape(str(goal["assist"]))})'
        lines.append(f'<div>{text}</div>')
    return '<div style="font-size:13px;font-weight:400;line-height:1.7;margin-top:8px">'+''.join(lines)+'</div>' if lines else ''
st.markdown(f'<div class="eyebrow">{html.escape(league_label(code))} · {html.escape(match["date"])}</div><div class="scoreboard"><div class="team"><div class="team-identity">{badge(home)}<div class="team-name">{html.escape(home)}</div></div>{scorers_html(home)}</div><div class="score">{goals[0]} – {goals[1]}</div><div class="team"><div class="team-identity">{badge(away)}<div class="team-name">{html.escape(away)}</div></div>{scorers_html(away)}</div></div>',unsafe_allow_html=True)
st.caption(f'Score: {score_source}. Regulation and extra time included where present; penalty shootouts excluded from event charts.')
from lineups import lineup_figure
original_match=STORE/'Match Data'/code/(match['id']+'.csv')
from ending_lineups import formation_labels
match_formations=formation_labels(code,match['id'],original_match.stat().st_mtime_ns if original_match.exists() else 0)
def lineup_formation(selected,team,phase):
    ids=selected.contestant_id.dropna().astype(str).unique() if 'contestant_id' in selected else []
    for key in [*ids,*selected.team_name.dropna().unique(),team]:
        if key in match_formations:return match_formations[key].get(phase)
    return None
st.subheader('Starting Lineups')
par_winner=None
if performance_metric in roster:
    ranked=roster.assign(_par=pd.to_numeric(roster[performance_metric],errors='coerce')).dropna(subset=['_par']).sort_values('_par',ascending=False,kind='stable')
    if len(ranked):
        best=ranked.iloc[0]
        mapped=d.loc[d.team_name.eq(best.team_name),'team']
        par_winner=(mapped.iloc[0] if len(mapped) else best.team_name,str(best.get('player_name',best.get('playerName','Unknown'))))
lineup_columns=st.columns(2)
for column,team in zip(lineup_columns,teams):
    with column:
        source_names=set(d.loc[d.team.eq(team),'team_name'])|{team}
        selected=roster.loc[roster.team_name.isin(source_names)] if 'team_name' in roster else pd.DataFrame()
        if selected.empty:st.info('Lineup data unavailable for '+team)
        else:
            lineup_chart,missing,total=lineup_figure(selected,team,colours[teams.index(team)],outlines[teams.index(team)],badges.get(team),ROOT,d,par_winner,link_context=player_link_context,formation=lineup_formation(selected,team,'start'),competition_logo=competition_logo)
            st.plotly_chart(lineup_chart,width='content',theme=None)
            show_face_lineup(selected,team,colours[teams.index(team)],outlines[teams.index(team)],badges.get(team),ROOT,d,par_winner,link_context=player_link_context,formation=lineup_formation(selected,team,'start'),competition_logo=competition_logo)
            if total!=11:st.caption(f'{total} starters identified in the player log.')
            if missing:st.caption('Positions unavailable: '+', '.join(missing))
st.caption('Starting positions follow Player Data Dashboard’s Position Share map. Bench squads are recovered from the original match lineup where available; names are matched by player ID to season logs. Players with no available name are identified by squad number. Player on events determine whether substitutes appeared, including appearances rounded to zero minutes.')
from ending_lineups import ending_roster
st.subheader('Ending Lineups' if match_finished else 'Current Lineups')
if not roster.empty:
    final_roster,final_notes=ending_roster(roster,d,code,match['id'],original_match.stat().st_mtime_ns if original_match.exists() else 0)
    ending_columns=st.columns(2)
    for column,team in zip(ending_columns,teams):
        with column:
            source_names=set(d.loc[d.team.eq(team),'team_name'])|{team}
            selected=final_roster.loc[final_roster.team_name.isin(source_names)]
            if len(selected):
                ending_chart,missing,total=lineup_figure(selected,team,colours[teams.index(team)],outlines[teams.index(team)],badges.get(team),ROOT,d,par_winner,ending=True,link_context=player_link_context,formation=lineup_formation(selected,team,'end'),current=not match_finished,competition_logo=competition_logo)
                st.plotly_chart(ending_chart,width='content',theme=None)
                show_face_lineup(selected,team,colours[teams.index(team)],outlines[teams.index(team)],badges.get(team),ROOT,d,par_winner,ending=True,link_context=player_link_context,formation=lineup_formation(selected,team,'end'),current=not match_finished,competition_logo=competition_logo)
                if missing:st.caption('Final positions unavailable: '+', '.join(missing))
            else:st.info('Ending lineup unavailable for '+team)
    for note in final_notes:st.caption(note)
    st.caption('Players on the pitch at the latest recorded event, using formation snapshots and substitutions. Substituted-off and dismissed players appear on the right. Match event icons are retained.')
else:st.info('Player-log data is required for ending lineups.')
shots=d.loc[d.shot].copy()
xgs=[float(d.loc[d.team.eq(t),'xg'].sum()) for t in teams]
xgots=[float(d.loc[d.team.eq(t),'xgot'].sum()) for t in teams]
has_xg=d.expectedGoals.notna().any()
from data import xgot_status
has_xgot,missing_xgot=xgot_status(d,teams)
has_poss=d.possession_chain_time.fillna(0).gt(0).any()
metrics=st.columns(4)
metrics[0].metric('xG · Home / Away' if has_xg else 'xThreat · Home / Away',f'{xgs[0]:.2f} / {xgs[1]:.2f}' if has_xg else f'{d.xt0.iloc[-1]:.2f} / {d.xt1.iloc[-1]:.2f}')
metrics[1].metric('xGOT · Home / Away',f'{xgots[0]:.2f} / {xgots[1]:.2f}' if has_xgot else 'Unavailable')
metrics[2].metric('Shots · Home / Away',f'{sum(shots.team.eq(home))} / {sum(shots.team.eq(away))}')
metrics[3].metric('True Possession · Home / Away',f'{d.share0.iloc[-1]:.1f}% / {d.share1.iloc[-1]:.1f}%' if has_poss else 'Unavailable')
if missing_xgot.any():
    st.warning(f'{int(missing_xgot.sum())} unblocked on-target shot(s) have no recorded xGOT. xGOT totals include recorded values only; where shown, probability estimates use zero xGOT for those missing shots and may be understated.')

def layout(fig,title,height=360):
    fig.update_layout(template='plotly_white',title=dict(text=title,font=dict(color='#24202b',size=19)),showlegend=False,height=height,paper_bgcolor='white',plot_bgcolor='white',font=dict(family='Comic Neue, cursive',color='#24202b'),margin=dict(l=45,r=25,t=60,b=45),legend=dict(orientation='h',y=-.2),hovermode='x unified')
    fig.update_xaxes(showgrid=False,zeroline=False,tickfont=dict(color='#514958'),title_font=dict(color='#514958'))
    fig.update_yaxes(gridcolor='#eee9ed',zeroline=False,tickfont=dict(color='#514958'),title_font=dict(color='#514958'))
    fig.update_traces(textfont=dict(color='#24202b'),selector=dict(type='scatter'))
    fig.update_layout(hoverlabel=dict(bgcolor='white',font_color='#24202b',font_family='Comic Neue, cursive'))
    return fig

def timeline(kind):
    fig=go.Figure()
    for i,t in enumerate(teams):
        values=d[f'{kind}{i}' if kind in ['xg','xt'] else f'share{i}']
        x=np.r_[0,d.minute];y=np.r_[0 if kind in ['xg','xt'] else 50,values]
        for colour,width,show in [(outlines[i],5,False),(colours[i],2.8,True)]:
            fig.add_trace(go.Scatter(x=x,y=y,mode='lines',name=t,line=dict(color=colour,width=width,shape='hv' if kind in ['xg','xt'] else 'linear'),showlegend=show,hoverinfo='skip' if not show else None))
        g=d.loc[d.scorer.eq(t)]
        fig.add_trace(go.Scatter(x=g.minute,y=values.loc[g.index],mode='markers',name=t+' goal',marker=dict(symbol='star',size=16,color=colours[i],line=dict(color=outlines[i],width=2)),text=g.playerName,hovertemplate='%{text} · goal<extra></extra>',showlegend=False))
    for p in sorted(d.periodId.unique())[1:]:
        fig.add_vline(x=d.loc[d.periodId.eq(p),'minute'].min(),line_dash='dot',line_color='#aaa')
    layout(fig,'<b>xG Story</b>' if kind=='xg' else '<b>xThreat Story</b>' if kind=='xt' else '<b>True Possession</b>')
    fig.update_layout(title_x=.5,title_xanchor='center',title_font_size=22,title_y=.935,title_yanchor='middle')
    for index,team in enumerate(teams):
        if badges.get(team):
            fig.add_layout_image(source=badges[team],xref='paper',yref='paper',x=index*.09,y=1.14,
                                 sizex=.075,sizey=.14,xanchor='left',yanchor='middle',sizing='contain')
    brand_uri='data:image/png;base64,'+base64.b64encode((ROOT/'assets/wtatransnew.png').read_bytes()).decode()
    fig.add_layout_image(source=brand_uri,xref='paper',yref='paper',x=1,y=1.14,
                         sizex=.10,sizey=.14,xanchor='right',yanchor='middle',sizing='contain')
    fig.update_xaxes(title='Minutes',range=[0,max(90,d.minute.max()+1)])
    fig.update_yaxes(title='Total Expected Goals' if kind=='xg' else 'Total xThreat' if kind=='xt' else 'True Possession Share',range=None if kind in ['xg','xt'] else [0,100])
    if kind=='poss':fig.add_hline(y=50,line_dash='dot',line_color='#bbb')
    return add_substitutions(fig,d,teams,kind)

left,right=st.columns(2)
with left:
    if has_xg:
        st.plotly_chart(timeline('xg'),width='stretch',theme=None)
        st.plotly_chart(block_story(d,teams,colours,outlines,'xg',badges,ROOT/'assets/wtatransnew.png'),width='stretch',theme=None)
    elif 'xT_value' in d and pd.to_numeric(d.xT_value,errors='coerce').notna().any():
        st.plotly_chart(timeline('xt'),width='stretch',theme=None)
        st.plotly_chart(block_story(d,teams,colours,outlines,'xt',badges,ROOT/'assets/wtatransnew.png'),width='stretch',theme=None)
    else:st.info('Neither xG nor xThreat data is available for this match.')
with right:
    if has_poss:
        st.plotly_chart(timeline('poss'),width='stretch',theme=None)
        st.plotly_chart(block_story(d,teams,colours,outlines,'poss',badges,ROOT/'assets/wtatransnew.png'),width='stretch',theme=None)
    else:st.info('True possession requires recorded possession_chain_time values.')
st.caption('15-minute bars show values within each block, with home then away. Stoppage time stays in the final block of its half. Possession shares use recorded possession-chain durations assigned to events within each block; blocks without recorded possession time are left blank.')
st.caption('Stars mark goals. True possession uses cumulative possession_chain_time, matching your notebook. Period boundaries include first-half stoppage time before the second half begins.')
st.caption('Circular Red/Green Arrows Mark Substitutions on Each Team’s Line · Yellow/Red Squares Mark Cards · Hover for Details')

if has_xg and has_xgot:
    rates=[.7*x+.3*y for x,y in zip(xgs,xgots)]
    simulation_count=100000
    chances=[tuple((.7*shots.loc[shots.team.eq(t),'xg']+.3*shots.loc[shots.team.eq(t),'xgot']).clip(0,1)) for t in teams]
    grid,wins,likely=simulate_shots(*chances,simulation_count)
    st.markdown(f'### Expected Result · Most Likely Scoreline: **{html.escape(home)} {likely[0]} – {likely[1]} {html.escape(away)}**')
    fig=go.Figure(go.Heatmap(z=grid*100,x=['0','1','2','3','4','5+'],y=['0','1','2','3','4','5+'],colorscale=[[0,'#fff8f3'],[.4,'#f89276'],[1,'#a40d27']],text=[[f'{v:.1%}' for v in r] for r in grid],texttemplate='',hovertemplate=home+' %{y} – %{x} '+away+'<br>%{z:.2f}%<extra></extra>',showscale=False,xgap=2,ygap=2))
    layout(fig,'<b>Scoreline Probability Grid</b>',510)
    fig.update_layout(title_x=.5,title_xanchor='center',title_y=.98,title_yanchor='top')
    fig.update_layout(margin=dict(l=100,r=85,t=155,b=75))
    logo_uri='data:image/png;base64,'+base64.b64encode((ROOT/'assets/wtatransnew.png').read_bytes()).decode()
    for source,x,y in [(logo_uri,-.10,1.21),(badges.get(home),-.13,.5),(badges.get(away),.5,1.20)]:
        if source:fig.add_layout_image(source=source,xref='paper',yref='paper',x=x,y=y,sizex=.14,sizey=.18,xanchor='center',yanchor='middle',sizing='contain',layer='above')
    for row in range(6):
        for col in range(6):
            fig.add_annotation(x=['0','1','2','3','4','5+'][col],y=['0','1','2','3','4','5+'][row],text=(f'<b>{grid[row,col]:.1%}</b>' if (row,col)==tuple(np.unravel_index(grid.argmax(),grid.shape)) else f'{grid[row,col]:.1%}'),showarrow=False,font=dict(size=14,color='white' if grid[row,col] >= grid.max()*.5 else '#24202b'))
    # Marginal scoring probabilities sum the unrounded simulated cells.
    for index,label in enumerate(['0','1','2','3','4','5+']):
        fig.add_annotation(x=label,y=-.10,xref='x',yref='paper',
                           text=f'<b>{grid[:,index].sum():.1%}</b>',showarrow=False,
                           font=dict(size=12,color='#24202b'),
                           hovertext=f'{away}: {label} goals, regardless of {home} score')
        fig.add_annotation(x=1.04,y=label,xref='paper',yref='y',xanchor='left',
                           text=f'<b>{grid[index,:].sum():.1%}</b>',showarrow=False,
                           font=dict(size=12,color='#24202b'),
                           hovertext=f'{home}: {label} goals, regardless of {away} score')
    fig.add_annotation(x=1.04,y=1.04,xref='paper',yref='paper',text='<b>Total</b>',
                       xanchor='left',showarrow=False,font=dict(size=12,color='#24202b'))
    fig.add_annotation(x=-.02,y=-.10,xref='paper',yref='paper',text='<b>Total</b>',
                       xanchor='right',showarrow=False,font=dict(size=12,color='#24202b'))
    fig.update_xaxes(title=None,side='top',type='category',tickmode='array',tickvals=['0','1','2','3','4','5+'],ticktext=['<b>'+v+'</b>' for v in ['0','1','2','3','4','5+']])
    fig.update_yaxes(title=None,autorange='reversed',type='category',tickmode='array',tickvals=['0','1','2','3','4','5+'],ticktext=['<b>'+v+'</b>' for v in ['0','1','2','3','4','5+']])
    from probability_panel import combined_probability
    probability_chart=combined_probability(fig,wins,colours,outlines,ROOT/'assets/wtatransnew.png',simulation_count)
    st.plotly_chart(probability_chart,width='stretch',theme=None,config={'toImageButtonOptions':{'format':'png','filename':match['id']+'-expected-result','width':1800,'height':733,'scale':2}})
    st.caption(f'Model scoring rates: {home} {rates[0]:.2f} · {away} {rates[1]:.2f}. The 5+ cells include all higher scores. Each shot is simulated with a scoring probability of 70% xG + 30% xGOT. Win/draw probabilities use the unbucketed simulated scores. These are retrospective chance-based estimates.')
elif has_xg:
    st.subheader('Expected Result')
    st.info('The 70/30 probability model needs both xG and xGOT. It is unavailable for this match rather than treating missing xGOT as zero.')

st.caption('Left to right in event order. Circle = Shot · Star = Goal · ! = Own Goal. Own-Goal Badges Show the Benefiting Team. Hover for the player, minute, and chance quality.')
if len(shots):
    shots['order']=range(1,len(shots)+1)
    fig=go.Figure()
    shots['_own_goal']=shots.goal & shots.scorer.notna() & shots.scorer.ne(shots.team)
    for i,t in enumerate(teams):
        s=shots.loc[shots.team.eq(t)]
        fig.add_trace(go.Scatter(x=s.order,y=np.zeros(len(s)),mode='markers',name=t,customdata=np.stack([s.playerName.fillna('Unknown'),s.xg,s.xgot,s.typeId],axis=1),marker=dict(symbol=['star' if g else 'circle' for g in s.goal],size=[0 if own else 22 for own in s._own_goal],color=colours[i],line=dict(color=outlines[i],width=2)),hovertemplate=t+' · %{customdata[0]}<br>%{customdata[3]} · xG %{customdata[1]:.2f} · xGOT %{customdata[2]:.2f}<extra></extra>'))
    for _,shot in shots.iterrows():
        fig.add_annotation(x=int(shot.order),y=0,yshift=-13,text=f'{int(shot.timeMin)}′',showarrow=False,
                           xanchor='center',yanchor='top',font=dict(size=12,color='#24202b',family='Comic Neue, cursive'))
        recipient=shot.scorer if shot['_own_goal'] else shot.team
        source=badges.get(recipient)
        if shot['_own_goal']:
            idx=teams.index(shot.team)
            svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 40"><path d="M9 2 H23 L20 26 H12 Z M12 31 H20 V39 H12 Z" fill="{colours[idx]}" stroke="{outlines[idx]}" stroke-width="2" stroke-linejoin="round"/></svg>'
            own_uri='data:image/svg+xml;base64,'+base64.b64encode(svg.encode()).decode()
            fig.add_layout_image(source=own_uri,xref='x',yref='y',x=int(shot.order),y=0,
                                 sizex=.62,sizey=22*.92/128,xanchor='center',yanchor='middle',sizing='contain',layer='above')
            fig.add_trace(go.Scatter(x=[int(shot.order)],y=[0],mode='markers',marker=dict(size=22,color='rgba(0,0,0,0)'),
                                     hovertemplate=f'{html.escape(str(shot.playerName))} · Own Goal<br>Goal Awarded to {html.escape(str(recipient))}<extra></extra>',showlegend=False))
        if source:
            fig.add_layout_image(source=source,xref='x',yref='y',x=int(shot.order),y=.18,
                                 sizex=.72,sizey=.27,xanchor='center',yanchor='bottom',
                                 sizing='contain',layer='above')
    layout(fig,f'<b>{html.escape(home)} {goals[0]} – {goals[1]} {html.escape(away)} · Match Shot Log</b>',200)
    fig.update_layout(title_font_size=22)
    fig.update_layout(margin=dict(l=45,r=25,t=60,b=12))
    fig.update_layout(title_x=.5,title_xanchor='center')
    brand_uri='data:image/png;base64,'+base64.b64encode((ROOT/'assets/wtatransnew.png').read_bytes()).decode()
    for x,anchor in [(0,'left'),(1,'right')]:
        fig.add_layout_image(source=brand_uri,xref='paper',yref='paper',x=x,y=1.20,
                             sizex=.055,sizey=.24,xanchor=anchor,yanchor='middle',
                             sizing='contain',layer='above')
    fig.update_layout(title_y=.828,title_yanchor='middle')
    fig.update_traces(cliponaxis=False)
    fig.update_yaxes(visible=False,range=[-.22,.7]);fig.update_xaxes(visible=False,range=[.5,len(shots)+.5]);fig.update_layout(hovermode='closest')
    st.plotly_chart(fig,width='stretch',theme=None)
    with st.expander('Shot Details and Export'):
        table=shots[['order','team','playerName','periodId','timeMin','timeSec','typeId','xg','xgot','scorer']].rename(columns={'scorer':'goal credited to'})
        st.dataframe(table,hide_index=True,width='stretch')
        st.download_button('Download shot log',table.to_csv(index=False),file_name=f'{match["id"]}-shots.csv',mime='text/csv')
else:st.info('No recorded shots in this match.')
leaders = performance_rankings.head(5)
from difflib import SequenceMatcher

def canonical_team(source):
    mapped=d.loc[d.team_name.eq(source),'team']
    return mapped.iloc[0] if len(mapped) else max(teams,key=lambda t:SequenceMatcher(None,t.casefold(),str(source).casefold()).ratio())

def player_card(rank,name,team,number,small=False,value=None):
    idx=teams.index(team)
    number='—' if pd.isna(number) else str(number).removesuffix('.0')
    shirt=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 90"><path d="M30 5 L15 12 L2 31 L20 44 L27 34 L27 85 L73 85 L73 34 L80 44 L98 31 L85 12 L70 5 Q50 22 30 5 Z" fill="{colours[idx]}" stroke="{outlines[idx]}" stroke-width="3"/><text x="50" y="59" text-anchor="middle" font-family="Comic Neue,cursive" font-size="29" font-weight="bold" fill="{outlines[idx]}">{html.escape(number)}</text></svg>'
    uri='data:image/svg+xml;base64,'+base64.b64encode(embed_svg_font(shirt).encode()).decode()
    image_size=38 if small else 50
    badge_size=28 if small else 36
    team_badge=badge(team).replace('<img ',f'<img style="height:{badge_size}px;width:{badge_size}px;object-fit:contain;flex-shrink:0" ')
    stat=f'<strong style="margin-left:auto;font-size:18px">{value}</strong>' if value is not None else ''
    st.markdown(f'<div style="display:flex;align-items:center;gap:8px;background:white;border:1px solid #e4dce1;border-radius:12px;padding:10px;margin-bottom:8px"><strong style="font-size:{18 if small else 23}px;min-width:16px">{rank}</strong>{team_badge}<img src="{uri}" width="{image_size}" height="{image_size}" alt="Squad number {html.escape(number)}"><div style="min-width:0"><strong style="font-size:{14 if small else 17}px;overflow-wrap:anywhere">{linked_name(name,team,player_link_context)}</strong><div style="color:#615a67;font-size:{11 if small else 13}px">{html.escape(team)}</div></div>{stat}</div>',unsafe_allow_html=True)

numbers={}
for _,r in roster.iterrows():
    t=canonical_team(r.get('team_name',''))
    for field in ['player_name','playerName']:
        if pd.notna(r.get(field)):numbers[(t,str(r[field]))]=r.get('squad_number',np.nan)
rankings=event_leaders(d)
col1,col2,col3=st.columns([1.15,1,1])
with col1:
    st.subheader('Players of the Match')
    st.caption(f'Top Five · {performance_metric}')
    if leaders.empty:st.info(f'No player-log {performance_metric} rankings are available for this match.')
    for rank,(_,r) in enumerate(leaders.iterrows(),1):
        player_card(rank,r.get('player_name',r.get('playerName','Unknown')),canonical_team(r.get('team_name','')),r.get('squad_number',np.nan))
for column,metrics in [(col2,['xG' if has_xg else 'Most Shots','Chances Created']),(col3,['Defensive Actions','Completed Passes'])]:
    with column:
        for metric in metrics:
            st.markdown(f'#### {metric}')
            if metric=='xG' and not has_xg:
                st.caption('xG data unavailable for this match.')
                continue
            board=rankings[metric]
            if board.empty:st.caption('No qualifying events recorded.')
            for rank,(_,r) in enumerate(board.iterrows(),1):
                value=f'{r[metric]:.2f}' if metric=='xG' else str(int(r[metric]))
                player_card(rank,r.playerName,r.team,numbers.get((r.team,r.playerName),np.nan),small=True,value=value)
physical=bundle['physical']
if not physical.empty:
    boards=[('Most Distance Covered','distanceCoveredKm','km'),('Most Distance Ran','runningKm','km'),('Most Sprints','numberOfSprints','sprints')]
    available=[item for item in boards if item[1] in physical and pd.to_numeric(physical[item[1]],errors='coerce').notna().any()]
    if available:
        st.subheader('Physical Performance')
        physical_columns=st.columns(len(available))
        for column,(heading,field,unit) in zip(physical_columns,available):
            with column:
                st.markdown(f'#### {heading}')
                board=physical.assign(_value=pd.to_numeric(physical[field],errors='coerce')).dropna(subset=['_value','scoresway_name','scoresway_team']).sort_values('_value',ascending=False,kind='stable').drop_duplicates(['scoresway_team','scoresway_name']).head(5)
                for rank,(_,r) in enumerate(board.iterrows(),1):
                    team=canonical_team(r.scoresway_team)
                    value=f'{int(r._value)}' if unit=='sprints' else f'{r._value:.2f} km'
                    player_card(rank,r.scoresway_name,team,numbers.get((team,r.scoresway_name),np.nan),small=True,value=value)
        st.caption('Distance Ran uses FotMob’s Running metric, a subset of total Distance Covered. Rankings appear only for physical metrics published for this match.')

entries=box_entries(d)
if not has_xg:st.caption('xThreat uses signed xT_value from Pass and Carry events only; negative values are retained.')
st.plotly_chart(entries_figure(entries,teams,colours,outlines,badges),width='stretch',theme=None)
st.caption('Successful passes and carries starting outside and ending inside the penalty area (x ≥ 83, y 21.1–78.9). Both teams attack upwards. Corners, throw-ins and free kicks are excluded, as are actions starting inside the box.')
from attacking_areas import attacking_figure
st.subheader('Attacking Areas')
attacking_columns=st.columns(2)
for column,team in zip(attacking_columns,teams):
    with column:
        figure,entry_count,pass_count=attacking_figure(d,team,colours[teams.index(team)],outlines[teams.index(team)],badges.get(team),ROOT/'assets/wtatransnew.png')
        st.plotly_chart(figure,width='stretch',theme=None)
        st.caption(f'{entry_count} Final-Third Entries · {pass_count} Successful Pass Locations in the Final Third')
st.caption('Arrows and percentages show the share of plotted actions (pass starting locations plus shots) within y-axis bands 0–33.33, 33.33–66.6 and 66.6–100. Small dots: successful pass starting locations in the final third; larger translucent dots: shots in the attacking half. Corners, throw-ins and free kicks are excluded from all counts and dots. Both teams attack upwards.')
from defensive_areas import defensive_figure
st.subheader('Defensive Actions')
defensive_columns=st.columns(2)
for column,team in zip(defensive_columns,teams):
    with column:
        figure,action_count,press_count=defensive_figure(d,team,colours[teams.index(team)],outlines[teams.index(team)],badges.get(team),ROOT/'assets/wtatransnew.png')
        st.plotly_chart(figure,width='stretch',theme=None)
        st.caption(f'{action_count} Defensive Actions · {press_count} Pressing 12 Actions')
st.caption('Interceptions, tackles, ball recoveries, defensive duels, challenges and clearances, plus any other event flagged pressing_action_12 = 1. Each event counts once; Pressing 12 actions use bolder circles. Goalkeeper actions (playing_position = GK) are excluded. Percentages describe plotted locations in the team’s own, middle and final thirds using x-axis bands 0–33.33, 33.33–66.6 and 66.6–100. Both teams attack upwards.')
from pitch_control import zone_counts,control_figure
try:
    control_counts=zone_counts(d,home,away)
    control_chart=control_figure(control_counts,teams,colours,badges,ROOT/'assets/wtatransnew.png')
    st.plotly_chart(control_chart,width='stretch',theme=None)
    st.caption('Successful actions only, excluding Player on, Player off, Card and flagged corners, free kicks, goal kicks and throw-ins. A zone is controlled only above 60% of its qualifying actions. Away coordinates are reversed on both axes; neutral zones are grey if a team’s primary colour is white.')
except ValueError as error:
    st.info(str(error))
from average_positions import average_positions,average_figure
st.subheader('Average Positions')
last_minute=max(1,int(np.ceil(pd.to_numeric(d.minute,errors='coerce').max())))
average_range=st.slider('Average Positions · Minute Range',min_value=0,max_value=last_minute,value=(0,last_minute),
                        key='average_range_'+code+'_'+match['id'])
average_roster=roster.copy()
average_roster['team_name']=average_roster.team_name.map(canonical_team)
positions=average_positions(d,average_roster,teams,average_range)
if positions.empty:st.info('No positional events for starters in the selected minute range.')
else:
    st.plotly_chart(average_figure(positions,teams,colours,outlines,badges,ROOT/'assets/wtatransnew.png',average_range),
                    width='stretch',theme=None)
st.caption('Starting players only. Circles show each player’s mean recorded event location in the selected minutes; Player on and Player off events are excluded. Away coordinates are reversed on both axes. Numbers are squad numbers; hover for player names and event counts. These are event-location averages, not tracking positions.')
from possession_chains import longest_chains,chain_figure
st.subheader('Longest Possession Chains')
st.caption('Four longest recorded on-ball sequences per team · Passes: Green · Carries: Purple · Unsuccessful Final Pass: Red · Final Shot: Blue Circle · Goal: Gold Star · Both Teams Attack Upwards')
chain_columns=st.columns(2)
for column,team in zip(chain_columns,teams):
    with column:
        st.markdown(f'#### {html.escape(team)}')
        chains=longest_chains(d,team)
        if chains:
            st.plotly_chart(chain_figure(chains,team,badges.get(team),ROOT/'assets/wtatransnew.png'),width='stretch',theme=None)
        else:st.info('No recorded possession-chain durations are available for this team.')
st.caption('Titles show the first on-ball action’s minute and elapsed seconds between the first and last recorded on-ball actions. Sequences split at recorded stoppages and restarts; waiting time before set pieces and isolated single-action restarts are excluded. Final shots and goals are marked at their recorded starting coordinates. Synthetic carries are omitted when the next recorded on-ball action is by a different player or starts more than 5 coordinate units from the carry endpoint.')
with st.expander('Data and Method'):
    st.write(('Sources: live Opta match-event API and live FotMob match-details API.' if competition_has_xg else 'Source: live Opta match-event API only; this competition is marked no xG in league_dict.')+' Fixtures are selected from your existing schedule files. The score and full-time status come from Opta. Refresh is manual, with the last successful snapshot retained if a request fails. Processing is bundled from your Single Game notebook; schedules and reference files are bundled with this app. Own goals count for the opponent; shootout events are excluded. Missing possession and chance fields are flagged.')
    feed_detail=f'FotMob: {fid}' if competition_has_xg else 'Opta only · No xG coverage'
    st.caption(f'Opta: {match["id"]} · {feed_detail} · {len(d):,} Processed Events · Snapshot: {fetched:%H:%M:%S %Z}')
