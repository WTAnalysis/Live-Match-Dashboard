"""No-xG model from WT Analysis - 2627 No xG Run.ipynb.

Uses the identical GP grid, fixed event values and score/time context weights.
Only adaptation: schedule is an explicit argument, instead of notebook globals.
"""
import pandas as pd
import numpy as np

class UnusableNoXGMatch(ValueError):
    """Missing input data makes this match unprocessable."""
GP_Y_EDGES = np.linspace(0.0, 100.0, 14)
GP_X_EDGES = np.linspace(0.0, 100.0, 21)
GOAL_PROBABILITY_GRID = np.array([[0.0, 0.0005285412262156448, 0.0002941176470588235, 0.0002800336040324839, 0.0018233051549809381, 0.0025572333170969315, 0.001192013509486441, 0.002066892145809846, 0.00199836497411209, 0.003702180172768408, 0.0041841004184100415, 0.0032719836400817996, 0.0034610947314446866, 0.0057093744244582235, 0.008707964601769912, 0.010235870048954161, 0.011764705882352941, 0.01552967276760954, 0.013787510137875101, 0.012720156555772993], [0.0008904719501335708, 0.0, 0.0008291873963515755, 0.001762114537444934, 0.001878245497735057, 0.002208443047651406, 0.001777840989901863, 0.002180088524806765, 0.002775850104094379, 0.0033560459676599207, 0.0038580972993318904, 0.004483079109944782, 0.005489980785067252, 0.008474094295626457, 0.010893390900033212, 0.0151414309484193, 0.017142212698770722, 0.019722508886595574, 0.01997450063748406, 0.018343524180100056], [0.0012547051442910915, 0.0006165228113440197, 0.0005837711617046118, 0.0004827419744146754, 0.0015512465373961218, 0.0014068189341277723, 0.0026225686603045095, 0.003092570957322521, 0.0036034762947784924, 0.004141018466703973, 0.003435352904434728, 0.005164319248826291, 0.006844850065189048, 0.009503122454520771, 0.013444827020823086, 0.021140142517814726, 0.02562862669245648, 0.02608346709470305, 0.028379387602688575, 0.028032345013477088], [0.0, 0.0009062075215224287, 0.0018317598985486826, 0.0010746910263299302, 0.0013848159009449332, 0.0014237959638479633, 0.0025807839131136083, 0.0029017047515415306, 0.00388903292714545, 0.003870861472574535, 0.004651162790697674, 0.005382070976060997, 0.009322186804594935, 0.012295351436649352, 0.01913795972707605, 0.026984950700570835, 0.035140866404119966, 0.04343057688089493, 0.041898031297324584, 0.04468085106382979], [0.0, 0.0014350633819660368, 0.0012234910277324632, 0.0007830853563038371, 0.001320771330456987, 0.0019703139366872456, 0.0024673211192188568, 0.0032385750269881253, 0.0038016705932747913, 0.0049862448418156805, 0.0052039773255273675, 0.00546869973621566, 0.008857204579822855, 0.013813517513566848, 0.021336644840821855, 0.03351432316045684, 0.04140885292717753, 0.057729562185199534, 0.07247386759581882, 0.0758082497212932], [0.0017206767995411529, 0.001466275659824047, 0.0011257360581918947, 0.0014290818149339049, 0.001554726368159204, 0.0020223152022315204, 0.0023227454851634634, 0.003472222222222222, 0.003436106983655275, 0.005668604651162791, 0.007001448575567359, 0.007980652962515114, 0.010910224438902744, 0.014704391035391949, 0.02800953516090584, 0.0407673860911271, 0.05473684210526316, 0.07907253269916766, 0.10120845921450151, 0.14130434782608695], [0.0002949852507374631, 0.0009462528387585163, 0.0007591684185937865, 0.0009837238418887498, 0.0011309891013777504, 0.0024369440721335447, 0.0028021978021978023, 0.003265602322206096, 0.004570541566057261, 0.0038060565944067516, 0.004415871160464965, 0.008437224530915503, 0.010519480519480519, 0.01609657947686117, 0.02760545905707196, 0.045303867403314914, 0.07107601184600197, 0.09691313711414214, 0.16709511568123395, 0.2222222222222222], [0.0, 0.000683900971139379, 0.0009344047841524949, 0.001519756838905775, 0.002023836294130875, 0.002011060834590246, 0.0015841351795353204, 0.004028263884302978, 0.00392156862745098, 0.004909503920275518, 0.005211674150096215, 0.008524173027989822, 0.00986277873070326, 0.014960549236602111, 0.019806338028169015, 0.03627394080092861, 0.048879837067209775, 0.08881199538638986, 0.10619469026548672, 0.10855263157894737], [0.0, 0.0007365578197888534, 0.0011179429849077697, 0.0009674922600619195, 0.0017189514396218307, 0.0015354104024054762, 0.002495670775185902, 0.0029743589743589744, 0.003428037189009505, 0.004313562836997097, 0.004078798923891348, 0.007636454682023034, 0.0089394264463992, 0.01449508777580931, 0.01905292479108635, 0.031485914196280614, 0.03923278116826504, 0.06289542240416822, 0.05762473647224174, 0.07380457380457381], [0.0006954102920723226, 0.0006737031214911295, 0.0005673758865248227, 0.0007093456286575634, 0.0014519333639003516, 0.0021480995286114924, 0.00241607978203876, 0.003332996667003333, 0.003007595452923485, 0.0038959015116097864, 0.004745973702637516, 0.006575458691271609, 0.008238276299112801, 0.012349649450054673, 0.015358636217433259, 0.0265950805343988, 0.029724570493591493, 0.04029692470837752, 0.04237080578006368, 0.04282204282204282], [0.0, 0.0009389671361502347, 0.0011645962732919255, 0.0016802688430148825, 0.0014095196790632116, 0.002461235540241201, 0.0021379310344827587, 0.002599480103979204, 0.002421633257096731, 0.003215778754421696, 0.003493013972055888, 0.004762207124261858, 0.00769570428310099, 0.009512406040045234, 0.013094473007712082, 0.01661523854735343, 0.015086206896551725, 0.02895676318921063, 0.021680876979293544, 0.017376681614349777], [0.0008368200836820083, 0.0011254924029262803, 0.0013101867016049786, 0.001361933946203609, 0.0008683382177358081, 0.0010754467240238254, 0.002166620072686609, 0.0018421052631578947, 0.0030911901081916537, 0.003036129946361704, 0.0031149793861658267, 0.004179331306990881, 0.005156335710367526, 0.0077251239478842385, 0.010424525066867842, 0.012135513231080398, 0.015229615745079663, 0.01734239512538083, 0.017726798748696558, 0.018246027074749854], [0.0, 0.0005411255411255411, 0.0002800336040324839, 0.0010534632604687912, 0.0009448818897637795, 0.0010480959590078024, 0.0015794669299111549, 0.0028296547821165816, 0.0022101482641127177, 0.0033477472450829963, 0.0038282091159229574, 0.0031902166688820947, 0.0033626004109844946, 0.005291005291005291, 0.007636286502156544, 0.00790262512489781, 0.012003556609365739, 0.01271921372133359, 0.011330255979857323, 0.012318029115341545]], dtype=float)

