def _live_grid_value(grid,y,x):
    if pd.isna(x) or pd.isna(y):return 0.0
    return float(grid[min(max(int(y),0),grid.shape[0]-1),min(max(int(x),0),grid.shape[1]-1)])

import pandas as pd
formation_rows = df[df['typeId'] == 34]
formation_dfs = []
for _, row in formation_rows.iterrows():
    row_data = row.to_dict()
    contestant_id = row_data.get('contestantId', None)
    qualifier_cols = [col for col in row.index if 'qualifierId' in col]
    formation_code = None
    player_ids = []
    squad_numbers = []
    formation_positions = []
    for col in qualifier_cols:
        try:
            qualifier_id = row[col]
            value_col = df.columns[df.columns.get_loc(col) + 1]
            value = row[value_col]
            if qualifier_id == 130:
                formation_code = value
            elif qualifier_id == 30:
                player_ids = str(value).split(',')
            elif qualifier_id == 59:
                squad_numbers = str(value).split(',')
            elif qualifier_id == 131:
                formation_positions = str(value).split(',')
        except:
            continue
    num_players = len(player_ids)
    data = {'formation_code': [formation_code] * num_players, 'player_id': player_ids, 'squad_number': squad_numbers, 'formation_position': formation_positions, 'is_starter': ['yes' if i < 11 else 'no' for i in range(num_players)], 'contestant_id': [contestant_id] * num_players}
    formation_df = pd.DataFrame(data)
    formation_dfs.append(formation_df)
formation_dfs = pd.concat(formation_dfs, ignore_index=True)
player_lookup = df[['playerId', 'playerName']].dropna().drop_duplicates()
formation_dfs['player_id'] = formation_dfs['player_id'].astype(str).str.strip()
player_lookup['playerId'] = player_lookup['playerId'].astype(str).str.strip()
formation_dfs = formation_dfs.merge(player_lookup, left_on='player_id', right_on='playerId', how='left').drop(columns=['playerId'])
formation_dfs
formation_dict['formation_code'] = formation_dict['formation_code'].astype(str).str.strip()
formation_dict_melted = formation_dict.melt(id_vars='formation_code', var_name='formation_position', value_name='position')
formation_dfs = formation_dfs[formation_dfs['formation_position'].notna()].copy()
formation_dfs['formation_position'] = formation_dfs['formation_position'].astype(float).astype(int).astype(str)
formation_dict_melted['formation_position'] = formation_dict_melted['formation_position'].astype(str)
formation_dfs = formation_dfs.merge(formation_dict_melted, on=['formation_code', 'formation_position'], how='left')
formation_dfs['playerName'] = formation_dfs['playerName'].fillna(formation_dfs['player_id'].map(_live_name_lookup))
formation_dfs['match_id'] = matchlink
formation_dfs.rename(columns={'playerName': 'player_name'}, inplace=True)
starting_lineups = formation_dfs[['match_id', 'contestant_id', 'player_name', 'squad_number', 'position', 'is_starter', 'formation_position', 'player_id']]
subs_off = df[df['typeId'] == 18][['playerName', 'timeMin', 'periodId']].dropna()
subs_off['playerName'] = subs_off['playerName'].astype(str).str.strip()
starting_lineups['player_name'] = starting_lineups['player_name'].astype(str).str.strip()
starting_lineups = starting_lineups.merge(subs_off, left_on='player_name', right_on='playerName', how='left').drop(columns=['playerName'])
starting_lineups.rename(columns={'timeMin': 'minutes_played'}, inplace=True)
starting_lineups['subbed_off'] = starting_lineups['minutes_played'].apply(lambda x: 'yes' if pd.notna(x) else 'no')
subs_on = df[df['typeId'] == 19][['playerName', 'timeMin', 'periodId']].dropna()
subs_on['playerName'] = subs_on['playerName'].astype(str).str.strip()
max_time = df['timeMin'].max()
subs_on['minutes_played'] = max_time - subs_on['timeMin']
subs_on['subbed_on'] = 'yes'
starting_lineups['player_name'] = starting_lineups['player_name'].astype(str).str.strip()
starting_lineups = starting_lineups.merge(subs_on, left_on='player_name', right_on='playerName', how='left').drop(columns=['playerName'])
starting_lineups['subbed_on'] = starting_lineups['subbed_on'].fillna('no')
starting_lineups['minutes_played'] = starting_lineups['minutes_played_x'].combine_first(starting_lineups['minutes_played_y'])
starting_lineups.drop(columns=['minutes_played_x', 'minutes_played_y'], inplace=True)
subs_on_events = df[df['typeId'] == 19][['playerId', 'playerName']].dropna().copy()
subs_on_events['playerId'] = subs_on_events['playerId'].astype(str).str.strip()
subs_on_events['playerName'] = subs_on_events['playerName'].astype(str).str.strip()
subs_on_events['event_index'] = subs_on_events.index
formation_changes = df[df['typeId'] == 40].copy()
formation_updates = []
formation_name_lookup = formation_dict[['formation_code', 'formation']].drop_duplicates('formation_code').set_index('formation_code')['formation'].to_dict()
formation_timeline_records = []
initial_team_formations = formation_dfs[['contestant_id', 'formation_code']].dropna().drop_duplicates('contestant_id', keep='first')
for _, initial_formation in initial_team_formations.iterrows():
    initial_code = str(initial_formation['formation_code']).strip()
    formation_timeline_records.append({'contestant_id': str(initial_formation['contestant_id']).strip(), 'formation_code': initial_code, 'formation': formation_name_lookup.get(initial_code), 'periodId': 1, 'timeMin': 0.0, 'timeSec': 0.0, '_event_order': 1000000.0})
if not formation_changes.empty:
    for _, row in formation_changes.iterrows():
        row_data = row.to_dict()
        contestant_id = row_data.get('contestantId', None)
        qualifier_cols = [col for col in row.index if 'qualifierId' in col]
        formation_code = None
        player_ids = []
        formation_positions = []
        for col in qualifier_cols:
            try:
                qualifier_id = row[col]
                value_col = df.columns[df.columns.get_loc(col) + 1]
                value = row[value_col]
                if qualifier_id == 130:
                    formation_code = str(value).strip()
                elif qualifier_id == 30:
                    player_ids = str(value).split(',')
                elif qualifier_id == 131:
                    formation_positions = str(value).split(',')
            except:
                continue
        if formation_code and player_ids and formation_positions:
            change_period = pd.to_numeric(pd.Series([row_data.get('periodId')]), errors='coerce').iloc[0]
            change_minute = pd.to_numeric(pd.Series([row_data.get('timeMin')]), errors='coerce').iloc[0]
            change_second = pd.to_numeric(pd.Series([row_data.get('timeSec')]), errors='coerce').fillna(0).iloc[0]
            if pd.notna(change_period) and pd.notna(change_minute):
                formation_timeline_records.append({'contestant_id': str(contestant_id).strip(), 'formation_code': formation_code, 'formation': formation_name_lookup.get(formation_code), 'periodId': int(change_period), 'timeMin': float(change_minute), 'timeSec': float(change_second), '_event_order': float(change_period) * 1000000.0 + float(change_minute) * 60.0 + float(change_second)})
            for i, pid in enumerate(player_ids):
                pid = pid.strip()
                formation_position = str(i + 1)
                formation_updates.append({'player_id': pid, 'formation_code': formation_code, 'formation_position': formation_position})
    if formation_updates:
        sub_positions_df = pd.DataFrame(formation_updates)
        sub_positions_df = sub_positions_df.merge(formation_dict_melted, on=['formation_code', 'formation_position'], how='left')
    else:
        pass
        sub_positions_df = pd.DataFrame(columns=['player_id', 'formation_code', 'formation_position', 'position'])
else:
    pass
    sub_positions_df = pd.DataFrame(columns=['player_id', 'formation_code', 'formation_position', 'position'])
starting_lineups = starting_lineups.merge(sub_positions_df[['player_id', 'position']], on='player_id', how='left', suffixes=('', '_new'))
starting_lineups['position'] = starting_lineups['position'].combine_first(starting_lineups['position_new'])
starting_lineups.drop(columns=['position_new'], inplace=True)
subs_on_events = df[df['typeId'] == 19][['playerId', 'playerName', 'contestantId']].dropna().copy()
subs_on_events['playerId'] = subs_on_events['playerId'].astype(str).str.strip()
subs_on_events['playerName'] = subs_on_events['playerName'].astype(str).str.strip()
subs_on_events['event_index'] = subs_on_events.index
for _, sub_on_row in subs_on_events.iterrows():
    idx = sub_on_row['event_index']
    team_id = sub_on_row['contestantId']
    sub_on_name = sub_on_row['playerName']
    for lookback in range(1, 6):
        if idx - lookback < 0:
            break
        prev_row = df.iloc[idx - lookback]
        if prev_row['typeId'] == 18 and prev_row['contestantId'] == team_id:
            sub_off_name = str(prev_row['playerName']).strip()
            sub_off_row = starting_lineups[(starting_lineups['player_name'] == sub_off_name) & starting_lineups['position'].notna()]
            if sub_off_row.empty:
                break
            inherited_position = sub_off_row.iloc[0]['position']
            mask = (starting_lineups['player_name'] == sub_on_name) & (starting_lineups['subbed_on'] == 'yes') & starting_lineups['position'].isna()
            if mask.any():
                starting_lineups.loc[mask, 'position'] = inherited_position
            break
max_time = df['timeMin'].max()
starting_lineups.loc[(starting_lineups['is_starter'] == 'yes') & (starting_lineups['subbed_off'] == 'no'), 'minutes_played'] = max_time
starting_lineups = starting_lineups.loc[starting_lineups['player_name'] != 'nan']
cards = df[df['typeId'] == 17].copy()
qualifier_cols = [col for col in cards.columns if 'qualifierId' in col]
if not cards.empty:
    cards['is_sent_off'] = cards[qualifier_cols].apply(lambda row: any((q in [32, 33] for q in row.values if pd.notna(q))), axis=1)
    sent_off = cards[cards['is_sent_off']][['playerName', 'timeMin']].dropna().copy()
    sent_off.rename(columns={'playerName': 'player_name', 'timeMin': 'sent_off_min'}, inplace=True)
    sent_off['player_name'] = sent_off['player_name'].astype(str).str.strip()
else:
    sent_off = pd.DataFrame(columns=['player_name', 'sent_off_min'])
starting_lineups['player_name'] = starting_lineups['player_name'].astype(str).str.strip()
starting_lineups = starting_lineups.merge(sent_off, on='player_name', how='left')
starting_lineups.loc[starting_lineups['sent_off_min'].notna() & (starting_lineups['is_starter'] == 'yes'), 'minutes_played'] = starting_lineups['sent_off_min']
starting_lineups.loc[starting_lineups['sent_off_min'].notna() & (starting_lineups['is_starter'] == 'no'), 'minutes_played'] = starting_lineups['sent_off_min'] - starting_lineups['minutes_played']
starting_lineups.drop(columns=['sent_off_min'], inplace=True)
from collections import defaultdict
player_position_changes = defaultdict(set)
formation_changes = df[df['typeId'] == 40].copy()
for _, row in formation_changes.iterrows():
    row_data = row.to_dict()
    contestant_id = row_data.get('contestantId', None)
    qualifier_cols = [col for col in row.index if 'qualifierId' in col]
    formation_code = None
    player_ids = []
    formation_positions = []
    for col in qualifier_cols:
        try:
            qualifier_id = row[col]
            value_col = df.columns[df.columns.get_loc(col) + 1]
            value = row[value_col]
            if qualifier_id == 130:
                formation_code = str(value).strip()
            elif qualifier_id == 30:
                player_ids = str(value).split(',')
            elif qualifier_id == 131:
                formation_positions = str(value).split(',')
        except:
            continue
    if not (formation_code and player_ids and formation_positions):
        continue
    formation_snapshot = pd.DataFrame({'formation_code': [formation_code] * len(player_ids), 'player_id': [pid.strip() for pid in player_ids], 'formation_position': [str(i + 1) for i in range(len(player_ids))], 'contestant_id': [contestant_id] * len(player_ids)})
    formation_snapshot = formation_snapshot.merge(formation_dict_melted, on=['formation_code', 'formation_position'], how='left')
    for _, player_row in formation_snapshot.iterrows():
        pid = player_row['player_id']
        new_pos = player_row['position']
        if pd.isna(new_pos):
            continue
        match = starting_lineups[(starting_lineups['player_id'] == pid) & (starting_lineups['contestant_id'] == contestant_id)]
        if match.empty:
            continue
        current_pos = match.iloc[0]['position']
        if pd.isna(current_pos):
            continue
        if new_pos != current_pos:
            player_position_changes[pid].add(new_pos)
starting_lineups['other_positions'] = starting_lineups['player_id'].apply(lambda pid: ', '.join(sorted(player_position_changes[pid])) if pid in player_position_changes else None)
player_position_change_times = defaultdict(dict)
for _, row in formation_changes.iterrows():
    row_data = row.to_dict()
    contestant_id = row_data.get('contestantId', None)
    time_min = row_data.get('timeMin', None)
    time_sec = row_data.get('timeSec', None)
    period_id = row_data.get('periodId', None)
    qualifier_cols = [col for col in row.index if 'qualifierId' in col]
    formation_code = None
    player_ids = []
    formation_positions = []
    for col in qualifier_cols:
        try:
            qualifier_id = row[col]
            value_col = df.columns[df.columns.get_loc(col) + 1]
            value = row[value_col]
            if qualifier_id == 130:
                formation_code = str(value).strip()
            elif qualifier_id == 30:
                player_ids = str(value).split(',')
            elif qualifier_id == 131:
                formation_positions = str(value).split(',')
        except:
            continue
    if not (formation_code and player_ids and formation_positions):
        continue
    formation_snapshot = pd.DataFrame({'formation_code': [formation_code] * len(player_ids), 'player_id': [pid.strip() for pid in player_ids], 'formation_position': [str(i + 1) for i in range(len(player_ids))], 'contestant_id': [contestant_id] * len(player_ids)})
    formation_snapshot = formation_snapshot.merge(formation_dict_melted, on=['formation_code', 'formation_position'], how='left')
    for _, player_row in formation_snapshot.iterrows():
        pid = player_row['player_id']
        new_pos = player_row['position']
        if pd.isna(new_pos):
            continue
        match = starting_lineups[(starting_lineups['player_id'] == pid) & (starting_lineups['contestant_id'] == contestant_id)]
        if match.empty or pd.isna(match.iloc[0]['position']):
            continue
        current_pos = match.iloc[0]['position']
        if new_pos != current_pos:
            if new_pos not in player_position_change_times[pid]:
                player_position_change_times[pid][new_pos] = {'periodId': period_id, 'timeMin': time_min, 'timeSec': time_sec}
