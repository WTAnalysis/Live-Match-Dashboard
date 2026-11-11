import pandas as pd

def _fotmob_stat_payload(section, label):
    item = section.get(label, {}) if isinstance(section, dict) else {}
    payload = item.get('stat', {}) if isinstance(item, dict) else {}
    return payload if isinstance(payload, dict) else {}

def physical_performance_from_matchdetails(matchdetails, match_id):
    """Return one row per player with FotMob physical-performance data."""
    content = matchdetails.get('content', {}) or {}
    player_stats = content.get('playerStats', {}) or {}
    general = matchdetails.get('general', {}) or {}
    rows = []
    for player_key, player in player_stats.items():
        physical_section = None
        top_stats = {}
        for group in player.get('stats', []) or []:
            if group.get('key') == 'physical_metrics':
                physical_section = group.get('stats', {}) or {}
            elif group.get('key') == 'top_stats':
                top_stats = group.get('stats', {}) or {}
        if not physical_section:
            continue
        top_speed = _fotmob_stat_payload(physical_section, 'Top speed')
        distance = _fotmob_stat_payload(physical_section, 'Distance covered')
        running = _fotmob_stat_payload(physical_section, 'Running')
        sprinting = _fotmob_stat_payload(physical_section, 'Sprinting')
        sprint_count = _fotmob_stat_payload(physical_section, 'Number of sprints')
        minutes = _fotmob_stat_payload(top_stats, 'Minutes played')
        distance_m = distance.get('value')
        running_m = running.get('value')
        sprinting_m = sprinting.get('value')
        running_total_m = running.get('total')
        sprinting_total_m = sprinting.get('total')
        rows.append({'matchId': int(match_id), 'matchName': general.get('matchName'), 'playerId': player.get('id', player_key), 'optaId': player.get('optaId'), 'playerName': player.get('name'), 'teamId': player.get('teamId'), 'teamName': player.get('teamName'), 'isGoalkeeper': player.get('isGoalkeeper'), 'minutesPlayed': minutes.get('value'), 'topSpeedKmh': top_speed.get('value'), 'distanceCoveredM': distance_m, 'distanceCoveredKm': distance_m / 1000 if pd.notna(distance_m) else None, 'runningM': running_m, 'runningKm': running_m / 1000 if pd.notna(running_m) else None, 'runningTotalM': running_total_m, 'runningPct': 100 * running_m / running_total_m if running_m is not None and running_total_m else None, 'sprintingM': sprinting_m, 'sprintingKm': sprinting_m / 1000 if pd.notna(sprinting_m) else None, 'sprintingTotalM': sprinting_total_m, 'sprintingPct': 100 * sprinting_m / sprinting_total_m if sprinting_m is not None and sprinting_total_m else None, 'numberOfSprints': sprint_count.get('value')})
    return pd.DataFrame(rows)