def context_multiplier(state, minute, goalkeeper=False):
    state = pd.to_numeric(state, errors='coerce')
    minute = pd.to_numeric(minute, errors='coerce')
    weight = pd.Series(1.0, index=state.index)
    weight.loc[(state.eq(0) & minute.lt(60)).fillna(False)] = 1.1
    weight.loc[(state.eq(0) & minute.between(60, 80)).fillna(False)] = 1.125
    weight.loc[(state.eq(0) & minute.gt(80)).fillna(False)] = 1.15
    close = state.abs().eq(1)
    if not goalkeeper:
        close &= minute.gt(70)
    weight.loc[close.fillna(False)] = 1.05
    return weight

def gp_at(x, y):
    x = pd.to_numeric(x, errors='coerce')
    y = pd.to_numeric(y, errors='coerce')
    xb = pd.cut(x, GP_X_EDGES, labels=False, include_lowest=True)
    yb = pd.cut(y, GP_Y_EDGES, labels=False, include_lowest=True)
    valid = xb.notna() & yb.notna()
    values = pd.Series(0.0, index=x.index, dtype=float)
    values.loc[valid] = GOAL_PROBABILITY_GRID[yb.loc[valid].astype(int), xb.loc[valid].astype(int)]
    return values
SHOT_TYPES = {'Attempt Saved', 'Miss', 'Post', 'Goal'}
SYNTHETIC_TYPES = {'goal_conceded', 'clean_sheet', 'position_change'}