initial_position_lookup = starting_lineups.set_index('player_id')['position'].dropna().to_dict()

def is_before_or_equal(change_time, row_time):
    return change_time['periodId'] < row_time['periodId'] or (change_time['periodId'] == row_time['periodId'] and (change_time['timeMin'] < row_time['timeMin'] or (change_time['timeMin'] == row_time['timeMin'] and change_time['timeSec'] <= row_time['timeSec'])))

def resolve_position(row):
    pid = str(row.get('playerId')).strip()
    if pid not in initial_position_lookup:
        return None
    current_time = {'periodId': row.get('periodId'), 'timeMin': row.get('timeMin'), 'timeSec': row.get('timeSec')}
    if pid not in player_position_change_times:
        return initial_position_lookup[pid]
    changes = player_position_change_times[pid]
    valid_changes = []
    for pos, change_time in changes.items():
        if is_before_or_equal(change_time, current_time):
            valid_changes.append((change_time, pos))
    if not valid_changes:
        return initial_position_lookup[pid]
    valid_changes.sort(key=lambda x: (x[0]['periodId'], x[0]['timeMin'], x[0]['timeSec']), reverse=True)
    return valid_changes[0][1]
df['playing_position'] = df.apply(resolve_position, axis=1)
max_match_time = starting_lineups['minutes_played'].max()
position_change_rows = []
player_name_map = starting_lineups.set_index('player_id')['player_name'].to_dict()
team_name_map = starting_lineups.set_index('player_id')['contestant_id'].to_dict()
for pid, changes in player_position_change_times.items():
    player_name = player_name_map.get(pid, None)
    team_name = team_name_map.get(pid, None)
    for pos, time_info in changes.items():
        position_change_rows.append({'timeMin': time_info['timeMin'], 'timeSec': time_info['timeSec'], 'playerId': pid, 'playerName': player_name, 'typeId': 'position_change', 'playing_position': pos, 'periodId': time_info['periodId']})
position_change_df = pd.DataFrame(position_change_rows)
red_card_events = df.iloc[:, 16:]
is_red_card = red_card_events.apply(lambda row: 32 in row.values or 33 in row.dropna().values, axis=1)
red_card_df = df[is_red_card & (df['typeId'] == 'Card')]
red_card_times = red_card_df.groupby('playerId')['timeMin'].min().to_dict()
for idx, row in starting_lineups.iterrows():
    player_id = row['player_id']
    if player_id in red_card_times:
        starting_lineups.at[idx, 'minutes_played'] = red_card_times[player_id]
starting_lineups['time_on'] = starting_lineups.apply(lambda row: max_match_time - row['minutes_played'] if row['subbed_on'] == 'yes' and pd.notna(row['minutes_played']) else None, axis=1)
starting_lineups['time_off'] = starting_lineups.apply(lambda row: row['minutes_played'] if row['is_starter'] == 'yes' and pd.notna(row['minutes_played']) and (row['minutes_played'] != max_match_time) else None, axis=1)
starting_lineups['time_on'] = starting_lineups['time_on'].fillna(0)
starting_lineups['time_off'] = starting_lineups['time_off'].fillna(max_match_time)
red_card_events = df.iloc[:, 16:]
is_red_card = red_card_events.apply(lambda row: 32 in row.values or 33 in row.dropna().values, axis=1)
red_card_df = df[is_red_card & (df['typeId'] == 'Card')]
red_card_times = red_card_df[['playerId', 'timeMin']].groupby('playerId').min().to_dict()['timeMin']
for idx, row in starting_lineups.iterrows():
    player_id = row['player_id']
    if player_id in red_card_times:
        starting_lineups.at[idx, 'time_off'] = red_card_times[player_id]
starting_lineups.loc[(starting_lineups['time_on'] == 0) & (starting_lineups['subbed_off'] == 'yes'), 'time_off'] = starting_lineups['minutes_played']
from collections import defaultdict
position_timeline = defaultdict(list)
for player_id, changes in player_position_change_times.items():
    initial_pos = initial_position_lookup.get(player_id)
    if initial_pos:
        position_timeline[player_id].append((0, initial_pos))
    for pos, time_data in sorted(changes.items(), key=lambda x: (x[1]['periodId'], x[1]['timeMin'], x[1]['timeSec'])):
        if time_data['timeMin'] is not None:
            position_timeline[player_id].append((time_data['timeMin'], pos))
for player_id, timeline in position_timeline.items():
    timeline = sorted(timeline, key=lambda x: x[0])
    updated = []
    for i in range(len(timeline)):
        start_time, pos = timeline[i]
        end_time = timeline[i + 1][0] if i + 1 < len(timeline) else starting_lineups[starting_lineups['player_id'] == player_id]['minutes_played'].max()
        duration = end_time - start_time
        updated.append((pos, duration))
    position_timeline[player_id] = updated[:5]
for i in range(5):
    pos_col = f'position{i + 1}'
    min_col = f'position{i + 1}mins'
    starting_lineups[pos_col] = None
    starting_lineups[min_col] = None
for idx, row in starting_lineups.iterrows():
    player_id = row['player_id']
    match_id = row['match_id']
    player_changes = [r for r in position_change_rows if r['playerId'] == player_id]
    if row['position'] and (not any((r['timeMin'] == 0 and r['timeSec'] == 0 for r in player_changes))):
        player_changes.insert(0, {'playerId': player_id, 'playerName': row['player_name'], 'typeId': 'position_change', 'playing_position': row['position'], 'timeMin': row['time_on'], 'timeSec': 0, 'periodId': 1})
    player_changes.sort(key=lambda r: (r['periodId'], r['timeMin'], r['timeSec']))
    change_times = [r['timeMin'] + r['timeSec'] / 60 for r in player_changes]
    end_min = row['time_off']
    change_times.append(end_min)
    for i in range(min(5, len(change_times) - 1)):
        pos_col = f'position{i + 1}'
        mins_col = f'position{i + 1}mins'
        starting_lineups.at[idx, pos_col] = player_changes[i]['playing_position']
        starting_lineups.at[idx, mins_col] = round(change_times[i + 1] - change_times[i], 1)
df = df.sort_values(by=['periodId', 'timeMin', 'timeSec']).reset_index(drop=True)
from collections import defaultdict
from datetime import timedelta
player_changes = defaultdict(list)
for row in position_change_rows:
    pid = row['playerId']
    player_changes[pid].append({'timeMin': row['timeMin'], 'timeSec': row['timeSec'], 'periodId': row['periodId'], 'position': row['playing_position']})
for pid in player_changes:
    player_changes[pid].sort(key=lambda x: (x['periodId'], x['timeMin'], x['timeSec']))
for pid, changes in player_changes.items():
    player_mask = df['playerId'] == pid
    player_df = df[player_mask]
    initial_pos = starting_lineups[starting_lineups['player_id'] == pid]['position']
    if initial_pos.empty or pd.isna(initial_pos.iloc[0]):
        continue
    initial_pos = initial_pos.iloc[0]
    first_change = changes[0]
    condition = player_mask & ((df['periodId'] < first_change['periodId']) | (df['periodId'] == first_change['periodId']) & ((df['timeMin'] < first_change['timeMin']) | (df['timeMin'] == first_change['timeMin']) & (df['timeSec'] < first_change['timeSec'])))
    df.loc[condition, 'playing_position'] = initial_pos
    for i in range(1, len(changes)):
        prev = changes[i - 1]
        curr = changes[i]
        condition = player_mask & ((df['periodId'] > prev['periodId']) | (df['periodId'] == prev['periodId']) & ((df['timeMin'] > prev['timeMin']) | (df['timeMin'] == prev['timeMin']) & (df['timeSec'] >= prev['timeSec']))) & ((df['periodId'] < curr['periodId']) | (df['periodId'] == curr['periodId']) & ((df['timeMin'] < curr['timeMin']) | (df['timeMin'] == curr['timeMin']) & (df['timeSec'] < curr['timeSec'])))
        df.loc[condition, 'playing_position'] = prev['position']
    last = changes[-1]
    condition = player_mask & ((df['periodId'] > last['periodId']) | (df['periodId'] == last['periodId']) & ((df['timeMin'] > last['timeMin']) | (df['timeMin'] == last['timeMin']) & (df['timeSec'] >= last['timeSec'])))
    df.loc[condition, 'playing_position'] = last['position']
import pandas as pd
import numpy as np
Events = pd.read_excel(__import__('pathlib').Path(__file__).resolve().parent / 'Excel Files/Opta Events.xlsx')
qualifiers = pd.read_excel(__import__('pathlib').Path(__file__).resolve().parent / 'Excel Files/Opta Qualifiers.xlsx')
event_map = dict(zip(Events['Code'], Events['Event']))
event_map.update({74: 'Defensive Duel', 83: 'Defensive Duel', '74': 'Defensive Duel', '83': 'Defensive Duel'})
qualifier_map = dict(zip(qualifiers['Code'], qualifiers['Qualifier']))
df = df.iloc[:, :100]
if 'assist' not in df.columns:
    df['assist'] = 0
df['typeId'] = df['typeId'].map(event_map).fillna(df['typeId'])
import re
player_name_lookup = starting_lineups[['player_id', 'player_name']].dropna(subset=['player_id']).drop_duplicates().copy()
player_name_lookup['player_id'] = player_name_lookup['player_id'].astype(str).str.strip()
player_name_lookup = player_name_lookup.set_index('player_id')['player_name'].to_dict()
qualifier_slots = sorted({int(m.group(1)) for col in df.columns for m in [re.match('qualifier/(\\d+)/qualifierId', col)] if m})
offside_rows = []
for idx, row in df.iterrows():
    for i in qualifier_slots:
        qid_col = f'qualifier/{i}/qualifierId'
        val_col = f'qualifier/{i}/value'
        if qid_col not in df.columns:
            continue
        qid = row.get(qid_col, pd.NA)
        if pd.isna(qid):
            continue
        try:
            is_offside = float(qid) == 7.0
        except:
            is_offside = str(qid).strip().lower() == 'offside'
        if not is_offside:
            continue
        offside_player_id = row.get(val_col, pd.NA)
        if pd.isna(offside_player_id):
            continue
        offside_player_id = str(offside_player_id).strip()
        if offside_player_id.endswith('.0'):
            offside_player_id = offside_player_id[:-2]
        offside_rows.append({'id': row.get('id', pd.NA), 'eventId': f"{row.get('eventId', idx)}_offside", 'typeId': 'Offside', 'periodId': row.get('periodId', pd.NA), 'timeMin': row.get('timeMin', pd.NA), 'timeSec': row.get('timeSec', pd.NA), 'contestantId': row.get('contestantId', pd.NA), 'outcome': 'Successful', 'x': row.get('end_x', pd.NA), 'y': row.get('end_y', pd.NA), 'timeStamp': row.get('timeStamp', pd.NA), 'lastModified': row.get('lastModified', pd.NA), 'playerId': offside_player_id, 'playerName': player_name_lookup.get(offside_player_id, pd.NA), 'keyPass': 0})
        break
if offside_rows:
    offside_df = pd.DataFrame(offside_rows)
    for col in df.columns:
        if col not in offside_df.columns:
            offside_df[col] = pd.NA
    offside_df = offside_df[df.columns]
    df = pd.concat([df, offside_df], ignore_index=True, sort=False)
pass
pass
qualifier_columns_requested = [f'qualifier/{i}/qualifierId' for i in range(16)]
existing_qualifier_cols = [c for c in qualifier_columns_requested if c in df.columns]
qualifier_columns = existing_qualifier_cols
if existing_qualifier_cols:
    df[existing_qualifier_cols] = df[existing_qualifier_cols].map(lambda x: qualifier_map.get(x, x))
df['outcome'] = df['outcome'].replace({0: 'Unsuccessful', 1: 'Successful'})
df.rename(columns={'contestantId': 'team_name'}, inplace=True)
df = df.merge(teamdata[['id', 'name']], how='left', left_on='team_name', right_on='id')
df.drop(columns=['team_name', 'id_y'], inplace=True)
df.rename(columns={'name': 'team_name', 'id_x': 'id'}, inplace=True)
import re
if 'end_x' not in df.columns:
    df['end_x'] = pd.NA
if 'end_y' not in df.columns:
    df['end_y'] = pd.NA
qualifier_indices = [int(match.group(1)) for col in df.columns if (match := re.match('qualifier/(\\d+)/', col))]
max_index = max(qualifier_indices, default=0)
for i in range(max_index + 1):
    value_col = f'qualifier/{i}/value'
    id_col = f'qualifier/{i}/qualifierId'
    if value_col not in df.columns or id_col not in df.columns:
        continue
    end_x_mask = df[id_col] == 'Pass End X'
    end_y_mask = df[id_col] == 'Pass End Y'
    df.loc[end_x_mask, 'end_x'] = pd.to_numeric(df.loc[end_x_mask, value_col], errors='coerce')
    df.loc[end_y_mask, 'end_y'] = pd.to_numeric(df.loc[end_y_mask, value_col], errors='coerce')
