"""Match PAR inputs shared by the leaderboard and ongoing ranking."""
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from no_xg_model import GP_X_EDGES, GP_Y_EDGES, context_multiplier, gp_at
from player_actions import boolean_series, is_goalkeeper_position


@st.cache_data(show_spinner=False)
def published_match_par(path, match_id, modified):
    scores = pd.read_csv(path, usecols=["match_id", "player_id", "PAR"],
                         dtype={"match_id": str, "player_id": str})
    scores = scores.loc[scores.match_id.eq(str(match_id))].drop_duplicates("player_id")
    return pd.to_numeric(scores.set_index("player_id").PAR, errors="coerce")


def match_par_inputs(events, roster, source, league, match_id):
    roster = roster.copy()
    teams = events.drop_duplicates("team_name").set_index("team_name").team
    opponent = dict(zip(teams.unique(), reversed(teams.unique())))
    kinds = events.typeId

    def numeric(column):
        return pd.to_numeric(events.get(column, pd.Series(0, index=events.index)), errors="coerce").fillna(0)

    value = numeric("xT_value")
    unsuccessful_pass = kinds.eq("Pass") & events.outcome.eq("Unsuccessful")
    # Run_v2.0 prices the turnover from the opponent's attacking perspective.
    failed = events.loc[unsuccessful_pass]
    penalty = -gp_at(100 - failed.x, failed.y)
    start_x_zone = pd.cut(failed.x, GP_X_EDGES, labels=False, include_lowest=True)
    start_y_zone = pd.cut(failed.y, GP_Y_EDGES, labels=False, include_lowest=True)
    end_x_zone = pd.cut(failed.end_x, GP_X_EDGES, labels=False, include_lowest=True)
    end_y_zone = pd.cut(failed.end_y, GP_Y_EDGES, labels=False, include_lowest=True)
    known_zones = start_x_zone.notna() & start_y_zone.notna() & end_x_zone.notna() & end_y_zone.notna()
    crosses_zone = start_x_zone.ne(end_x_zone) | start_y_zone.ne(end_y_zone)
    half_penalty = failed.x.le(25) & failed.end_x.ge(failed.x) & known_zones & crosses_zone
    value.loc[unsuccessful_pass] = penalty.where(~half_penalty, penalty * 0.5)
    recipient = events.get("pass_recipient", pd.Series(None, index=events.index, dtype=object))
    assigned_keeper = events.get("playing_GK", pd.Series(None, index=events.index, dtype=object))
    scored = events.scorer.notna()
    swing = pd.Series(np.where(scored, np.where(events.scorer.eq(events.team), 1, -1), 0), index=events.index)
    home = next(iter(opponent))
    signed = swing.where(events.team.eq(home), -swing)
    before = signed.cumsum() - signed
    state = before.where(events.team.eq(home), -before)
    keeper_weight = context_multiplier(state, events.timeMin, goalkeeper=True)
    cards = kinds.eq("Card")
    card_value = pd.Series(np.select(
        [numeric("redcard").eq(1), numeric("yellowcard2").eq(1), numeric("yellowcard").eq(1)],
        [-0.8, -0.525, -0.275], default=0.0,
    ), index=events.index)
    fouls = kinds.eq("Foul")
    won = events.outcome.eq("Successful")
    foul_x = events.x.where(won, 100 - events.x)
    foul_y = events.y.where(won, 100 - events.y)
    zone = gp_at(foul_x, foul_y)
    in_box = foul_x.between(83, 100) & foul_y.between(21.1, 78.9)
    foul_value = zone.where(~in_box, 0.78 - zone)
    foul_value *= events.outcome.map({"Successful": 1, "Unsuccessful": -1}).fillna(0)
    discipline = cards | fouls
    base_discipline = card_value.where(cards, foul_value)
    outfield_weight = context_multiplier(state, events.timeMin)
    value = value.where(~discipline, base_discipline * outfield_weight)
    blocked = boolean_series(events.get("isBlocked", pd.Series(False, index=events.index))) | numeric("shotblocked").eq(1)
    faced = (kinds.eq("Goal") | (kinds.eq("Attempt Saved") & ~blocked)) & events.expectedGoalsOnTarget.notna()
    faced &= ~(numeric("isOwnGoal").eq(1) | numeric("owngoal").eq(1))
    shot_credit = (events.expectedGoalsOnTarget.fillna(0) - kinds.eq("Goal").astype(int)) * keeper_weight
    error = numeric("errorshot").eq(1) | numeric("errorgoal").eq(1)
    error_value = pd.Series(np.where(numeric("errorgoal").eq(1), -0.75, -0.30), index=events.index)
    keeper_actions = value.where(kinds.isin(["Claim", "Punch", "Keeper Sweeper", "Foul", "Card", "Own Goal", "Pass"]), 0)
    keeper_actions = keeper_actions.where(~error, error_value * keeper_weight)
    keeper_actions = keeper_actions.where(~discipline, base_discipline * keeper_weight)
    keeper_actions += 0.10 * numeric("xG_buildup") * keeper_weight
    successful_pass = kinds.eq("Pass") & events.outcome.eq("Successful")
    received_gp = gp_at(events.end_x, events.end_y).where(events.end_x.gt(50), 0) * keeper_weight

    by_player = {}
    totals = pd.Series(np.nan, index=roster.index)
    for index, row in roster.iterrows():
        if pd.isna(row.minutes_played) or float(row.minutes_played) <= 0:
            continue
        team, name = teams.get(row.team_name, row.team_name), row.player_name
        own = events.team.eq(team) & events.playerName.eq(name)
        received = events.team.eq(team) & recipient.eq(name) & successful_pass
        keeper = any(is_goalkeeper_position(row.get(column)) for column in ("position", "position1"))
        if keeper:
            against = events.team.eq(opponent.get(team)) & assigned_keeper.eq(name) & faced
            contributions = keeper_actions.where(own, 0) + received_gp.where(received, 0) + shot_credit.where(against, 0)
        else:
            contributions = value.where(own, 0) + numeric("received_pass_GP").where(received, 0)
        by_player[(team, name)] = contributions
        totals.at[index] = contributions.sum()

    stored = pd.to_numeric(roster.get("PAR", pd.Series(np.nan, index=roster.index)), errors="coerce")
    path = Path(source) / "Processed Matches" / "Season Player Logs" / f"{league}_PAR.csv"
    if path.is_file():
        try:
            published = published_match_par(str(path), str(match_id), path.stat().st_mtime_ns)
            stored = stored.fillna(roster.player_id.astype(str).map(published))
        except (OSError, ValueError):
            pass
    # Keep one scoring basis for the match. Partial exports cannot be compared
    # directly with raw event scores on a different scale.
    played = totals.notna()
    if played.any() and stored.loc[played].notna().all():
        roster["PAR"] = stored
        return roster, "PAR", by_player
    roster["Match PAR"] = totals
    return roster, "Match PAR", by_player