def prepare_no_xg_match(events, lineups, match_id, schedule):
    events = events.copy()
    lineups = lineups.loc[:, ~lineups.columns.duplicated()].copy()
    lineups = lineups.drop_duplicates(['player_id', 'match_id']).reset_index(drop=True)
    events['typeId'] = events.typeId.replace({'Attempted saved': 'Attempt Saved', 'Attempted Saved': 'Attempt Saved', 'Attempt saved': 'Attempt Saved'})
    for c in ['timeMin', 'timeSec', 'x', 'y', 'end_x', 'end_y', 'periodId']:
        events[c] = pd.to_numeric(events[c], errors='coerce')
    events['timeSec'] = events.timeSec.fillna(0.0)
    events = events.loc[events.periodId.ne(5)].copy()
    events['event_time'] = events.timeMin * 60 + events.timeSec
    events = events.sort_values(['periodId', 'timeMin', 'timeSec'], kind='stable').reset_index(drop=True)
    teams = lineups.team_name.dropna().unique().tolist()
    if len(teams) != 2:
        raise ValueError('No XG processing needs exactly two match teams.')
    team_a, team_b = teams
    goals = events.loc[events.typeId.isin(['Goal', 'Own Goal'])].copy()
    if 'id' in goals:
        real = goals.id.notna()
        goals = pd.concat([goals.loc[real].drop_duplicates(['id', 'team_name']), goals.loc[~real]])
    scoring = {}
    for idx, row in goals.iterrows():
        scoring[idx] = row.team_name if row.typeId == 'Goal' else team_b if row.team_name == team_a else team_a
    scores = {team_a: 0, team_b: 0}
    for idx, row in events.iterrows():
        team = row.team_name
        opponent = team_b if team == team_a else team_a
        events.at[idx, 'game_state_before'] = scores.get(team, 0) - scores.get(opponent, 0)
        if idx in scoring:
            scores[scoring[idx]] += 1
        events.at[idx, 'game_state'] = scores.get(team, 0) - scores.get(opponent, 0)
    events['_ball_out_of_play'] = events.x.lt(0) | events.x.gt(100) | events.y.lt(0) | events.y.gt(100)
    events['model_variant'] = 'NO_XG_GP_PAR'
    events['match_id'] = str(match_id)
    scheduled = schedule.loc[str(match_id)] if str(match_id) in schedule.index else None
    for table in (events, lineups):
        table['date'] = scheduled.get('date', pd.NA) if scheduled is not None else pd.NA
        table['opponent'] = table.team_name.map({team_a: team_b, team_b: team_a})
        home = scheduled.get('Home_Team') if scheduled is not None else None
        away = scheduled.get('Away_Team') if scheduled is not None else None
        table['venue'] = table.team_name.map({home: 'Home', away: 'Away'}) if home and away else pd.NA
    unknown = events.loc[events.playerName.notna() & ~events.typeId.isin(SYNTHETIC_TYPES), ['team_name', 'playerName', 'typeId']]
    lineup_keys = set(zip(lineups.team_name, lineups.player_name))
    unresolved = []
    for (team, name), group in unknown.groupby(['team_name', 'playerName']):
        if (team, name) not in lineup_keys and (not group.typeId.isin(['Card', 'Out', 'Deleted event']).all()):
            unresolved.append((team, name))
    if unresolved:
        raise UnusableNoXGMatch('On-ball players missing from the lineup/minutes records; match excluded rather than assigning invented minutes: ' + str(unresolved[:10]))
    duration = events.loc[~events.typeId.isin(SYNTHETIC_TYPES), 'event_time'].max() / 60
    if not np.isfinite(duration) or duration <= 0:
        raise ValueError('Match duration cannot be determined from event times.')
    lineups['team_match_minutes'] = duration
    for idx, row in lineups.iterrows():
        team = row.team_name
        opponent = team_b if team == team_a else team_a
        lineups.at[idx, 'team_total_goals_for'] = scores[team]
        lineups.at[idx, 'team_total_goals_against'] = scores[opponent]
    value = pd.to_numeric(events.xT_value, errors='coerce').fillna(0.0)
    start = gp_at(events.x, events.y)
    end = gp_at(events.end_x, events.end_y)
    success = events.outcome.eq('Successful')
    passes = events.typeId.eq('Pass')
    value.loc[passes] = np.where(success.loc[passes], (end - start).loc[passes], -start.loc[passes])
    carries = events.typeId.eq('Carry')
    value.loc[carries] = (end - start).loc[carries]
    defence = events.typeId.isin(['Tackle', 'Interception', 'Ball recovery', 'Ball Recovery', 'Clearance', 'Blocked Pass', 'Defensive Duel', 'Aerial'])
    defensive_zone = gp_at(100 - events.x, 100 - events.y)
    value.loc[defence] = (defensive_zone * events.outcome.map({'Successful': 1.0, 'Unsuccessful': -1.0}).fillna(0.0)).loc[defence]
    shots = events.typeId.isin(SHOT_TYPES)
    fixed_shots = events.typeId.map({'Goal': 0.95, 'Attempt Saved': 0.2, 'Miss': 0.05, 'Post': 0.1})
    fixed_shots = fixed_shots.where(pd.to_numeric(events.get('shotblocked', 0), errors='coerce').ne(1), 0.05)
    value.loc[shots] = fixed_shots.loc[shots]
    cards = events.typeId.eq('Card')
    value.loc[cards] = pd.to_numeric(events.get('card_value', pd.Series(0.0, index=events.index)), errors='coerce').fillna(0.0).loc[cards]
    assist = pd.to_numeric(events.get('assist', pd.Series(0, index=events.index)), errors='coerce').eq(1)
    keypass = pd.to_numeric(events.get('keyPass', pd.Series(0, index=events.index)), errors='coerce').eq(1)
    value.loc[assist] = 0.6
    value.loc[keypass & ~assist] += 0.1
    fouls = events.typeId.eq('Foul') & events.outcome.isin(['Successful', 'Unsuccessful'])
    foul_x = events.x.where(success, 100 - events.x)
    foul_y = events.y.where(success, 100 - events.y)
    zone = gp_at(foul_x, foul_y)
    box = foul_x.between(83, 100) & foul_y.between(21.1, 78.9)
    value.loc[fouls] = (np.where(success, 1.0, -1.0) * np.where(box, 0.78 - zone, zone))[fouls]
    events['xT_value_unweighted'] = value
    events['rating_context_multiplier'] = context_multiplier(events.game_state_before, events.timeMin)
    events['xT_value'] = value * events.rating_context_multiplier
    events['received_pass_GP'] = 0.0
    receiver = events.get('pass_recipient', pd.Series(pd.NA, index=events.index))
    received = passes & success & receiver.notna()
    events.loc[received, 'received_pass_GP'] = (end * events.rating_context_multiplier).loc[received]
    events = add_no_xg_possession_chains(events, teams)
    events = add_defensive_action_flags(add_pressing_actions(events))
    action = events.groupby(['team_name', 'playerName']).xT_value.sum()
    credit = events.loc[events.received_pass_GP.ne(0)].groupby(['team_name', 'pass_recipient']).received_pass_GP.sum().rename_axis(['team_name', 'playerName'])
    score = action.add(credit, fill_value=0)
    lineups['Threat Value'] = [float(score.get((r.team_name, r.player_name), 0.0)) for r in lineups.itertuples()]
    lineups['Goal_Probability_value'] = lineups['Threat Value']
    lineups['model_variant'] = 'NO_XG_GP_PAR'
    return (events, lineups, teams)