df['end_x'] = pd.to_numeric(df['end_x'], errors='coerce').fillna(0)
df['end_y'] = pd.to_numeric(df['end_y'], errors='coerce').fillna(0)
df['throwin'] = df[qualifier_columns].apply(lambda row: 'Throw-in' in row.dropna().values, axis=1).astype(int)
df['corner'] = df[qualifier_columns].apply(lambda row: 'Corner taken' in row.dropna().values, axis=1).astype(int)
df['freekick'] = df[qualifier_columns].apply(lambda row: 'Free-kick taken' in row.dropna().values, axis=1).astype(int)
df['goalkick'] = df[qualifier_columns].apply(lambda row: 'Goal Kick' in row.dropna().values, axis=1).astype(int)
df['cross'] = df[qualifier_columns].apply(lambda row: 'Cross' in row.dropna().values, axis=1).astype(int)
df['longball'] = df[qualifier_columns].apply(lambda row: 'Long ball' in row.dropna().values, axis=1).astype(int)
df['switch'] = df[qualifier_columns].apply(lambda row: 'Switch of play' in row.dropna().values, axis=1).astype(int)
df['launch'] = df[qualifier_columns].apply(lambda row: 'Launch' in row.dropna().values, axis=1).astype(int)
df['secondassist'] = df[qualifier_columns].apply(lambda row: '2nd assist' in row.dropna().values, axis=1).astype(int)
df['head'] = df[qualifier_columns].apply(lambda row: 'Head' in row.dropna().values, axis=1).astype(int)
df['leftfoot'] = df[qualifier_columns].apply(lambda row: 'Left footed' in row.dropna().values, axis=1).astype(int)
df['rightfoot'] = df[qualifier_columns].apply(lambda row: 'Right footed' in row.dropna().values, axis=1).astype(int)
df['otherbody'] = df[qualifier_columns].apply(lambda row: 'Other body part' in row.dropna().values, axis=1).astype(int)
df['fastbreakshot'] = df[qualifier_columns].apply(lambda row: 'Fast break' in row.dropna().values, axis=1).astype(int)
df['setpieceshot'] = df[qualifier_columns].apply(lambda row: 'Set piece' in row.dropna().values, axis=1).astype(int)
df['freekickshot'] = df[qualifier_columns].apply(lambda row: 'Free kick' in row.dropna().values, axis=1).astype(int)
df['cornershot'] = df[qualifier_columns].apply(lambda row: 'From corner' in row.dropna().values, axis=1).astype(int)
df['throwinshot'] = df[qualifier_columns].apply(lambda row: 'Throw-in set piece' in row.dropna().values, axis=1).astype(int)
df['dfreekickshot'] = df[qualifier_columns].apply(lambda row: 'Direct free' in row.dropna().values, axis=1).astype(int)
df['penaltyshot'] = df[qualifier_columns].apply(lambda row: 'Penalty' in row.dropna().values, axis=1).astype(int)
df['owngoal'] = df.iloc[:, 16:].apply(lambda row: any((isinstance(val, str) and val.strip().lower() in ['own goal', 'own_goal'] for val in row.values)), axis=1).astype(int)
df.loc[df['owngoal'] == 1, 'typeId'] = 'Own Goal'
raw_end_x = pd.to_numeric(df['end_x'], errors='coerce')
raw_end_y = pd.to_numeric(df['end_y'], errors='coerce')
df['_ball_out_of_play'] = raw_end_x.le(0) | raw_end_x.ge(100) | raw_end_y.le(0) | raw_end_y.ge(100)
df['bigchance'] = df[qualifier_columns].apply(lambda row: 'Big chance' in row.dropna().values, axis=1).astype(int)
df['hitwoodwork'] = df[qualifier_columns].apply(lambda row: 'Hit woodwork' in row.dropna().values, axis=1).astype(int)
df['lastman'] = df[qualifier_columns].apply(lambda row: 'Last line' in row.dropna().values, axis=1).astype(int)
df['errorshot'] = df[qualifier_columns].apply(lambda row: 'Leading to attempt' in row.dropna().values, axis=1).astype(int)
df['errorgoal'] = df[qualifier_columns].apply(lambda row: 'Leading to goal' in row.dropna().values, axis=1).astype(int)
df['yellowcard'] = df[qualifier_columns].apply(lambda row: 'Yellow Card' in row.dropna().values, axis=1).astype(int)
df['yellowcard2'] = df[qualifier_columns].apply(lambda row: 'Second yellow' in row.dropna().values, axis=1).astype(int)
df['redcard'] = df[qualifier_columns].apply(lambda row: 'Red card' in row.dropna().values, axis=1).astype(int)
df['shotblocked'] = df[qualifier_columns].apply(lambda row: 'Blocked' in row.dropna().values, axis=1).astype(int)
df = df.loc[df['typeId'] != 40]
df = df.loc[df['typeId'] != 'Deleted event']
values_to_remove = ['Collection End', 'End', 'Team set up', 'Start']
df = df[~df['typeId'].isin(values_to_remove)]
columns_to_keep = ['id', 'eventId', 'typeId', 'periodId', 'timeMin', 'timeSec', 'team_name', 'outcome', 'x', 'y', 'end_x', 'end_y', 'playerName', 'playing_position', 'keyPass', 'secondassist', 'assist', 'throwin', 'corner', 'freekick', 'goalkick', 'cross', 'longball', 'switch', 'launch', 'head', 'leftfoot', 'rightfoot', 'otherbody', 'fastbreakshot', 'setpieceshot', 'freekickshot', 'cornershot', 'throwinshot', 'dfreekickshot', 'penaltyshot', 'owngoal', 'bigchance', 'hitwoodwork', 'lastman', 'errorshot', 'errorgoal', 'yellowcard', 'yellowcard2', 'redcard', 'shotblocked', '_ball_out_of_play']
df = df[columns_to_keep]
df['end_x'] = pd.to_numeric(df['end_x'], errors='coerce').clip(0, 100)
df['end_y'] = pd.to_numeric(df['end_y'], errors='coerce').clip(0, 100)
if globals().get('_live_no_xg', False):
    # Match the endpoint normalization used by the regular No XG notebook.
    for axis in ['end_x', 'end_y']:
        low, high = df[axis].min(), df[axis].max()
        if pd.notna(high) and high > low:
            df[axis] = (df[axis] - low) / (high - low) * 100
df.loc[df['owngoal'] == 1, 'typeId'] = 'Own Goal'
df['next_player'] = df['playerName'].shift(-1)
df['next_team'] = df['team_name'].shift(-1)
df['next_position'] = df['playing_position'].shift(-1)
df['pass_recipient'] = np.where((df['typeId'] == 'Pass') & (df['outcome'] == 'Successful') & (df['team_name'] == df['next_team']), df['next_player'], np.nan)
df['pass_recipient_position'] = np.where((df['typeId'] == 'Pass') & (df['outcome'] == 'Successful') & (df['team_name'] == df['next_team']), df['next_position'], np.nan)
df = df[df['typeId'].notna()].reset_index(drop=True)
mask = df['typeId'] == 'Ball recovery'
df.loc[mask, 'end_x'] = df.loc[mask, 'x']
df.loc[mask, 'end_y'] = df.loc[mask, 'y']
df.loc[df['typeId'] == 'Offside', 'playing_position'] = df.groupby('playerName')['playing_position'].ffill().loc[df['typeId'] == 'Offside']
df['event_time'] = df['timeMin'] * 60 + df['timeSec']
df = df.sort_values(by=['event_time', 'id']).reset_index(drop=True)
carry_rows = []
for i in range(len(df) - 1):
    current = df.iloc[i]
    current_team = current['team_name']
    current_player = current['playerName']
    end_x = current['end_x']
    end_y = current['end_y']
    current_type = current['typeId']
    current_outcome = current['outcome']
    is_pass = current_type == 'Pass' and current_outcome == 'Successful'
    is_recovery = current_type == 'Ball recovery' and current_outcome == 'Successful'
    is_interception = current_type == 'Interception'
    is_take_on = current_type == 'Take on' and current_outcome == 'Successful'
    if not (is_pass or is_recovery or is_interception or is_take_on):
        continue
    for j in range(i + 1, len(df)):
        next_row = df.iloc[j]
        if next_row['team_name'] != current_team:
            continue
        if end_x == next_row['x'] and end_y == next_row['y']:
            break
        if next_row['typeId'] == 'Aerial':
            break
        if (is_recovery or is_interception or is_take_on) and current_player != next_row['playerName']:
            break
        carry_row = current.copy()
        carry_row['id'] = current['id'] + 0.5
        carry_row['eventId'] = current['eventId'] + 0.5
        carry_row['typeId'] = 'Carry'
        carry_row['x'] = end_x
        carry_row['y'] = end_y
        carry_row['end_x'] = next_row['x']
        carry_row['end_y'] = next_row['y']
        carry_row['playerName'] = next_row['playerName']
        carry_row['playing_position'] = next_row['playing_position']
        carry_row['outcome'] = 'Successful'
        carry_rows.append(carry_row)
        break
df = pd.concat([df, pd.DataFrame(carry_rows)], ignore_index=True)
df = df.sort_values(by=['timeMin', 'timeSec', 'periodId']).reset_index(drop=True)
df = df[~((df['typeId'] == 'Carry') & (df['x'] == 0) & (df['y'] == 0))].reset_index(drop=True)
df = df[~((df['typeId'] == 'Carry') & (df['end_x'] == 0) & (df['end_y'] == 0))].reset_index(drop=True)
to_delete = []
for i in range(len(df) - 1):
    if df.iloc[i]['typeId'] == 'Carry' and df.iloc[i + 1]['typeId'] == 'Ball recovery':
        to_delete.append(i)
df = df.drop(index=to_delete).reset_index(drop=True)
df.loc[df['typeId'] == 'Carry', 'pass_recipient'] = np.nan
carry_filter = ~((df['typeId'] == 'Carry') & ((df['x'] - df['end_x']).abs() < 1.5) & ((df['y'] - df['end_y']).abs() < 2.5))
df = df[carry_filter]
df.loc[df['typeId'] == 'Carry', ['keyPass', 'assist']] = np.nan
xT = np.array([[0.00638303, 0.00779616, 0.00844854, 0.00977659, 0.01126267, 0.01248344, 0.01473596, 0.0174506, 0.02122129, 0.02756312, 0.03485072, 0.0379259], [0.00750072, 0.00878589, 0.00942382, 0.0105949, 0.01214719, 0.0138454, 0.01611813, 0.01870347, 0.02401521, 0.02953272, 0.04066992, 0.04647721], [0.0088799, 0.00977745, 0.01001304, 0.01110462, 0.01269174, 0.01429128, 0.01685596, 0.01935132, 0.0241224, 0.02855202, 0.05491138, 0.06442595], [0.00941056, 0.01082722, 0.01016549, 0.01132376, 0.01262646, 0.01484598, 0.01689528, 0.0199707, 0.02385149, 0.03511326, 0.10805102, 0.25745362], [0.00941056, 0.01082722, 0.01016549, 0.01132376, 0.01262646, 0.01484598, 0.01689528, 0.0199707, 0.02385149, 0.03511326, 0.10805102, 0.25745362], [0.0088799, 0.00977745, 0.01001304, 0.01110462, 0.01269174, 0.01429128, 0.01685596, 0.01935132, 0.0241224, 0.02855202, 0.05491138, 0.06442595], [0.00750072, 0.00878589, 0.00942382, 0.0105949, 0.01214719, 0.0138454, 0.01611813, 0.01870347, 0.02401521, 0.02953272, 0.04066992, 0.04647721], [0.00638303, 0.00779616, 0.00844854, 0.00977659, 0.01126267, 0.01248344, 0.01473596, 0.0174506, 0.02122129, 0.02756312, 0.03485072, 0.0379259]])
xT_rows, xT_cols = xT.shape
x_bins = np.linspace(0, 100, xT_cols + 1)
y_bins = np.linspace(0, 100, xT_rows + 1)
df['x1_bin'] = pd.cut(df['x'], bins=x_bins, labels=False)
df['y1_bin'] = pd.cut(df['y'], bins=y_bins, labels=False)
df['x2_bin'] = pd.cut(df['end_x'], bins=x_bins, labels=False)
df['y2_bin'] = pd.cut(df['end_y'], bins=y_bins, labels=False)
passingthreat = df.loc[(df['typeId'] == 'Pass') & (df['outcome'] == 'Successful')]
passingthreat = passingthreat.loc[passingthreat['x'] < 99.49]
passingthreat = passingthreat.dropna(subset=['x1_bin', 'y1_bin', 'x2_bin', 'y2_bin'])
passingthreat['x1_bin'] = passingthreat['x1_bin'].astype(int)
passingthreat['y1_bin'] = passingthreat['y1_bin'].astype(int)
passingthreat['x2_bin'] = passingthreat['x2_bin'].astype(int)
passingthreat['y2_bin'] = passingthreat['y2_bin'].astype(int)
passingthreat['xT_value'] = passingthreat.apply(lambda row: _live_grid_value(xT, row['y2_bin'], row['x2_bin']) - _live_grid_value(xT, row['y1_bin'], row['x1_bin']), axis=1)
passthreattotal = passingthreat.groupby('playerName')['xT_value'].sum().reset_index()
carrythreat = df.loc[df['typeId'] == 'Carry']
carrythreat['y_diff'] = carrythreat['y'] - carrythreat['end_y']
carrythreat = carrythreat.dropna(subset=['x1_bin', 'y1_bin', 'x2_bin', 'y2_bin'])
carrythreat['x1_bin'] = carrythreat['x1_bin'].astype(int)
carrythreat['y1_bin'] = carrythreat['y1_bin'].astype(int)
carrythreat['x2_bin'] = carrythreat['x2_bin'].astype(int)
carrythreat['y2_bin'] = carrythreat['y2_bin'].astype(int)
carrythreat['xT_value'] = carrythreat.apply(lambda row: _live_grid_value(xT, row['y2_bin'], row['x2_bin']) - _live_grid_value(xT, row['y1_bin'], row['x1_bin']), axis=1)
carrythreattotal = carrythreat.groupby('playerName')['xT_value'].sum().reset_index()
df['id'] = df['id'].astype(str)
passingthreat['id'] = passingthreat['id'].astype(str)
df = df.merge(passingthreat[['id', 'xT_value']], on='id', how='left')
carrythreat['id'] = carrythreat['id'].astype(str)
carrythreat['eventId'] = carrythreat['eventId'].astype(str)
df['id'] = df['id'].astype(str)
df['eventId'] = df['eventId'].astype(str)
df = df.merge(carrythreat[['id', 'eventId', 'xT_value']], on=['id', 'eventId'], how='left', suffixes=('', '_carry'))
df['xT_value'] = df['xT_value'].combine_first(df['xT_value_carry'])
df.drop(columns=['xT_value_carry'], inplace=True)
df['assist_xt'] = 0.0
df.loc[df['keyPass'] == 1, 'assist_xt'] = 0.1
df.loc[df['assist'] == 1, 'assist_xt'] = 0.6
shotassisttotal = df.groupby('playerName', as_index=False)['assist_xt'].sum()
shotassisttotal.rename(columns={'assist_xt': 'xT_value'}, inplace=True)
shotassisttotal = shotassisttotal.loc[shotassisttotal['xT_value'] > 0]
teamname = teamdata.iloc[0, 1]
opponentname = teamdata.iloc[1, 1]
RPxT = np.array([[0.00638303, 0.00779616, 0.00844854, 0.00977659, 0.01126267, 0.01248344, 0.01473596, 0.0174506, 0.02122129, 0.02756312, 0.03485072, 0.0379259], [0.00750072, 0.00878589, 0.00942382, 0.0105949, 0.01214719, 0.0138454, 0.01611813, 0.01870347, 0.02401521, 0.02953272, 0.04066992, 0.04647721], [0.0088799, 0.00977745, 0.01001304, 0.01110462, 0.01269174, 0.01429128, 0.01685596, 0.01935132, 0.0241224, 0.02855202, 0.05491138, 0.06442595], [0.00941056, 0.01082722, 0.01016549, 0.01132376, 0.01262646, 0.01484598, 0.01689528, 0.0199707, 0.02385149, 0.03511326, 0.10805102, 0.25745362], [0.00941056, 0.01082722, 0.01016549, 0.01132376, 0.01262646, 0.01484598, 0.01689528, 0.0199707, 0.02385149, 0.03511326, 0.10805102, 0.25745362], [0.0088799, 0.00977745, 0.01001304, 0.01110462, 0.01269174, 0.01429128, 0.01685596, 0.01935132, 0.0241224, 0.02855202, 0.05491138, 0.06442595], [0.00750072, 0.00878589, 0.00942382, 0.0105949, 0.01214719, 0.0138454, 0.01611813, 0.01870347, 0.02401521, 0.02953272, 0.04066992, 0.04647721], [0.00638303, 0.00779616, 0.00844854, 0.00977659, 0.01126267, 0.01248344, 0.01473596, 0.0174506, 0.02122129, 0.02756312, 0.03485072, 0.0379259]])
RPxT_rows, RPxT_cols = RPxT.shape
distinct_teams = df['team_name'].dropna().unique()
teamsinmatch = teamdata[teamdata['name'].isin(distinct_teams)].copy()
teamsinmatch.rename(columns={'name': 'team'}, inplace=True)
teamsinmatch = teamsinmatch[['id', 'team']]
teamname = teamsinmatch.iloc[0, 1]
recthreattest = df.loc[df['team_name'] == teamname]
recthreattest = recthreattest.loc[recthreattest['end_x'] > 50]
receivedpasshome = recthreattest[(recthreattest['typeId'] == 'Pass') & (recthreattest['outcome'] == 'Successful')]
receivedpasshome['recipient'] = recthreattest['playerName'].shift(-1)
receivedpasshome['x2_bin'] = pd.cut(receivedpasshome['end_x'], bins=np.linspace(0, 100, RPxT_cols + 1), labels=False, include_lowest=True)
receivedpasshome['y2_bin'] = pd.cut(receivedpasshome['end_y'], bins=np.linspace(0, 100, RPxT_rows + 1), labels=False, include_lowest=True)
receivedpasshome['xT_value'] = receivedpasshome[['x2_bin', 'y2_bin']].apply(lambda x: _live_grid_value(RPxT, x.iloc[1], x.iloc[0]), axis=1)
recpassh = receivedpasshome.groupby('recipient')['xT_value'].sum().reset_index()
recpassh.rename(columns={'recipient': 'playerName'}, inplace=True)
recthreattest = df.loc[df['team_name'] != teamname]
recthreattest = recthreattest.loc[recthreattest['end_x'] > 50]
receivedpassaway = recthreattest[(recthreattest['typeId'] == 'Pass') & (recthreattest['outcome'] == 'Successful')]
receivedpassaway['recipient'] = recthreattest['playerName'].shift(-1)
receivedpassaway['x2_bin'] = pd.cut(receivedpassaway['end_x'], bins=np.linspace(0, 100, RPxT_cols + 1), labels=False, include_lowest=True)
receivedpassaway['y2_bin'] = pd.cut(receivedpassaway['end_y'], bins=np.linspace(0, 100, RPxT_rows + 1), labels=False, include_lowest=True)
receivedpassaway['xT_value'] = receivedpassaway[['x2_bin', 'y2_bin']].apply(lambda x: _live_grid_value(RPxT, x.iloc[1], x.iloc[0]), axis=1)
recpassa = receivedpassaway.groupby('recipient')['xT_value'].sum().reset_index()
recpassa.rename(columns={'recipient': 'playerName'}, inplace=True)
recpassa
receivedpasses = pd.concat([recpassh, recpassa], ignore_index=True)
receivedpassestotal = receivedpasses.groupby('playerName')['xT_value'].sum().reset_index()
RPxT = np.array([[0.00638303, 0.00779616, 0.00844854, 0.00977659, 0.01126267, 0.01248344, 0.01473596, 0.0174506, 0.02122129, 0.02756312, 0.03485072, 0.0379259], [0.00750072, 0.00878589, 0.00942382, 0.0105949, 0.01214719, 0.0138454, 0.01611813, 0.01870347, 0.02401521, 0.02953272, 0.04066992, 0.04647721], [0.0088799, 0.00977745, 0.01001304, 0.01110462, 0.01269174, 0.01429128, 0.01685596, 0.01935132, 0.0241224, 0.02855202, 0.05491138, 0.06442595], [0.00941056, 0.01082722, 0.01016549, 0.01132376, 0.01262646, 0.01484598, 0.01689528, 0.0199707, 0.02385149, 0.03511326, 0.10805102, 0.25745362], [0.00941056, 0.01082722, 0.01016549, 0.01132376, 0.01262646, 0.01484598, 0.01689528, 0.0199707, 0.02385149, 0.03511326, 0.10805102, 0.25745362], [0.0088799, 0.00977745, 0.01001304, 0.01110462, 0.01269174, 0.01429128, 0.01685596, 0.01935132, 0.0241224, 0.02855202, 0.05491138, 0.06442595], [0.00750072, 0.00878589, 0.00942382, 0.0105949, 0.01214719, 0.0138454, 0.01611813, 0.01870347, 0.02401521, 0.02953272, 0.04066992, 0.04647721], [0.00638303, 0.00779616, 0.00844854, 0.00977659, 0.01126267, 0.01248344, 0.01473596, 0.0174506, 0.02122129, 0.02756312, 0.03485072, 0.0379259]])
RPxT_rows, RPxT_cols = RPxT.shape
recthreattest = df.loc[df['team_name'] == teamname]
recthreattest = recthreattest.loc[recthreattest['end_x'] > 50]
receivedpasshome = recthreattest[(recthreattest['typeId'] == 'Pass') & (recthreattest['outcome'] == 'Successful')]
receivedpasshome['x2_bin'] = pd.cut(receivedpasshome['end_x'], bins=np.linspace(0, 100, RPxT_cols + 1), labels=False, include_lowest=True)
receivedpasshome['y2_bin'] = pd.cut(receivedpasshome['end_y'], bins=np.linspace(0, 100, RPxT_rows + 1), labels=False, include_lowest=True)
receivedpasshome['xT_value'] = receivedpasshome[['x2_bin', 'y2_bin']].apply(lambda x: _live_grid_value(RPxT, x.iloc[1], x.iloc[0]), axis=1)
recpassh = receivedpasshome.groupby('pass_recipient')['xT_value'].sum().reset_index()
recpassh.rename(columns={'pass_recipient': 'playerName'}, inplace=True)
recthreattest = df.loc[df['team_name'] != teamname]
recthreattest = recthreattest.loc[recthreattest['end_x'] > 50]
receivedpassaway = recthreattest[(recthreattest['typeId'] == 'Pass') & (recthreattest['outcome'] == 'Successful')]
receivedpassaway['x2_bin'] = pd.cut(receivedpassaway['end_x'], bins=np.linspace(0, 100, RPxT_cols + 1), labels=False, include_lowest=True)
receivedpassaway['y2_bin'] = pd.cut(receivedpassaway['end_y'], bins=np.linspace(0, 100, RPxT_rows + 1), labels=False, include_lowest=True)
receivedpassaway['xT_value'] = receivedpassaway[['x2_bin', 'y2_bin']].apply(lambda x: _live_grid_value(RPxT, x.iloc[1], x.iloc[0]), axis=1)
recpassa = receivedpassaway.groupby('pass_recipient')['xT_value'].sum().reset_index()
recpassa.rename(columns={'pass_recipient': 'playerName'}, inplace=True)
recpassa
receivedpasses = pd.concat([recpassh, recpassa], ignore_index=True)
receivedpassestotal = receivedpasses.groupby('playerName')['xT_value'].sum().reset_index()
eventstoinclude = ['Tackle', 'Defensive Duel', 'Aerial', 'Challenge', 'Interception', 'Blocked Pass', 'Clearance', 'Ball recovery']
df_events_def = df[df['typeId'].isin(eventstoinclude)]
xT = np.array([[0.00638303, 0.00779616, 0.00844854, 0.00977659, 0.01126267, 0.01248344, 0.01473596, 0.0174506, 0.02122129, 0.02756312, 0.03485072, 0.0379259], [0.00750072, 0.00878589, 0.00942382, 0.0105949, 0.01214719, 0.0138454, 0.01611813, 0.01870347, 0.02401521, 0.02953272, 0.04066992, 0.04647721], [0.0088799, 0.00977745, 0.01001304, 0.01110462, 0.01269174, 0.01429128, 0.01685596, 0.01935132, 0.0241224, 0.02855202, 0.05491138, 0.06442595], [0.00941056, 0.01082722, 0.01016549, 0.01132376, 0.01262646, 0.01484598, 0.01689528, 0.0199707, 0.02385149, 0.03511326, 0.10805102, 0.25745362], [0.00941056, 0.01082722, 0.01016549, 0.01132376, 0.01262646, 0.01484598, 0.01689528, 0.0199707, 0.02385149, 0.03511326, 0.10805102, 0.25745362], [0.0088799, 0.00977745, 0.01001304, 0.01110462, 0.01269174, 0.01429128, 0.01685596, 0.01935132, 0.0241224, 0.02855202, 0.05491138, 0.06442595], [0.00750072, 0.00878589, 0.00942382, 0.0105949, 0.01214719, 0.0138454, 0.01611813, 0.01870347, 0.02401521, 0.02953272, 0.04066992, 0.04647721], [0.00638303, 0.00779616, 0.00844854, 0.00977659, 0.01126267, 0.01248344, 0.01473596, 0.0174506, 0.02122129, 0.02756312, 0.03485072, 0.0379259]])
xT_rows, xT_cols = xT.shape
df_events_def['x'] = 105 - df_events_def['x']
df_events_def['end_x'] = 105 - df_events_def['end_x']
df_events_def['x1_bin'] = pd.cut(df_events_def['x'], bins=np.linspace(0, 100, xT_cols + 1), labels=False, include_lowest=True)
df_events_def['y1_bin'] = pd.cut(df_events_def['y'], bins=np.linspace(0, 100, xT_rows + 1), labels=False, include_lowest=True)
df_events_def['xT_value'] = df_events_def[['x1_bin', 'y1_bin']].apply(lambda x: _live_grid_value(xT, x.iloc[1], x.iloc[0]), axis=1)
df_events_def['xT_value'] = df_events_def.apply(lambda row: row['xT_value'] * -1 if row['outcome'] == 'Unsuccessful' else row['xT_value'], axis=1)
defthreattotal = df_events_def.groupby('playerName')['xT_value'].sum().reset_index()
df = df.merge(df_events_def[['id', 'xT_value']], on='id', how='left', suffixes=('', '_carry'))
df['xT_value'] = df['xT_value'].combine_first(df['xT_value_carry'])
df.drop(columns=['xT_value_carry'], inplace=True)
IPxT = np.array([[0.01, 0.012, 0.013, 0.015, 0.017, 0.018, 0.02, 0.022, 0.025, 0.02756312, 0.03485072, 0.0379259], [0.012, 0.01378589, 0.01442382, 0.0155949, 0.01714719, 0.0188454, 0.02111813, 0.02370347, 0.02701521, 0.02953272, 0.04066992, 0.04647721], [0.01388799, 0.01477745, 0.01501304, 0.01610462, 0.01869174, 0.02, 0.02285596, 0.02535132, 0.031224, 0.0455202, 0.05491138, 0.06442595], [0.02941056, 0.03082722, 0.03216549, 0.03432376, 0.0462646, 0.04784598, 0.0589528, 0.0699707, 0.07385149, 0.08511326, 0.10805102, 0.25745362], [0.02941056, 0.03082722, 0.03216549, 0.03432376, 0.0462646, 0.04784598, 0.0589528, 0.0699707, 0.07385149, 0.08511326, 0.10805102, 0.25745362], [0.01388799, 0.01477745, 0.01501304, 0.01610462, 0.01869174, 0.02, 0.02285596, 0.02535132, 0.031224, 0.0455202, 0.05491138, 0.06442595], [0.012, 0.01378589, 0.01442382, 0.0155949, 0.01714719, 0.0188454, 0.02111813, 0.02370347, 0.02701521, 0.02953272, 0.04066992, 0.04647721], [0.01, 0.012, 0.013, 0.015, 0.017, 0.018, 0.02, 0.022, 0.025, 0.02756312, 0.03485072, 0.0379259]])
IPxT_rows, IPxT_cols = IPxT.shape
incompletepasses = df.loc[(df['typeId'] == 'Pass') & (df['outcome'] == 'Unsuccessful')]
incompletepasses['x'] = 105 - incompletepasses['x']
incompletepasses['end_x'] = 105 - incompletepasses['end_x']
incompletepasses['x1_bin'] = pd.cut(incompletepasses['x'], bins=np.linspace(0, 100, IPxT_cols + 1), labels=False, include_lowest=True)
incompletepasses['y1_bin'] = pd.cut(incompletepasses['y'], bins=np.linspace(0, 100, IPxT_rows + 1), labels=False, include_lowest=True)
incompletepasses['xT_value'] = incompletepasses[['x1_bin', 'y1_bin']].apply(lambda x: _live_grid_value(IPxT, x.iloc[1], x.iloc[0]), axis=1)
incompletepasses['xT_value'] = incompletepasses['xT_value'] * -1
incomppasstotal = incompletepasses.groupby('playerName')['xT_value'].sum().reset_index()
df = df.merge(incompletepasses[['id', 'xT_value']], on='id', how='left', suffixes=('', '_carry'))
df['xT_value'] = df['xT_value'].combine_first(df['xT_value_carry'])
df.drop(columns=['xT_value_carry'], inplace=True)
for card_column in ['yellowcard', 'yellowcard2', 'redcard']:
    df[card_column] = pd.to_numeric(df[card_column], errors='coerce').fillna(0)