def add_no_xg_possession_chains(events, teams):
    df = events.copy()
    team_a, team_b = teams
    df['possession_chain'] = pd.Series(pd.NA, index=df.index, dtype='Int64')
    df['possession_chain_time'] = pd.Series(pd.NA, index=df.index, dtype='Float64')
    synthetic_event_types = {'goal_conceded', 'clean_sheet', 'position_change'}
    shot_event_types = {'Attempt Saved', 'Attempted saved', 'Goal', 'Own Goal', 'Miss', 'Post'}
    chain_number_by_team = {team_a: 0, team_b: 0}
    possession_state = {'indices': [], 'team': None, 'period': None}
    previous_event_ended_chain = False

    def finalise_possession_chain():
        if len(possession_state['indices']) >= 2:
            chain_team = possession_state['team']
            chain_number_by_team[chain_team] += 1
            chain_number = chain_number_by_team[chain_team]
            df.loc[possession_state['indices'], 'possession_chain'] = chain_number
            first_idx = possession_state['indices'][0]
            last_idx = possession_state['indices'][-1]
            start_seconds = float(df.at[first_idx, 'timeMin']) * 60.0 + float(df.at[first_idx, 'timeSec'])
            end_seconds = float(df.at[last_idx, 'timeMin']) * 60.0 + float(df.at[last_idx, 'timeSec'])
            df.at[last_idx, 'possession_chain_time'] = max(0.0, end_seconds - start_seconds)
        possession_state['indices'] = []
        possession_state['team'] = None
        possession_state['period'] = None
    for row_idx, row in df.iterrows():
        event_type = row['typeId']
        if event_type in synthetic_event_types:
            continue
        team = row['team_name']
        period = row['periodId']
        has_valid_event = team in chain_number_by_team and pd.notna(period) and pd.notna(row['timeMin']) and pd.notna(row['timeSec'])
        if not has_valid_event:
            finalise_possession_chain()
            previous_event_ended_chain = False
            continue
        starts_new_chain = not possession_state['indices'] or team != possession_state['team'] or period != possession_state['period'] or previous_event_ended_chain
        if starts_new_chain:
            finalise_possession_chain()
            possession_state['team'] = team
            possession_state['period'] = period
        possession_state['indices'].append(row_idx)
        outcome_ends_chain = str(row['outcome']).strip().lower() == 'unsuccessful'
        coordinates_end_chain = bool(row['_ball_out_of_play'])
        shot_ends_chain = event_type in shot_event_types
        previous_event_ended_chain = outcome_ends_chain or coordinates_end_chain or shot_ends_chain
    finalise_possession_chain()
    df['chain_ended_with_shot'] = False
    ends = df.loc[df.possession_chain_time.notna()]
    for _, r in ends.iterrows():
        mask = df.team_name.eq(r.team_name) & df.periodId.eq(r.periodId) & df.possession_chain.eq(r.possession_chain)
        df.loc[mask, 'chain_ended_with_shot'] = r.typeId in SHOT_TYPES
    return df