sending_off_mask = df['yellowcard2'].eq(1) | df['redcard'].eq(1)
yellow_card_mask = df['yellowcard'].eq(1) & ~sending_off_mask
card_event_mask = yellow_card_mask | sending_off_mask
df['card_value'] = 0.0
df.loc[yellow_card_mask, 'card_value'] = -0.1
df.loc[sending_off_mask, 'card_value'] = -0.6
df.loc[card_event_mask, 'xT_value'] = df.loc[card_event_mask, 'card_value']
cards_df = df.loc[card_event_mask].groupby('playerName', as_index=False)['card_value'].sum()
cards_df = cards_df.rename(columns={'card_value': 'xT_value'})
df = df[df['id'].notna()].copy()
df['id'] = df['id'].astype(str).str.replace('.0', '', regex=False).str.replace('.5', '', regex=False).astype('int64')
shots = shots[shots['id'].notna()].copy()
shots['id'] = shots['id'].astype(str).str.replace('.0', '', regex=False).astype('int64')
per_match_shot_columns = ['id', 'eventType', 'isBlocked', 'isOnTarget', 'expectedGoals', 'expectedGoalsOnTarget', 'shotType', 'situation', 'isOwnGoal', 'isSavedOffLine', 'onGoalShot']
available_shot_columns = [column for column in per_match_shot_columns if column in shots.columns]
required_xg_columns = {'id', 'eventType', 'expectedGoals', 'expectedGoalsOnTarget', 'situation'}
missing_xg_columns = required_xg_columns - set(available_shot_columns)
if missing_xg_columns:
    raise ValueError(f'FotMob shot data is missing required columns: {sorted(missing_xg_columns)}')
shots_subset = shots[available_shot_columns].drop_duplicates(subset=['id'], keep='first')
df = df.merge(shots_subset, how='left', on='id')
event_keys = [column for column in ['id', 'eventId'] if column in df.columns]
if event_keys:
    real_event = df[event_keys].notna().all(axis=1)
    df = pd.concat([df.loc[real_event].drop_duplicates(subset=event_keys, keep='first'), df.loc[~real_event]]).sort_index().reset_index(drop=True)
shotsmerged = df
shotstaken = shotsmerged.loc[shotsmerged['typeId'].isin(['Miss', 'Attempt Saved', 'Goal', 'Post'])].copy()
shotstaken = shotstaken.loc[shotstaken['periodId'] < 5].copy()
shotstaken['xT_value'] = np.where((shotstaken['situation'] == 'Penalty') & (shotstaken['eventType'] != 'Goal'), -0.78, np.where(shotstaken['eventType'] == 'Goal', 0.95, shotstaken['expectedGoalsOnTarget'] - shotstaken['expectedGoals'] + shotstaken['expectedGoals'] / 2))
shotstakentotal = shotstaken.groupby('playerName')['xT_value'].sum().reset_index()
df = df.merge(shotstaken[['id', 'xT_value']], on='id', how='left', suffixes=('', '_shot'))
df['xT_value'] = df['xT_value'].combine_first(df['xT_value_shot'])
df.drop(columns=['xT_value_shot'], inplace=True)
starting_lineups = starting_lineups.merge(teamdata, left_on='contestant_id', right_on='id', how='left')
starting_lineups.rename(columns={'name': 'team_name'}, inplace=True)
starting_lineups['time_on'] = pd.to_numeric(starting_lineups['time_on'])
starting_lineups['time_off'] = pd.to_numeric(starting_lineups['time_off'])
goal_events = df[df['typeId'].isin(['Goal', 'Own Goal'])].copy()
goal_events['minute'] = pd.to_numeric(goal_events['timeMin'], errors='coerce')
team_names = df['team_name'].dropna().unique()
goal_events['team_goal'] = goal_events.apply(lambda row: row['team_name'] if row['typeId'] == 'Goal' else [team for team in team_names if team != row['team_name']][0] if row['typeId'] == 'Own Goal' else None, axis=1)

def get_goals_for_and_against(player_row):
    time_on = player_row['time_on']
    time_off = player_row['time_off']
    player_team = player_row['team_name']
    active_goals = goal_events[(goal_events['minute'] >= time_on) & (goal_events['minute'] <= time_off)]
    goals_for = (active_goals['team_goal'] == player_team).sum()
    goals_against = (active_goals['team_goal'] != player_team).sum()
    return pd.Series({'goals_scored': goals_for, 'goals_conceded': goals_against})
starting_lineups[['goals_scored', 'goals_conceded']] = starting_lineups.apply(get_goals_for_and_against, axis=1)

def calculate_xt_value(row):
    pos = row['position']
    mins = row['minutes_played']
    goals_conceded = row['goals_conceded']
    if any((p in pos for p in ['LB', 'CB', 'RB', 'RWB', 'LWB'])):
        if mins > 60 and goals_conceded == 0:
            return 0.4
        else:
            return goals_conceded * -0.2
    elif 'M' in pos:
        if mins > 60 and goals_conceded == 0:
            return 0.1
        else:
            return goals_conceded * -0.05
    return 0
goal_conceded_rows = []
player_name_map = starting_lineups.set_index('player_id')['player_name'].to_dict()
team_name_map = starting_lineups.set_index('player_id')['team_name'].to_dict()
team_names = df['team_name'].dropna().unique()
goal_events = goal_events.copy()
goal_events['conceding_team'] = goal_events.apply(lambda row: [team for team in team_names if team != row['team_name']][0] if row['typeId'] == 'Goal' else row['team_name'], axis=1)
for _, goal_row in goal_events.iterrows():
    conceded_team = goal_row['conceding_team']
    goal_minute = goal_row['timeMin']
    goal_sec = goal_row['timeSec']
    goal_period = goal_row['periodId']
    active_players = starting_lineups[(starting_lineups['team_name'] == conceded_team) & (starting_lineups['time_on'] <= goal_minute) & (starting_lineups['time_off'] >= goal_minute)]
    for _, player in active_players.iterrows():
        pid = player['player_id']
        player_name = player['player_name']
        team_name = player['team_name']
        playing_pos = resolve_position({'playerId': pid, 'periodId': goal_period, 'timeMin': goal_minute, 'timeSec': goal_sec})
        if pd.isna(playing_pos) or not playing_pos:
            xt_val = 0
        elif any((p in playing_pos for p in ['LB', 'CB', 'RB', 'RWB', 'LWB'])):
            xt_val = -0.2
        elif 'M' in playing_pos:
            xt_val = -0.05
        else:
            xt_val = 0
        goal_conceded_rows.append({'playerName': player_name, 'team_name': team_name, 'timeMin': goal_minute, 'timeSec': goal_sec, 'periodId': goal_period, 'playing_position': playing_pos, 'typeId': 'goal_conceded', 'xT_value': xt_val})
goal_conceded_df = pd.DataFrame(goal_conceded_rows, columns=['playerName', 'team_name', 'timeMin', 'timeSec', 'periodId', 'playing_position', 'typeId', 'xT_value'])
goal_conceded_df = goal_conceded_df.drop_duplicates(subset=['periodId', 'timeMin', 'timeSec', 'playerName', 'team_name'])
for col in df.columns:
    if col not in goal_conceded_df.columns:
        goal_conceded_df[col] = None
df = pd.concat([df, goal_conceded_df], ignore_index=True)
df = df.sort_values(by=['periodId', 'timeMin', 'timeSec']).reset_index(drop=True)
teams_conceded = goal_events['conceding_team'].unique()
clean_sheet_eligible = starting_lineups[(starting_lineups['minutes_played'] > 60) & (starting_lineups['goals_conceded'] == 0) & ~starting_lineups['team_name'].isin(teams_conceded)]
clean_sheet_rows = []
if not _live_finished:
    clean_sheet_eligible = clean_sheet_eligible.iloc[:0]
for _, player in clean_sheet_eligible.iterrows():
    pos = player['position']
    if pd.isna(pos):
        continue
    if any((p in pos for p in ['LB', 'CB', 'RB', 'RWB', 'LWB'])):
        xt_val = 0.4
    elif 'M' in pos:
        xt_val = 0.1
    else:
        xt_val = None
    clean_sheet_rows.append({'playerName': player['player_name'], 'team_name': player['team_name'], 'typeId': 'clean_sheet', 'playing_position': pos, 'xT_value': xt_val})
clean_sheet_df = pd.DataFrame(clean_sheet_rows)
for col in df.columns:
    if col not in clean_sheet_df.columns:
        clean_sheet_df[col] = None
df = pd.concat([df, clean_sheet_df], ignore_index=True)
df = df.sort_values(by=['periodId', 'timeMin', 'timeSec'], na_position='last').reset_index(drop=True)
clean_sheet_mask = df['typeId'] == 'clean_sheet'
df = pd.concat([df[~clean_sheet_mask], df[clean_sheet_mask].drop_duplicates(subset=['playerName', 'playing_position'])]).reset_index(drop=True)
starting_lineups = starting_lineups[starting_lineups['minutes_played'].notna()]
starting_lineups['xT_value'] = starting_lineups.apply(calculate_xt_value, axis=1)
starting_lineups['periodId'] = starting_lineups['periodId_x'].combine_first(starting_lineups['periodId_y'])
goalsconcededtotal = df[df['typeId'].isin(['goal_conceded', 'clean_sheet'])][['playerName', 'xT_value']].copy()
goalsconcededtotal = goalsconcededtotal.groupby('playerName', as_index=False)['xT_value'].sum()
takeondf = df[df['typeId'] == 'Take On'].copy()
takeondf['x'] = pd.to_numeric(takeondf['x'], errors='coerce')

def assign_xt(row):
    if row['x'] < 33.33:
        return -0.15 if row['outcome'] == 'Unsuccessful' else 0.05
    elif row['x'] < 66.66:
        return -0.1 if row['outcome'] == 'Unsuccessful' else 0.1
    else:
        return -0.05 if row['outcome'] == 'Unsuccessful' else 0.15
takeondf['xT_value'] = takeondf.apply(assign_xt, axis=1)
takeontotal = takeondf.groupby('playerName')['xT_value'].sum().reset_index()
df = df.merge(takeondf[['id', 'xT_value']], on='id', how='left', suffixes=('', '_carry'))
df['xT_value'] = df['xT_value'].combine_first(df['xT_value_carry'])
df.drop(columns=['xT_value_carry'], inplace=True)
errorsdf = df[(df['errorshot'] == 1) | (df['errorgoal'] == 1)].copy()

def assign_error_xt(row):
    if row.get('errorgoal') == 1:
        return -0.5
    elif row.get('errorshot') == 1:
        return -0.1
    return 0
errorsdf['xT_value'] = errorsdf.apply(assign_error_xt, axis=1)
errorstotal = errorsdf.groupby('playerName')['xT_value'].sum().reset_index()
df = df.merge(errorsdf[['id', 'xT_value']], on='id', how='left', suffixes=('', '_carry'))
df['xT_value'] = df['xT_value'].combine_first(df['xT_value_carry'])
df.drop(columns=['xT_value_carry'], inplace=True)
dispossdf = df[df['typeId'] == 'Dispossessed'].copy()

def assign_disposs_xt(x):
    if x < 33.3:
        return -0.15
    elif 33.3 <= x < 66.6:
        return -0.01
    else:
        return -0.05
dispossdf['xT_value'] = dispossdf['x'].apply(assign_disposs_xt)
disposstotal = dispossdf.groupby('playerName')['xT_value'].sum().reset_index()
df = df.merge(errorsdf[['id', 'xT_value']], on='id', how='left', suffixes=('', '_carry'))
df['xT_value'] = df['xT_value'].combine_first(df['xT_value_carry'])
df.drop(columns=['xT_value_carry'], inplace=True)
dataframes = [shotstakentotal, defthreattotal, incomppasstotal, passthreattotal, carrythreattotal, cards_df, shotassisttotal, receivedpassestotal, goalsconcededtotal, takeontotal, errorstotal, disposstotal]
valid_dataframes = [df for df in dataframes if isinstance(df, pd.DataFrame) and (not df.empty)]
totalxt = pd.concat(dataframes)
totalxt = totalxt.groupby('playerName', as_index=False).sum()
totalxt = totalxt.sort_values(by='xT_value', ascending=False)
goalkeepers = starting_lineups[starting_lineups['position'] == 'GK']['player_name'].unique()
totalxt = totalxt[~totalxt['playerName'].isin(goalkeepers)].reset_index(drop=True)
trimmed_xt = totalxt.iloc[1:-1]
mean_xt = trimmed_xt['xT_value'].mean()
totalxt['Player Impact'] = totalxt['xT_value'] - mean_xt
totalxt['Player Impact'] = totalxt['Player Impact'].round(2)
totalxt['Player Impact'] = totalxt['Player Impact'].apply(lambda x: f'+{x:.2f}' if x > 0 else f'-{abs(x):.2f}')
totalxt['Match Rank'] = totalxt['xT_value'].rank(method='max', ascending=False)
totalxt['Match Rank'] = totalxt['Match Rank'].astype(int)
totalxt.rename(columns={'xT_value': 'Threat Value'}, inplace=True)
starting_lineups = starting_lineups.merge(totalxt, how='left', left_on='player_name', right_on='playerName')
starting_lineups = starting_lineups.drop_duplicates(subset=['player_id', 'match_id'], keep='first')
for col in df.columns:
    if col not in position_change_df.columns:
        position_change_df[col] = None
df = pd.concat([df, position_change_df], ignore_index=True)
df['start_distance'] = ((df['x'] - 100) ** 2 + (df['y'] - 50) ** 2) ** 0.5
df['end_distance'] = ((df['end_x'] - 100) ** 2 + (df['end_y'] - 50) ** 2) ** 0.5
df['progressive_carry'] = 'No'
carry_mask = (df['typeId'] == 'Carry') & (df['end_distance'] < 0.8 * df['start_distance'])
df.loc[carry_mask, 'progressive_carry'] = 'Yes'
pass_conditions = [(df['x'] <= 50) & (df['end_x'] <= 50), (df['x'] <= 50) & (df['end_x'] >= 50), (df['x'] > 50) & (df['x'] <= 75), df['x'] > 75]
pass_percentages = [0.65, 0.8, 0.85, 1.0]
df['progressive_pass'] = 'No'
is_pass = (df['typeId'] == 'Pass') & (df['outcome'] == 'Successful')
for cond, threshold in zip(pass_conditions, pass_percentages):
    pass_mask = is_pass & cond & (df['end_distance'] < threshold * df['start_distance'])
    df.loc[pass_mask, 'progressive_pass'] = 'Yes'
df['assist'] = pd.to_numeric(df['assist'], errors='coerce').fillna(0)
df['keyPass'] = pd.to_numeric(df['keyPass'], errors='coerce').fillna(0)
df['xT_value'] = pd.to_numeric(df['xT_value'], errors='coerce').fillna(0)
df.loc[df['keyPass'] == 1, 'xT_value'] = df.loc[df['keyPass'] == 1, 'xT_value'] + 0.1
df.loc[df['assist'] == 1, 'xT_value'] = 0.6

def to_abs_min(period_id, time_min, time_sec=0):
    if pd.isna(time_min):
        return pd.NA
    period_id = int(period_id) if pd.notna(period_id) else 1
    t = float(time_min) + (float(time_sec) / 60.0 if pd.notna(time_sec) else 0.0)
    if period_id == 1:
        return t
    if period_id == 2:
        return t if t > 45 else 45.0 + t
    if period_id == 3:
        return t if t > 90 else 90.0 + t
    if period_id == 4:
        return t if t > 105 else 105.0 + t
    return t
if 'abs_min' not in df.columns:
    df['abs_min'] = df.apply(lambda r: to_abs_min(r.get('periodId'), r.get('timeMin'), r.get('timeSec', 0)), axis=1)
match_end_abs = pd.to_numeric(df['abs_min'], errors='coerce').max()
starting_lineups = starting_lineups.copy()
starting_lineups['time_on'] = pd.to_numeric(starting_lineups.get('time_on'), errors='coerce')
starting_lineups['time_off'] = pd.to_numeric(starting_lineups.get('time_off'), errors='coerce')
if 'periodId' not in starting_lineups.columns:
    starting_lineups['periodId'] = np.nan
if 'periodId_y' in starting_lineups.columns:
    starting_lineups['periodId'] = starting_lineups['periodId'].combine_first(starting_lineups['periodId_y'])
if 'periodId_x' in starting_lineups.columns:
    starting_lineups['periodId'] = starting_lineups['periodId'].combine_first(starting_lineups['periodId_x'])
starting_lineups['periodId'] = pd.to_numeric(starting_lineups['periodId'], errors='coerce').fillna(1).astype(int)
starting_lineups['time_on_abs'] = np.where(starting_lineups['is_starter'].astype(str).str.lower().eq('yes'), 0.0, starting_lineups.apply(lambda r: to_abs_min(r['periodId'], r['time_on'], 0), axis=1))
starting_lineups['time_off_abs'] = starting_lineups.apply(lambda r: to_abs_min(r['periodId'], r['time_off'], 0) if pd.notna(r['time_off']) else match_end_abs, axis=1)
starting_lineups['time_on_abs'] = pd.to_numeric(starting_lineups['time_on_abs'], errors='coerce').fillna(0.0)
starting_lineups['time_off_abs'] = pd.to_numeric(starting_lineups['time_off_abs'], errors='coerce').fillna(match_end_abs)
sl = starting_lineups.copy()
for c in ['is_starter', 'subbed_on', 'subbed_off']:
    if c in sl.columns:
        sl[c] = sl[c].astype(str).str.lower()
sl['time_on'] = pd.to_numeric(sl['time_on'], errors='coerce').fillna(0)
sl['time_off'] = pd.to_numeric(sl['time_off'], errors='coerce')
sl['minutes_played'] = pd.to_numeric(sl.get('minutes_played'), errors='coerce')
sl['time_off'] = sl['time_off'].combine_first(sl['minutes_played'])
sl['on_periodId'] = 1
if 'periodId_y' in sl.columns:
    sl.loc[sl['subbed_on'].eq('yes'), 'on_periodId'] = pd.to_numeric(sl.loc[sl['subbed_on'].eq('yes'), 'periodId_y'], errors='coerce').fillna(2).astype(int)
else:
    sl.loc[sl['subbed_on'].eq('yes'), 'on_periodId'] = 2
sl['off_periodId'] = sl['on_periodId']
if 'periodId_x' in sl.columns:
    mask_off = sl['subbed_off'].eq('yes')
    sl.loc[mask_off, 'off_periodId'] = pd.to_numeric(sl.loc[mask_off, 'periodId_x'], errors='coerce').fillna(sl.loc[mask_off, 'on_periodId']).astype(int)
pos_cols = [c for c in sl.columns if c.startswith('position') and (not c.endswith('mins'))]

def row_has_gk(r):
    if str(r.get('position', '')).strip() == 'GK':
        return True
    for c in pos_cols:
        if str(r.get(c, '')).strip() == 'GK':
            return True
    return False
sl['is_gk_candidate'] = sl.apply(row_has_gk, axis=1)
gk_candidates = sl[sl['is_gk_candidate']].copy()
gk_by_team_period = {}
for team, grp in gk_candidates.groupby('team_name'):
    team_map = {}
    starter = grp[(grp['is_starter'] == 'yes') & ((grp['position'].astype(str).str.strip() == 'GK') | grp.apply(row_has_gk, axis=1))]
    starter_name = starter.iloc[0]['player_name'] if not starter.empty else None
    team_map[1] = starter_name
    for p in [2, 3, 4]:
        p_sub = grp[(grp['subbed_on'] == 'yes') & (grp['on_periodId'] == p)]
        if not p_sub.empty:
            p_sub = p_sub.sort_values('time_on')
            team_map[p] = p_sub.iloc[0]['player_name']
        else:
            team_map[p] = starter_name
    gk_by_team_period[team] = team_map
match_teams = [t for t in df['team_name'].dropna().unique()]

def get_opponent_team(team):
    if team in match_teams and len(match_teams) == 2:
        return match_teams[0] if match_teams[1] == team else match_teams[1]
    return None

def resolve_opposition_gk_period_aware(row):
    shooting_team = row.get('team_name')
    if pd.isna(shooting_team):
        return None
    opp_team = get_opponent_team(shooting_team)
    if opp_team is None:
        return None
    p = row.get('periodId')
    if pd.isna(p):
        return None
    p = int(p)
    return gk_by_team_period.get(opp_team, {}).get(p, None)
shot_types = ['Goal', 'Miss', 'Attempt Saved', 'Post']
df['cross'] = pd.to_numeric(df.get('cross', 0), errors='coerce').fillna(0).astype(int)
df.loc[(df['cross'] == 1) & (df['typeId'] != 'Pass'), 'cross'] = 0
shot_mask = df['typeId'].isin(shot_types)
cross_mask = df['cross'].eq(1)
target_mask = shot_mask | cross_mask
df['playing_GK'] = None
df.loc[target_mask, 'playing_GK'] = df.loc[target_mask].apply(resolve_opposition_gk_period_aware, axis=1)
SIX_X_MIN, SIX_X_MAX = (94.2, 100.0)
SIX_Y_MIN, SIX_Y_MAX = (36.8, 63.2)

def _point_in_rect(px, py, xmin, xmax, ymin, ymax):
    return xmin <= px <= xmax and ymin <= py <= ymax

def _segment_intersects_rect(x1, y1, x2, y2, xmin, xmax, ymin, ymax):
    """
    Returns True if the line segment (x1,y1)->(x2,y2) intersects the axis-aligned rectangle.
    Uses Liang–Barsky line clipping (robust for segment-rectangle intersection).
    """
    if _point_in_rect(x1, y1, xmin, xmax, ymin, ymax) or _point_in_rect(x2, y2, xmin, xmax, ymin, ymax):
        return True
    dx = x2 - x1
    dy = y2 - y1
    p = [-dx, dx, -dy, dy]
    q = [x1 - xmin, xmax - x1, y1 - ymin, ymax - y1]
    u1, u2 = (0.0, 1.0)
    for pi, qi in zip(p, q):
        if pi == 0:
            if qi < 0:
                return False
        else:
            t = qi / pi
            if pi < 0:
                if t > u2:
                    return False
                if t > u1:
                    u1 = t
            else:
                if t < u1:
                    return False
                if t < u2:
                    u2 = t
    return u1 <= u2
for c in ['x', 'y', 'end_x', 'end_y']:
    df[c] = pd.to_numeric(df[c], errors='coerce')
df['cross'] = pd.to_numeric(df.get('cross', 0), errors='coerce').fillna(0).astype(int)

def cross_into_six_row(r):
    if r.get('cross', 0) != 1:
        return 'no'
    x1, y1, x2, y2 = (r['x'], r['y'], r['end_x'], r['end_y'])
    if pd.isna(x1) or pd.isna(y1) or pd.isna(x2) or pd.isna(y2):
        return 'no'
    hit = _segment_intersects_rect(float(x1), float(y1), float(x2), float(y2), SIX_X_MIN, SIX_X_MAX, SIX_Y_MIN, SIX_Y_MAX)
    return 'yes' if hit else 'no'
df['cross_into_six'] = df.apply(cross_into_six_row, axis=1)
defensive_actions = {'Tackle', 'Interception', 'Ball recovery', 'Clearance', 'Save'}
shot_events = {'Goal', 'Miss', 'Attempt Saved', 'Post'}
goal_events = {'Goal'}
df = df.sort_values(['periodId', 'timeMin', 'timeSec']).reset_index(drop=True)
df['match_seconds'] = df['timeMin'] * 60 + df['timeSec']
is_successful_def_action = df['typeId'].isin(defensive_actions) & (df['outcome'] == 'Successful')
df['turnover_shot'] = 0
df['turnover_goal'] = 0
for (period, team), group in df.groupby(['periodId', 'team_name'], sort=False):
    idx = group.index.to_numpy()
    times = group['match_seconds'].to_numpy()
    types = group['typeId'].to_numpy()
    def_pos = np.where(group['typeId'].isin(defensive_actions).to_numpy() & (group['outcome'].to_numpy() == 'Successful'))[0]
    shot_pos = np.where(np.isin(types, list(shot_events)))[0]
    goal_pos = np.where(np.isin(types, list(goal_events)))[0]
    for pos in def_pos:
        start_time = times[pos]
        end_time = start_time + 15
        has_shot = np.any((times[shot_pos] > start_time) & (times[shot_pos] <= end_time))
        has_goal = np.any((times[goal_pos] > start_time) & (times[goal_pos] <= end_time))
        df.loc[idx[pos], 'turnover_shot'] = int(has_shot)
        df.loc[idx[pos], 'turnover_goal'] = int(has_goal)
df.drop(columns='match_seconds', inplace=True)
starting_lineups['contestant_id'] = starting_lineups['contestant_id'].astype(str).str.strip()
teamdata['id'] = teamdata['id'].astype(str).str.strip()
starting_lineups = starting_lineups.merge(teamdata[['id', 'name']], left_on='contestant_id', right_on='id', how='left')
starting_lineups.rename(columns={'name': 'team_name'}, inplace=True)
starting_lineups = starting_lineups.loc[:, ~starting_lineups.columns.duplicated()].copy()
lineup_dedupe_keys = [col for col in ['match_id', 'player_id'] if col in starting_lineups.columns]
if lineup_dedupe_keys:
    starting_lineups = starting_lineups.drop_duplicates(subset=lineup_dedupe_keys, keep='first').reset_index(drop=True)
player_to_team = starting_lineups[['player_name', 'team_name']].dropna(subset=['player_name', 'team_name']).drop_duplicates(subset=['player_name'], keep='first').set_index('player_name')['team_name'].to_dict()
mask = df['typeId'] == 'position_change'
df.loc[mask, 'team_name'] = df.loc[mask, 'playerName'].map(player_to_team)
match_teams = list(starting_lineups['team_name'].dropna().unique())
if len(match_teams) != 2:
    raise ValueError(f'Expected exactly two teams when calculating game_state; found {match_teams}')
team_a, team_b = match_teams
scoring_team = pd.Series(pd.NA, index=df.index, dtype='object')
normal_goal_mask = df['typeId'].eq('Goal')
own_goal_mask = df['typeId'].eq('Own Goal')
scoring_team.loc[normal_goal_mask] = df.loc[normal_goal_mask, 'team_name']
scoring_team.loc[own_goal_mask] = np.where(df.loc[own_goal_mask, 'team_name'].eq(team_a), team_b, team_a)
team_a_score = scoring_team.eq(team_a).cumsum()
team_b_score = scoring_team.eq(team_b).cumsum()
score_difference = team_a_score - team_b_score
df['game_state'] = np.select([df['team_name'].eq(team_a), df['team_name'].eq(team_b)], [score_difference, -score_difference], default=np.nan)
df['game_state'] = df['game_state'].astype('Int64')
df['possession_chain'] = pd.Series(pd.NA, index=df.index, dtype='Int64')
df['possession_chain_time'] = pd.Series(pd.NA, index=df.index, dtype='Float64')
synthetic_event_types = {'goal_conceded', 'clean_sheet', 'position_change'}
shot_event_types = {'Attempt Saved', 'Goal', 'Own Goal', 'Miss', 'Post'}
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
df['expectedGoals'] = pd.to_numeric(df.get('expectedGoals'), errors='coerce')
df['xG_buildup'] = 0.0
match_chain_keys = ['team_name', 'possession_chain']
chain_ending_shots = df.loc[df['expectedGoals'].notna() & df['possession_chain_time'].notna() & df['possession_chain'].notna(), match_chain_keys + ['expectedGoals']].copy()
match_chain_xg = chain_ending_shots.groupby(match_chain_keys, dropna=False)['expectedGoals'].max().to_dict()
match_chain_values = pd.Series(list(zip(df['team_name'], df['possession_chain'])), index=df.index)
df['_match_chain_xg'] = match_chain_values.map(match_chain_xg)
non_shot_involvement = ~df.index.isin(chain_ending_shots.index)
first_match_chain_involvement = df['playerName'].notna() & df['possession_chain'].notna() & df['_match_chain_xg'].notna() & non_shot_involvement & ~df.loc[non_shot_involvement].duplicated(subset=match_chain_keys + ['playerName'], keep='first').reindex(df.index, fill_value=False)
df.loc[first_match_chain_involvement, 'xG_buildup'] = df.loc[first_match_chain_involvement, '_match_chain_xg']
df.drop(columns=['_match_chain_xg'], inplace=True)
event_order = pd.to_numeric(df['periodId'], errors='coerce').fillna(0) * 1000000.0 + pd.to_numeric(df['timeMin'], errors='coerce').fillna(0) * 60.0 + pd.to_numeric(df['timeSec'], errors='coerce').fillna(0)
timing_events = df.copy()
timing_events['_event_order'] = event_order
valid_period_mask = pd.to_numeric(timing_events['periodId'], errors='coerce').isin([1, 2, 3, 4])
valid_timing_events = timing_events.loc[valid_period_mask].copy()
timing_dedupe_keys = [col for col in ['id', 'eventId'] if col in valid_timing_events.columns]
if timing_dedupe_keys:
    real_timing_event = valid_timing_events[timing_dedupe_keys].notna().all(axis=1)
    valid_timing_events = pd.concat([valid_timing_events.loc[real_timing_event].drop_duplicates(subset=timing_dedupe_keys, keep='first'), valid_timing_events.loc[~real_timing_event]]).sort_index()