def add_defensive_action_flags(events):
    events = events.copy()
    events['defensive_duels'] = events['typeId'].eq('Defensive Duel').fillna(False).astype(int)
    events['defensive_duels_won'] = (events['typeId'].eq('Defensive Duel') & events['outcome'].eq('Successful')).fillna(False).astype(int)
    events['counter_press_defensive_actions'] = (events['typeId'].isin(['Interception', 'Ball recovery', 'Tackle', 'Defensive Duel']) | events['typeId'].eq('Foul') & events['outcome'].eq('Unsuccessful')).fillna(False).astype(int)
    return events

def add_pressing_actions(events):
    """Apply identical pressing rules with inclusive 8- and 12-second limits."""
    result = events.copy()
    limits = {'pressing_action': 8, 'pressing_action_12': 12}
    for column in limits:
        result[column] = 0

    def number(value):
        value = pd.to_numeric(value, errors='coerce')
        return float(value) if pd.notna(value) else float('nan')

    def equals(value, expected):
        return pd.notna(value) and value == expected
    previous = None
    before_previous = None
    recent_passes = {}
    for index, row in result.iterrows():
        period, team, player = (row['periodId'], row['team_name'], row['playerName'])
        seconds = number(row['timeMin']) * 60 + number(row['timeSec'])
        if pd.isna(period) or pd.isna(team) or pd.isna(seconds):
            before_previous = previous
            previous = row
            continue
        action = row['typeId']
        defensive = any((equals(action, name) for name in ('Tackle', 'Ball recovery', 'Challenge', 'Defensive Duel')))
        defensive = defensive or (equals(action, 'Foul') and equals(row['outcome'], 'Unsuccessful'))
        key = (period, team)
        recent = [(when, passer) for when, passer in recent_passes.get(key, []) if 0 <= seconds - when <= 12]
        successful_teammate_pass = previous is not None and (equals(previous['team_name'], team) and equals(previous['typeId'], 'Pass') and equals(previous['outcome'], 'Successful'))
        eligible_location = number(row['x']) >= 33.3
        opponent_previous = previous is not None and (equals(previous['periodId'], period) and pd.notna(previous['team_name']) and (previous['team_name'] != team))
        recovery_elapsed = float('nan')
        if opponent_previous and before_previous is not None and equals(previous['typeId'], 'Carry') and equals(previous['outcome'], 'Successful') and equals(before_previous['typeId'], 'Ball recovery') and equals(before_previous['outcome'], 'Successful') and equals(before_previous['periodId'], period) and equals(before_previous['team_name'], previous['team_name']) and pd.notna(previous['playerName']) and equals(before_previous['playerName'], previous['playerName']):
            recovery_seconds = number(before_previous['timeMin']) * 60 + number(before_previous['timeSec'])
            carry_seconds = number(previous['timeMin']) * 60 + number(previous['timeSec'])
            if recovery_seconds <= carry_seconds <= seconds:
                recovery_elapsed = seconds - recovery_seconds
        for column, limit in limits.items():
            pressing = False
            if eligible_location and pd.notna(player) and (not successful_teammate_pass):
                if opponent_previous:
                    chain_time = number(previous['possession_chain_time'])
                    if 0 <= chain_time <= limit:
                        pressing = defensive and (equals(previous['outcome'], 'Unsuccessful') or equals(previous['typeId'], 'Dispossessed'))
                        pressing = pressing or (equals(action, 'Interception') and equals(previous['typeId'], 'Pass') and equals(previous['outcome'], 'Unsuccessful') and (number(previous['longball']) == 0))
                if defensive:
                    pressing = pressing or 0 <= recovery_elapsed <= limit
                    pressing = pressing or any((passer != player and 0 <= seconds - when <= limit for when, passer in recent))
            result.at[index, column] = int(pressing)
        if equals(action, 'Pass') and equals(row['outcome'], 'Unsuccessful') and (number(row['freekick']) == 0) and (number(row['corner']) == 0) and pd.notna(player):
            recent.append((seconds, player))
        recent_passes[key] = recent
        before_previous = previous
        previous = row
    return result