match_end_order = valid_timing_events['_event_order'].max()
team_match_minutes = (pd.to_numeric(valid_timing_events['timeMin'], errors='coerce') + pd.to_numeric(valid_timing_events['timeSec'], errors='coerce').fillna(0) / 60.0).max()
xg_shots = valid_timing_events.loc[valid_timing_events['expectedGoals'].notna() & valid_timing_events['_event_order'].notna()].copy()
xg_shots['_is_chain_shot'] = xg_shots['possession_chain_time'].notna()
scoring_events = valid_timing_events.loc[valid_timing_events['typeId'].isin(['Goal', 'Own Goal']) & valid_timing_events['_event_order'].notna()].copy()
scoring_events['_scoring_team'] = np.where(scoring_events['typeId'].eq('Goal'), scoring_events['team_name'], np.where(scoring_events['team_name'].eq(team_a), team_b, team_a))
buildup_events = valid_timing_events.loc[pd.to_numeric(valid_timing_events['xG_buildup'], errors='coerce').fillna(0).gt(0) & valid_timing_events['_event_order'].notna()].copy()
player_on_clock = valid_timing_events.loc[valid_timing_events['typeId'].eq('Player on')].dropna(subset=['team_name', 'playerName', '_event_order']).groupby(['team_name', 'playerName'])['_event_order'].min().to_dict()
player_off_clock = valid_timing_events.loc[valid_timing_events['typeId'].eq('Player off')].dropna(subset=['team_name', 'playerName', '_event_order']).groupby(['team_name', 'playerName'])['_event_order'].max().to_dict()
position_change_events = valid_timing_events.loc[valid_timing_events['typeId'].eq('position_change') & valid_timing_events['playerName'].notna() & valid_timing_events['playing_position'].notna()].sort_values('_event_order')
position_metric_suffixes = ['xG_on_field', 'chain_xG_on_field', 'xG_faced', 'chain_xG_faced', 'xG_buildup', 'team_goals_for', 'team_goals_against']
for slot in range(1, 6):
    for suffix in position_metric_suffixes:
        starting_lineups[f'position{slot}_{suffix}'] = 0.0
for lineup_idx, lineup_row in starting_lineups.iterrows():
    player_name = lineup_row.get('player_name')
    player_team = lineup_row.get('team_name')
    player_key = (player_team, player_name)
    is_starter = str(lineup_row.get('is_starter')).strip().lower() == 'yes'
    is_subbed_off = str(lineup_row.get('subbed_off')).strip().lower() == 'yes'
    fallback_start = pd.to_numeric(pd.Series([lineup_row.get('time_on')]), errors='coerce').iloc[0]
    fallback_end = pd.to_numeric(pd.Series([lineup_row.get('time_off')]), errors='coerce').iloc[0]
    on_period = pd.to_numeric(pd.Series([lineup_row.get('on_periodId', 1)]), errors='coerce').fillna(1).iloc[0]
    off_period = pd.to_numeric(pd.Series([lineup_row.get('off_periodId', on_period)]), errors='coerce').fillna(on_period).iloc[0]
    fallback_start_order = float(on_period) * 1000000.0 + (0.0 if pd.isna(fallback_start) else float(fallback_start) * 60.0)
    fallback_end_order = float(off_period) * 1000000.0 + float(fallback_end) * 60.0 + 59.999 if pd.notna(fallback_end) else match_end_order
    stint_start = 1000000.0 if is_starter else player_on_clock.get(player_key, fallback_start_order)
    if is_subbed_off:
        stint_end_limit = player_off_clock.get(player_key, fallback_end_order)
    else:
        stint_end_limit = match_end_order
    if pd.isna(stint_start) or pd.isna(stint_end_limit):
        continue
    valid_slots = [slot for slot in range(1, 6) if pd.notna(lineup_row.get(f'position{slot}')) and pd.notna(pd.to_numeric(pd.Series([lineup_row.get(f'position{slot}mins')]), errors='coerce').iloc[0])]
    player_changes = position_change_events.loc[position_change_events['team_name'].eq(player_team) & position_change_events['playerName'].eq(player_name) & position_change_events['_event_order'].gt(float(stint_start)) & position_change_events['_event_order'].lt(float(stint_end_limit))].copy()
    used_change_indices = set()
    for slot in valid_slots:
        stint_minutes = pd.to_numeric(pd.Series([lineup_row.get(f'position{slot}mins')]), errors='coerce').iloc[0]
        if pd.isna(stint_minutes) or stint_minutes <= 0:
            continue
        is_last_slot = slot == valid_slots[-1]
        if is_last_slot:
            stint_end = float(stint_end_limit)
        else:
            next_position = lineup_row.get(f'position{slot + 1}')
            matching_changes = player_changes.loc[player_changes['playing_position'].eq(next_position) & ~player_changes.index.isin(used_change_indices) & player_changes['_event_order'].gt(float(stint_start))]
            if not matching_changes.empty:
                change_idx = matching_changes.index[0]
                used_change_indices.add(change_idx)
                stint_end = min(float(stint_end_limit), float(matching_changes.at[change_idx, '_event_order']))
            else:
                stint_end = min(float(stint_end_limit), float(stint_start) + float(stint_minutes) * 60.0)
        if is_last_slot:
            shot_time_mask = xg_shots['_event_order'].between(stint_start, stint_end, inclusive='both')
            buildup_time_mask = buildup_events['_event_order'].between(stint_start, stint_end, inclusive='both')
            goal_time_mask = scoring_events['_event_order'].between(stint_start, stint_end, inclusive='both')
        else:
            shot_time_mask = xg_shots['_event_order'].ge(stint_start) & xg_shots['_event_order'].lt(stint_end)
            buildup_time_mask = buildup_events['_event_order'].ge(stint_start) & buildup_events['_event_order'].lt(stint_end)
            goal_time_mask = scoring_events['_event_order'].ge(stint_start) & scoring_events['_event_order'].lt(stint_end)
        team_shots = xg_shots.loc[shot_time_mask & xg_shots['team_name'].eq(player_team)]
        opposition_shots = xg_shots.loc[shot_time_mask & ~xg_shots['team_name'].eq(player_team)]
        player_buildup = buildup_events.loc[buildup_time_mask & buildup_events['playerName'].eq(player_name)]
        interval_goals = scoring_events.loc[goal_time_mask]
        starting_lineups.at[lineup_idx, f'position{slot}_xG_on_field'] = team_shots['expectedGoals'].sum()
        starting_lineups.at[lineup_idx, f'position{slot}_chain_xG_on_field'] = team_shots.loc[team_shots['_is_chain_shot'], 'expectedGoals'].sum()
        starting_lineups.at[lineup_idx, f'position{slot}_xG_faced'] = opposition_shots['expectedGoals'].sum()
        starting_lineups.at[lineup_idx, f'position{slot}_chain_xG_faced'] = opposition_shots.loc[opposition_shots['_is_chain_shot'], 'expectedGoals'].sum()
        starting_lineups.at[lineup_idx, f'position{slot}_xG_buildup'] = player_buildup['xG_buildup'].sum()
        starting_lineups.at[lineup_idx, f'position{slot}_team_goals_for'] = interval_goals['_scoring_team'].eq(player_team).sum()
        starting_lineups.at[lineup_idx, f'position{slot}_team_goals_against'] = interval_goals['_scoring_team'].ne(player_team).sum()
        stint_start = stint_end
for suffix in position_metric_suffixes:
    slot_columns = [f'position{slot}_{suffix}' for slot in range(1, 6)]
    total_column = 'xG_buildup_match_total' if suffix == 'xG_buildup' else suffix
    starting_lineups[total_column] = starting_lineups[slot_columns].sum(axis=1)
team_xg_totals = xg_shots.groupby('team_name')['expectedGoals'].sum().to_dict()
team_goal_totals = scoring_events['_scoring_team'].value_counts().to_dict()
for lineup_idx, lineup_row in starting_lineups.iterrows():
    lineup_team = lineup_row.get('team_name')
    opponent_team = team_b if lineup_team == team_a else team_a
    starting_lineups.at[lineup_idx, 'team_total_xG_for'] = team_xg_totals.get(lineup_team, 0.0)
    starting_lineups.at[lineup_idx, 'team_total_xG_against'] = team_xg_totals.get(opponent_team, 0.0)
    starting_lineups.at[lineup_idx, 'team_total_goals_for'] = team_goal_totals.get(lineup_team, 0)
    starting_lineups.at[lineup_idx, 'team_total_goals_against'] = team_goal_totals.get(opponent_team, 0)
    starting_lineups.at[lineup_idx, 'team_match_minutes'] = team_match_minutes
starting_lineups['xG_buildup_involvement_pct'] = np.where(starting_lineups['chain_xG_on_field'].gt(0), 100.0 * starting_lineups['xG_buildup_match_total'] / starting_lineups['chain_xG_on_field'], 0.0)
contestant_team_lookup = starting_lineups[['contestant_id', 'team_name']].dropna().drop_duplicates('contestant_id').assign(contestant_id=lambda x: x['contestant_id'].astype(str).str.strip()).set_index('contestant_id')['team_name'].to_dict()
formation_timeline = pd.DataFrame(formation_timeline_records)
if not formation_timeline.empty:
    formation_timeline['team_name'] = formation_timeline['contestant_id'].map(contestant_team_lookup)
    formation_timeline = formation_timeline.dropna(subset=['team_name', 'formation_code', '_event_order']).sort_values(['team_name', '_event_order'])
chain_end_events = valid_timing_events.loc[valid_timing_events['possession_chain'].notna() & valid_timing_events['possession_chain_time'].notna()].copy()
chain_end_events = chain_end_events.drop_duplicates(subset=['team_name', 'periodId', 'possession_chain'], keep='last')
formation_stint_rows = []
nominal_period_minute = {1: 0.0, 2: 45.0, 3: 90.0, 4: 105.0}
match_periods = sorted(pd.to_numeric(valid_timing_events['periodId'], errors='coerce').dropna().astype(int).unique())
for formation_team in [team_a, team_b]:
    team_timeline = formation_timeline.loc[formation_timeline['team_name'].eq(formation_team)].copy() if not formation_timeline.empty else pd.DataFrame()
    if team_timeline.empty:
        continue
    formation_opponent = team_b if formation_team == team_a else team_a
    team_stint_number = 0
    for formation_period in match_periods:
        period_events = valid_timing_events.loc[pd.to_numeric(valid_timing_events['periodId'], errors='coerce').eq(formation_period)]
        if period_events.empty:
            continue
        period_start_order = formation_period * 1000000.0 + nominal_period_minute.get(formation_period, 0.0) * 60.0
        period_end_order = period_events['_event_order'].max()
        active_candidates = team_timeline.loc[team_timeline['_event_order'].le(period_start_order)]
        if active_candidates.empty:
            continue
        active_formation = active_candidates.iloc[-1]
        period_changes = team_timeline.loc[team_timeline['_event_order'].gt(period_start_order) & team_timeline['_event_order'].lt(period_end_order) & team_timeline['periodId'].eq(formation_period)].copy()
        segment_starts = [period_start_order] + period_changes['_event_order'].tolist()
        segment_ends = period_changes['_event_order'].tolist() + [period_end_order]
        segment_formations = [active_formation] + [change_row for _, change_row in period_changes.iterrows()]
        for segment_index, (segment_start, segment_end, segment_formation) in enumerate(zip(segment_starts, segment_ends, segment_formations)):
            if segment_end <= segment_start:
                continue
            team_stint_number += 1
            is_final_segment = segment_index == len(segment_starts) - 1
            if is_final_segment:
                xg_mask = xg_shots['_event_order'].between(segment_start, segment_end, inclusive='both')
                goal_mask = scoring_events['_event_order'].between(segment_start, segment_end, inclusive='both')
                chain_mask = chain_end_events['_event_order'].between(segment_start, segment_end, inclusive='both')
            else:
                xg_mask = xg_shots['_event_order'].ge(segment_start) & xg_shots['_event_order'].lt(segment_end)
                goal_mask = scoring_events['_event_order'].ge(segment_start) & scoring_events['_event_order'].lt(segment_end)
                chain_mask = chain_end_events['_event_order'].ge(segment_start) & chain_end_events['_event_order'].lt(segment_end)
            stint_xg = xg_shots.loc[xg_mask]
            stint_goals = scoring_events.loc[goal_mask]
            stint_chains = chain_end_events.loc[chain_mask]
            chains_for = stint_chains.loc[stint_chains['team_name'].eq(formation_team)]
            chains_against = stint_chains.loc[stint_chains['team_name'].eq(formation_opponent)]
            score_before = scoring_events.loc[scoring_events['_event_order'].lt(segment_start), '_scoring_team']
            team_score = int(score_before.eq(formation_team).sum())
            opponent_score = int(score_before.eq(formation_opponent).sum())
            game_state_seconds = {'Ahead': 0.0, 'Level': 0.0, 'Behind': 0.0}
            state_cursor = float(segment_start)
            for _, scoring_row in stint_goals.sort_values('_event_order').iterrows():
                scoring_time = min(max(float(scoring_row['_event_order']), state_cursor), float(segment_end))
                score_difference = team_score - opponent_score
                state_name = 'Ahead' if score_difference > 0 else 'Behind' if score_difference < 0 else 'Level'
                game_state_seconds[state_name] += scoring_time - state_cursor
                if scoring_row['_scoring_team'] == formation_team:
                    team_score += 1
                elif scoring_row['_scoring_team'] == formation_opponent:
                    opponent_score += 1
                state_cursor = scoring_time
            score_difference = team_score - opponent_score
            state_name = 'Ahead' if score_difference > 0 else 'Behind' if score_difference < 0 else 'Level'
            game_state_seconds[state_name] += float(segment_end) - state_cursor
            raw_formation = segment_formation.get('formation')
            formation_text = str(int(raw_formation)) if pd.notna(raw_formation) else str(segment_formation['formation_code'])
            formation_label = '-'.join(list(formation_text))
            formation_stint_rows.append({'match_id': matchlink, 'team_name': formation_team, 'opponent': formation_opponent, 'formation_code': segment_formation['formation_code'], 'formation': raw_formation, 'formation_label': formation_label, 'periodId': formation_period, 'stint_number': team_stint_number, 'start_event_order': segment_start, 'end_event_order': segment_end, 'playing_time_seconds': segment_end - segment_start, 'time_ahead_seconds': game_state_seconds['Ahead'], 'time_level_seconds': game_state_seconds['Level'], 'time_behind_seconds': game_state_seconds['Behind'], 'team_goals_for': stint_goals['_scoring_team'].eq(formation_team).sum(), 'team_goals_against': stint_goals['_scoring_team'].eq(formation_opponent).sum(), 'total_xG_for': stint_xg.loc[stint_xg['team_name'].eq(formation_team), 'expectedGoals'].sum(), 'total_xG_against': stint_xg.loc[stint_xg['team_name'].eq(formation_opponent), 'expectedGoals'].sum(), 'possession_chain_count_for': len(chains_for), 'possession_chain_count_against': len(chains_against), 'possession_chain_time_for': pd.to_numeric(chains_for['possession_chain_time'], errors='coerce').sum(), 'possession_chain_time_against': pd.to_numeric(chains_against['possession_chain_time'], errors='coerce').sum()})
formation_stints_df = pd.DataFrame(formation_stint_rows)
formation_pair_rows = []
if not formation_stints_df.empty:
    team_a_stints = formation_stints_df.loc[formation_stints_df['team_name'].eq(team_a)]
    team_b_stints = formation_stints_df.loc[formation_stints_df['team_name'].eq(team_b)]
    for _, team_a_stint in team_a_stints.iterrows():
        for _, team_b_stint in team_b_stints.loc[team_b_stints['periodId'].eq(team_a_stint['periodId'])].iterrows():
            pair_start = max(team_a_stint['start_event_order'], team_b_stint['start_event_order'])
            pair_end = min(team_a_stint['end_event_order'], team_b_stint['end_event_order'])
            if pair_end <= pair_start:
                continue
            pair_xg = xg_shots.loc[xg_shots['_event_order'].ge(pair_start) & xg_shots['_event_order'].lt(pair_end)]
            pair_goals = scoring_events.loc[scoring_events['_event_order'].ge(pair_start) & scoring_events['_event_order'].lt(pair_end)]
            pair_chains = chain_end_events.loc[chain_end_events['_event_order'].ge(pair_start) & chain_end_events['_event_order'].lt(pair_end)]
            score_before = scoring_events.loc[scoring_events['_event_order'].lt(pair_start), '_scoring_team']
            score_a = int(score_before.eq(team_a).sum())
            score_b = int(score_before.eq(team_b).sum())
            pair_state_seconds = {'Ahead': 0.0, 'Level': 0.0, 'Behind': 0.0}
            state_cursor = float(pair_start)
            for _, scoring_row in pair_goals.sort_values('_event_order').iterrows():
                scoring_time = float(scoring_row['_event_order'])
                difference = score_a - score_b
                state_name = 'Ahead' if difference > 0 else 'Behind' if difference < 0 else 'Level'
                pair_state_seconds[state_name] += scoring_time - state_cursor
                if scoring_row['_scoring_team'] == team_a:
                    score_a += 1
                elif scoring_row['_scoring_team'] == team_b:
                    score_b += 1
                state_cursor = scoring_time
            difference = score_a - score_b
            state_name = 'Ahead' if difference > 0 else 'Behind' if difference < 0 else 'Level'
            pair_state_seconds[state_name] += float(pair_end) - state_cursor
            chains_a = pair_chains.loc[pair_chains['team_name'].eq(team_a)]
            chains_b = pair_chains.loc[pair_chains['team_name'].eq(team_b)]
            formation_pair_rows.append({'match_id': matchlink, 'periodId': team_a_stint['periodId'], 'team_a_name': team_a, 'team_b_name': team_b, 'team_a_formation_code': team_a_stint['formation_code'], 'team_a_formation': team_a_stint['formation_label'], 'team_b_formation_code': team_b_stint['formation_code'], 'team_b_formation': team_b_stint['formation_label'], 'start_event_order': pair_start, 'end_event_order': pair_end, 'playing_time_seconds': pair_end - pair_start, 'team_a_time_ahead_seconds': pair_state_seconds['Ahead'], 'time_level_seconds': pair_state_seconds['Level'], 'team_a_time_behind_seconds': pair_state_seconds['Behind'], 'team_a_goals_for': pair_goals['_scoring_team'].eq(team_a).sum(), 'team_a_goals_against': pair_goals['_scoring_team'].eq(team_b).sum(), 'team_a_xG_for': pair_xg.loc[pair_xg['team_name'].eq(team_a), 'expectedGoals'].sum(), 'team_a_xG_against': pair_xg.loc[pair_xg['team_name'].eq(team_b), 'expectedGoals'].sum(), 'team_a_possession_chain_count_for': len(chains_a), 'team_a_possession_chain_count_against': len(chains_b), 'team_a_possession_chain_time_for': pd.to_numeric(chains_a['possession_chain_time'], errors='coerce').sum(), 'team_a_possession_chain_time_against': pd.to_numeric(chains_b['possession_chain_time'], errors='coerce').sum()})
formation_pairs_df = pd.DataFrame(formation_pair_rows)
df.drop(columns=['_ball_out_of_play'], inplace=True)
live_events = df.loc[~df['typeId'].isin({'goal_conceded', 'clean_sheet', 'position_change'}) & df['periodId'].notna() & df['timeMin'].notna() & df['timeSec'].notna()].copy()
live_events['periodId'] = pd.to_numeric(live_events['periodId'], errors='coerce')
live_events['raw_seconds'] = pd.to_numeric(live_events['timeMin'], errors='coerce') * 60.0 + pd.to_numeric(live_events['timeSec'], errors='coerce')
nominal_period_start = {1: 0.0, 2: 45.0 * 60, 3: 90.0 * 60, 4: 105.0 * 60}
score_by_team = {team_a: 0, team_b: 0}
state_seconds = {team_a: {}, team_b: {}}
for period in sorted(live_events['periodId'].dropna().astype(int).unique()):
    period_events = live_events.loc[live_events['periodId'].eq(period)].copy()
    if period_events.empty:
        continue
    nominal_start = nominal_period_start.get(period, 0.0)
    minimum_raw_time = period_events['raw_seconds'].min()
    clock_is_continuous = period == 1 or minimum_raw_time >= max(0.0, nominal_start - 5.0 * 60)
    if clock_is_continuous:
        period_events['clock_seconds'] = period_events['raw_seconds']
    else:
        period_events['clock_seconds'] = nominal_start + period_events['raw_seconds']
    period_events = period_events.sort_values(['clock_seconds', 'id'], kind='stable', na_position='last')
    period_end = period_events['clock_seconds'].max()
    cursor = nominal_start
    period_goals = period_events.loc[period_events['typeId'].isin(['Goal', 'Own Goal'])]
    for _, goal_row in period_goals.iterrows():
        goal_time = max(cursor, float(goal_row['clock_seconds']))
        interval_seconds = max(0.0, goal_time - cursor)
        for state_team, opponent_team in [(team_a, team_b), (team_b, team_a)]:
            exact_state = score_by_team[state_team] - score_by_team[opponent_team]
            state = max(-5, min(5, exact_state))
            state_seconds[state_team][state] = state_seconds[state_team].get(state, 0.0) + interval_seconds
        scoring_team_for_summary = goal_row['team_name'] if goal_row['typeId'] == 'Goal' else team_b if goal_row['team_name'] == team_a else team_a
        if scoring_team_for_summary in score_by_team:
            score_by_team[scoring_team_for_summary] += 1
        cursor = goal_time
    final_interval_seconds = max(0.0, float(period_end) - cursor)
    for state_team, opponent_team in [(team_a, team_b), (team_b, team_a)]:
        exact_state = score_by_team[state_team] - score_by_team[opponent_team]
        state = max(-5, min(5, exact_state))
        state_seconds[state_team][state] = state_seconds[state_team].get(state, 0.0) + final_interval_seconds
game_state_summary_rows = []
synthetic_event_number = 1
for summary_team in [team_a, team_b]:
    for state, elapsed_seconds in sorted(state_seconds[summary_team].items()):
        if elapsed_seconds <= 0:
            continue
        state_label = 'Ahead' if state > 0 else 'Behind' if state < 0 else 'Level'
        summary_row = {column: pd.NA for column in df.columns}
        summary_row.update({'id': -900000 - synthetic_event_number, 'eventId': -900000 - synthetic_event_number, 'team_name': summary_team, 'typeId': state, 'outcome': state_label, 'event_time': elapsed_seconds, 'game_state': state})
        game_state_summary_rows.append(summary_row)
        synthetic_event_number += 1
if game_state_summary_rows:
    df = pd.concat([df, pd.DataFrame(game_state_summary_rows, columns=df.columns)], ignore_index=True, sort=False)
event_dedupe_keys = [col for col in ['id', 'eventId'] if col in df.columns]
if event_dedupe_keys:
    df['_event_row_order'] = np.arange(len(df))
    real_event_mask = df[event_dedupe_keys].notna().all(axis=1)
    df = pd.concat([df.loc[real_event_mask].drop_duplicates(subset=event_dedupe_keys, keep='first'), df.loc[~real_event_mask]]).sort_values('_event_row_order').drop(columns=['_event_row_order']).reset_index(drop=True)
from difflib import SequenceMatcher
import unicodedata

def _physical_tokens(value):
    text = unicodedata.normalize('NFKD', str(value))
    text = ''.join((char for char in text if not unicodedata.combining(char)))
    return re.findall('[a-z0-9]+', text.casefold())

def _physical_compact(value):
    return ''.join(_physical_tokens(value))

def _physical_team_similarity(left, right):
    left_key, right_key = (_physical_compact(left), _physical_compact(right))
    if not left_key or not right_key:
        return 0.0
    if left_key == right_key:
        return 1.0
    if left_key in right_key or right_key in left_key:
        return 0.94
    return SequenceMatcher(None, left_key, right_key).ratio()

def _physical_name_similarity(scoresway_name, fotmob_name):
    left, right = (_physical_tokens(scoresway_name), _physical_tokens(fotmob_name))
    if not left or not right:
        return 0.0
    if left == right:
        return 1.0
    left_surname, right_surname = (left[-1], right[-1])
    surname_score = SequenceMatcher(None, left_surname, right_surname).ratio()
    first_initial_matches = left[0][0] == right[0][0]
    if left_surname == right_surname and first_initial_matches:
        return 0.98
    if left_surname == right_surname:
        return 0.82
    compact_score = SequenceMatcher(None, ''.join(left), ''.join(right)).ratio()
    if first_initial_matches and surname_score >= 0.84:
        return max(compact_score, 0.86 * surname_score)
    return compact_score

def add_physical_data_to_player_log(player_log, physical_df):
    output = player_log.copy()
    physical_columns = ['matchId', 'playerId', 'optaId', 'playerName', 'teamId', 'teamName', 'isGoalkeeper', 'minutesPlayed', 'topSpeedKmh', 'distanceCoveredM', 'distanceCoveredKm', 'runningM', 'runningKm', 'runningTotalM', 'runningPct', 'sprintingM', 'sprintingKm', 'sprintingTotalM', 'sprintingPct', 'numberOfSprints']
    renamed = {column: f'physical_{column}' for column in physical_columns}
    if physical_df is None or physical_df.empty:
        pass
        for new_column in renamed.values():
            output[new_column] = pd.NA
        output['physical_match_score'] = pd.NA
        return output
    if not {'player_name', 'team_name'}.issubset(output.columns):
        raise ValueError('Player log requires player_name and team_name for physical matching.')
    physical = physical_df.reset_index(drop=True).copy()
    scoreway_teams = output['team_name'].dropna().astype(str).unique().tolist()
    fotmob_teams = physical['teamName'].dropna().astype(str).unique().tolist()
    team_map = {}
    for scoreway_team in scoreway_teams:
        ranked_teams = sorted(((_physical_team_similarity(scoreway_team, fotmob_team), fotmob_team) for fotmob_team in fotmob_teams), reverse=True)
        if ranked_teams and ranked_teams[0][0] >= 0.72:
            team_map[scoreway_team] = ranked_teams[0][1]
    candidate_edges = []
    for log_index, log_row in output.iterrows():
        fotmob_team = team_map.get(str(log_row.get('team_name')))
        if fotmob_team is None:
            continue
        team_candidates = physical.loc[physical['teamName'].astype(str) == fotmob_team]
        log_minutes = pd.to_numeric(log_row.get('minutes_played'), errors='coerce')
        for physical_index, physical_row in team_candidates.iterrows():
            name_score = _physical_name_similarity(log_row.get('player_name'), physical_row.get('playerName'))
            if name_score < 0.78:
                continue
            physical_minutes = pd.to_numeric(physical_row.get('minutesPlayed'), errors='coerce')
            minute_bonus = 0.0
            if pd.notna(log_minutes) and pd.notna(physical_minutes):
                minute_bonus = max(0.0, 0.03 * (1 - abs(log_minutes - physical_minutes) / 15))
            candidate_edges.append((name_score + minute_bonus, name_score, log_index, physical_index))
    assigned_log_rows, assigned_physical_rows, assignments = (set(), set(), {})
    for total_score, name_score, log_index, physical_index in sorted(candidate_edges, reverse=True):
        if log_index in assigned_log_rows or physical_index in assigned_physical_rows:
            continue
        assignments[log_index] = (physical_index, name_score)
        assigned_log_rows.add(log_index)
        assigned_physical_rows.add(physical_index)
    for new_column in renamed.values():
        output[new_column] = pd.NA
    output['physical_match_score'] = pd.NA
    audit_rows = []
    for log_index, (physical_index, name_score) in assignments.items():
        physical_row = physical.loc[physical_index]
        for old_column, new_column in renamed.items():
            if old_column in physical_row.index:
                output.at[log_index, new_column] = physical_row[old_column]
        output.at[log_index, 'physical_match_score'] = round(float(name_score), 3)
        audit_rows.append({'Scoresway player': output.at[log_index, 'player_name'], 'Scoresway team': output.at[log_index, 'team_name'], 'FotMob player': physical_row.get('playerName'), 'FotMob team': physical_row.get('teamName'), 'Name score': round(float(name_score), 3), 'Distance km': physical_row.get('distanceCoveredKm')})
    unmatched = output.loc[output['physical_playerId'].isna(), ['player_name', 'team_name']]
    pass
    if audit_rows:
        pass
    if not unmatched.empty:
        pass
        pass
    return output
starting_lineups = add_physical_data_to_player_log(starting_lineups, physical_performance)

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
df = add_pressing_actions(df)
