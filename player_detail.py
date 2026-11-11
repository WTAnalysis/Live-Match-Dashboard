"""Pass connections, shot locations and minute-by-minute player ranks."""
from io import BytesIO
import html

from matplotlib.figure import Figure
from mplsoccer import VerticalPitch
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from player_actions import (
    BackgroundColor, GoalColor, PitchColor, PitchLineColor, SaveColor,
    is_goalkeeper_position, keeper_shot_locations, parse_on_goal_shot,
)


def pitch(half=False):
    return VerticalPitch(
        pitch_type="opta", half=half, pitch_color=PitchColor, line_color=PitchLineColor,
    )


def panel_note(ax, text, y=0.5):
    ax.text(0.5, y, text, transform=ax.transAxes, ha="center", va="center",
            color=BackgroundColor, fontsize=9)


# Scatter sizes are areas. Scale by the square to increase diameter by 25%.
PASS_MARKER_AREA_SCALE = 1.25 ** 2


def mark_selected(field, ax, point, number, colour, outline):
    x, y = point
    field.scatter(x, y, ax=ax, s=245 * PASS_MARKER_AREA_SCALE, color=colour,
                  edgecolor=outline, linewidth=1.5, zorder=5)
    ax.text(y, x, number, ha="center", va="center", color=outline,
            fontsize=9, weight="bold", zorder=6)


def format_position(point):
    x, y = point
    return f"x {x:.2f}, y {y:.2f}" if pd.notna(x) and pd.notna(y) else "Unavailable"


def pass_panel(ax, passes, centre, name, numbers, colour, outline, receiving=False, by_teammate=False):
    field = VerticalPitch(
        pitch_type="opta", pitch_color="#c5dfa9", line_color=PitchLineColor,
    )
    field.draw(ax=ax)
    title = "Receiving Map" if receiving else "Pass Map"
    ax.set_title(f"{name} - {title}", color="white")
    focus = "pass_recipient" if receiving else "playerName"
    partner = "playerName" if receiving else "pass_recipient"
    links = passes.loc[passes[focus].eq(name) & passes[partner].ne(name)]
    number = numbers.get(name, "–")
    if not by_teammate and not pd.isna(centre).any():
        mark_selected(field, ax, centre, number, colour, outline)
    if links.empty:
        panel_note(ax, "No completed passes linked", y=0.1)
        return []

    groups = links.groupby(partner, sort=False)
    counts = groups.size()
    locations = groups[["x", "y", "end_x", "end_y"]].mean()
    partner_x, partner_y = ("x", "y") if receiving else ("end_x", "end_y")
    selected_x, selected_y = ("end_x", "end_y") if receiving else ("x", "y")
    for teammate, row in locations.iterrows():
        partner_point = (row[partner_x], row[partner_y])
        selected_point = (row[selected_x], row[selected_y]) if by_teammate else centre
        if by_teammate:
            mark_selected(field, ax, selected_point, number, colour, outline)
        start, end = (partner_point, selected_point) if receiving else (selected_point, partner_point)
        field.lines(*start, *end, ax=ax, color=colour,
                    linewidth=0.75 + 4 * counts[teammate] / counts.max(), alpha=0.65, zorder=2)

    marker_sizes = 110 + 210 * counts.reindex(locations.index) / counts.max()
    field.scatter(locations[partner_x], locations[partner_y], ax=ax, s=marker_sizes * PASS_MARKER_AREA_SCALE,
                  color=outline, edgecolor=colour, linewidth=1.1, zorder=3)
    for teammate, row in locations.iterrows():
        ax.text(row[partner_y], row[partner_x], numbers.get(teammate, "–"),
                ha="center", va="center", color=colour, fontsize=8, weight="bold", zorder=4)
    entries = [
        f"{numbers.get(teammate, '–')}  {teammate} ({count})"
        + (f" · {format_position(locations.loc[teammate, [selected_x, selected_y]])}" if by_teammate else "")
        for teammate, count in counts.sort_values(ascending=False, kind="stable").items()
    ]
    return entries


def shot_panels(ax, events, name):
    field = pitch(half=True)
    field.draw(ax=ax)
    ax.set_title(f"{name} - Shot Map", color="white")
    shots = events.loc[events.typeId.isin(["Attempt Saved", "Miss", "Post", "Goal"])
                       & ~events.isOwnGoal.eq(1)]
    attempts = shots.typeId.eq("Attempt Saved")
    blocked = attempts & (
        shots.expectedGoalsOnTarget.eq(0)
        | shots.get("isBlocked", pd.Series(False, index=shots.index)).astype(str).str.lower().isin(["true", "1", "1.0"])
    )
    on_target = attempts & ~blocked
    goals = shots.typeId.eq("Goal")
    for mask, colour, label in (
        (on_target, "blue", "On target"),
        (blocked, "orange", "Blocked"),
        (shots.typeId.isin(["Miss", "Post"]), "red", "Off target"),
        (goals, "green", "Goal"),
    ):
        group = shots.loc[mask]
        field.scatter(group.x, group.y, s=group.expectedGoals.fillna(0.035).clip(lower=0.01) * 1000,
                      ax=ax, facecolors="none", edgecolors=colour, label=label, zorder=3)
    if shots.empty:
        panel_note(ax, "No shots recorded")
    else:
        ax.legend(loc="upper left", fontsize=7, framealpha=0.85, markerscale=0.6)

    return shots.loc[on_target | goals]


def draw_goal(goal, name, faced=False):
    title = "Shots Faced on Goal" if faced else "Shot Locations on Goal"
    goal.set_title(f"{name} - {title}", color="white")
    goal.set_facecolor(PitchColor)
    goal.set(xlim=(-0.18, 2.18), ylim=(-0.10, 0.76), xticks=[], yticks=[])
    # Match the data-unit proportions of the main goalkeeper overview.
    main_goal_aspect = (0.255 * 10) / (0.380 * 14) * (2.04 / 0.70)
    goal.set_aspect(main_goal_aspect, adjustable="box")
    for spine in goal.spines.values():
        spine.set_visible(False)
    goal.plot([0, 0, 2, 2], [0, 0.66, 0.66, 0], color="black", linewidth=2.4)
    goal.vlines(np.arange(0.2, 2, 0.2), 0, 0.66, color="grey", linewidth=0.5)
    goal.hlines(np.arange(0.0825, 0.66, 0.0825), 0, 2, color="grey", linewidth=0.5)
def outfield_goal(goal, shots, name):
    draw_goal(goal, name)
    placed = shots.copy()
    coords = placed.get("onGoalShot", pd.Series(index=placed.index, dtype=object)).map(parse_on_goal_shot)
    for axis in ("x", "y"):
        placed[f"goal_{axis}"] = pd.to_numeric(coords.map(lambda item: item.get(axis) if item else None),
                                               errors="coerce")
    placed = placed.dropna(subset=["goal_x", "goal_y"])
    for is_goal in (False, True):
        group = placed.loc[placed.typeId.eq("Goal").eq(is_goal)]
        goal.scatter(group.goal_x, group.goal_y,
                     s=group.expectedGoalsOnTarget.fillna(0.035).clip(lower=0.01) * 800,
                     marker="*" if is_goal else "o", facecolors="green" if is_goal else "none",
                     edgecolors=BackgroundColor if is_goal else "blue", alpha=0.85, zorder=3)
    if placed.empty:
        panel_note(goal, "No shot placement available", y=0.12)


def keeper_panels(ax, goal, player_events, shots_faced, name):
    field = pitch(half=True)
    field.draw(ax=ax)
    ax.invert_xaxis()
    ax.invert_yaxis()
    ax.set_title(f"{name} - Goalkeeper Actions", color="white")
    types = player_events.typeId.astype("string").str.lower().str.replace(r"[^a-z]", "", regex=True)
    plotted = False
    for kinds, marker, label in (
        (("claim", "claims"), "s", "Claim"),
        (("punch", "punches"), "^", "Punch"),
        (("smother", "smothers"), "D", "Smother"),
        (("keepersweeper", "goalkeepersweeper"), "h", "Keeper Sweeper"),
    ):
        actions = player_events.loc[types.isin(kinds) & player_events.x.between(0, 50)
                                    & player_events.y.between(0, 100)]
        if not actions.empty:
            plotted = True
        field.scatter(100 - actions.x, 100 - actions.y, ax=ax, marker=marker, s=65,
                      c=actions.outcome.map({"Successful": "green", "Unsuccessful": "red"}).fillna("grey"),
                      edgecolors="white", linewidths=0.6, label=label, zorder=3)
    if plotted:
        ax.legend(loc="upper left", fontsize=7, framealpha=0.85, labelcolor=BackgroundColor)
    else:
        panel_note(ax, "No goalkeeper actions recorded")

    draw_goal(goal, name, faced=True)
    saves, conceded = keeper_shot_locations(shots_faced)
    for group, marker, colour in ((saves, "o", SaveColor), (conceded, "*", GoalColor)):
        goal.scatter(group.goal_x, group.goal_y,
                     s=group.expectedGoalsOnTarget.fillna(0.035).clip(lower=0.01) * 800,
                     marker=marker, facecolors=colour, edgecolors="white", zorder=3)
    if saves.empty and conceded.empty:
        panel_note(goal, "No shot placement available", y=0.12)


def detail_maps(events, roster, name, team, colour, outline, by_teammate=False):
    team_events = events.loc[events.team.eq(team)]
    source_teams = team_events.team_name.unique()
    squad = roster.loc[roster.team_name.isin([team, *source_teams])]
    numbers = {
        row.player_name: str(row.squad_number).strip().removesuffix(".0")
        for row in squad.itertuples() if pd.notna(row.squad_number)
    }
    all_passes = team_events.loc[team_events.typeId.eq("Pass")]
    if "pass_recipient" not in all_passes:
        all_passes = all_passes.assign(pass_recipient=pd.Series(dtype="object"))
    made = all_passes.loc[all_passes.playerName.eq(name), ["x", "y"]]
    received = all_passes.loc[all_passes.pass_recipient.eq(name), ["end_x", "end_y"]]
    made_centre = made.loc[made.apply(lambda col: col.between(0, 100)).all(axis=1)].mean()
    received_centre = received.loc[received.apply(lambda col: col.between(0, 100)).all(axis=1)].mean()
    passes = all_passes.loc[all_passes.outcome.eq("Successful")
                            & all_passes.pass_recipient.notna() & all_passes.playerName.notna()]
    passes = passes.loc[passes[["x", "y", "end_x", "end_y"]].apply(lambda col: col.between(0, 100)).all(axis=1)]

    fig = Figure(figsize=(14, 7), facecolor=BackgroundColor, layout="constrained")
    grid = fig.add_gridspec(2, 3, height_ratios=[1.35, 1])
    outgoing = pass_panel(fig.add_subplot(grid[:, 0]), passes, made_centre, name, numbers, colour, outline, by_teammate=by_teammate)
    incoming = pass_panel(fig.add_subplot(grid[:, 1]), passes, received_centre, name, numbers, colour, outline, receiving=True, by_teammate=by_teammate)
    player_events = team_events.loc[team_events.playerName.eq(name)]
    selected = squad.loc[squad.player_name.eq(name)]
    is_keeper = any(frame[column].map(is_goalkeeper_position).any()
                    for frame, columns in ((selected, ("position", "position1")),
                                           (player_events, ("playing_position",)))
                    for column in columns if column in frame)
    pitch_ax, goal_ax = fig.add_subplot(grid[0, 2]), fig.add_subplot(grid[1, 2])
    if is_keeper:
        assigned = events.get("playing_GK", pd.Series(pd.NA, index=events.index))
        shots_faced = events.loc[events.team.ne(team) & assigned.eq(name)]
        keeper_panels(pitch_ax, goal_ax, player_events, shots_faced, name)
    else:
        outfield_goal(goal_ax, shot_panels(pitch_ax, player_events, name), name)
    from player_faces import portrait
    from mpl_toolkits.axes_grid1.inset_locator import inset_axes
    face=portrait(selected)
    if face is not None:
        halfway=pitch_ax.transAxes.inverted().transform(pitch_ax.transData.transform((0,50)))[1]
        face_ax=inset_axes(pitch_ax,width="23%",height="27%",loc='lower left',
                          bbox_to_anchor=(.04,halfway,1,1),bbox_transform=pitch_ax.transAxes,borderpad=0)
        face_ax.imshow(face)
        face_ax.set_anchor('SW')
        face_ax.set_axis_off()
    output = BytesIO()
    fig.savefig(output, format="png", dpi=145)
    return output.getvalue(), outgoing, incoming, format_position(made_centre), format_position(received_centre), is_keeper


def performance_figure(events, rankings, metric, name, team, colours, outlines, par_actions):
    """Estimate the ranking path using events and the shared match-summary scores."""
    match_end = events.minute.max()
    source_to_team = events.drop_duplicates("team_name").set_index("team_name").team
    events_by_player = dict(tuple(events.groupby(["team", "playerName"], sort=False)))
    dismissal_flags = events.reindex(columns=["redcard", "yellowcard2"]).apply(pd.to_numeric, errors="coerce")
    dismissals = events.typeId.eq("Card") & dismissal_flags.eq(1).any(axis=1)
    players = {}
    for _, row in rankings.iterrows():
        player_team = source_to_team.get(row.team_name, row.team_name)
        key = (player_team, row.player_name)
        own = events_by_player.get(key, events.iloc[:0])
        on = own.loc[own.typeId.eq("Player on"), "minute"]
        off = own.loc[own.typeId.eq("Player off") | dismissals.loc[own.index], "minute"]
        if str(row.is_starter).lower() == "yes":
            start = 0.0
        elif not on.empty:
            start = on.min()
        elif pd.notna(row.minutes_played) and float(row.minutes_played) > 0:
            start = pd.to_numeric(getattr(row, "time_on_abs", np.nan), errors="coerce")
            if pd.isna(start):
                start = own.minute.min() if not own.empty else max(0, match_end - float(row.minutes_played))
        else:
            continue
        end = off.min() if not off.empty else match_end
        if player_team not in colours:
            continue
        start = min(start, end)
        contributions = par_actions[key]
        actions = contributions.groupby(events.minute).sum().sort_index().loc[start:end].cumsum()
        players[key] = (start, end, actions, float(row["_performance"]))

    focus = (team, name)
    if focus not in players:
        return None
    selected_events = events_by_player.get(focus, events.iloc[:0])
    flags = selected_events.reindex(columns=["yellowcard", "yellowcard2", "redcard", "owngoal", "isOwnGoal", "assist"])
    flags = flags.apply(pd.to_numeric, errors="coerce").eq(1)
    types = selected_events.typeId
    cards = types.eq("Card")
    sent_off = flags.redcard | flags.yellowcard2
    own_goal = types.eq("Own Goal") | (types.eq("Goal") & (flags.owngoal | flags.isOwnGoal))
    moments = (
        (cards & flags.yellowcard & ~sent_off, "Yellow card", "square", "#f2cf29"),
        (cards & sent_off, "Red card", "square", "#e32e3a"),
        (types.eq("Goal") & ~own_goal, "Goal", "star", "#168c43"),
        (own_goal, "Own goal", "star", "#e32e3a"),
        (types.eq("Pass") & flags.assist, "Assist", "diamond", "#1675db"),
        (types.eq("Player on"), "Subbed on", "triangle-up", "#168c43"),
        (types.eq("Player off"), "Subbed off", "triangle-down", "#d92b36"),
    )
    markers = [
        (selected_events.loc[mask, "minute"], label, symbol, colour)
        for mask, label, symbol, colour in moments
    ]
    keeper_rows = rankings.loc[
        rankings.player_name.eq(name) & rankings.team_name.map(lambda club: source_to_team.get(club, club)).eq(team)
    ]
    is_keeper = any(keeper_rows[column].map(is_goalkeeper_position).any()
                    for column in ("position", "position1") if column in keeper_rows)
    if is_keeper:
        start, end, _, _ = players[focus]
        assigned = events.get("playing_GK", pd.Series(pd.NA, index=events.index))
        conceded = events.scorer.notna() & events.scorer.ne(team) & events.minute.between(start, end)
        # Own goals can be attributed to the opposing keeper by the shot feed.
        eligible = assigned.eq(name) | assigned.isna() | events.scorer.ne(events.team)
        for opponent, goals in events.loc[conceded & eligible].groupby("scorer"):
            markers.append((goals.minute, "Goal conceded", "star", colours[opponent]))
    horizon = match_end
    boundary = [time for start, end, _, _ in players.values() for time in (start, end) if time <= horizon]
    boundary.extend(minute for _, _, impact, _ in players.values()
                    for minute in impact.index[impact.diff().fillna(impact).ne(0)])
    boundary.extend(minute for minutes, _, _, _ in markers for minute in minutes)
    periods = []
    period_labels = {1: "First Half", 2: "Second Half", 3: "Extra Time · First Half", 4: "Extra Time · Second Half"}
    period_titles = []
    tick_labels = {}
    for period_id, period in events.groupby("periodId", sort=False):
        first = period.iloc[0]
        start, end = first.minute, min(period.minute.max(), horizon)
        if start > horizon:
            break
        nominal_start = {1: 0, 2: 45, 3: 90, 4: 105}[period_id]
        clock = first.clock
        if clock < nominal_start - 20:
            clock += nominal_start
        offset = start - clock
        if period_id == 1:
            start = 0.0
        periods.append((start, end, offset))
        period_titles.append(((start + end) / 2, period_labels[period_id]))
        boundary.extend((start, end))
        for minute in range(nominal_start, int(end - offset) + 1):
            position = minute + offset
            if start <= position <= end:
                boundary.append(position)
                if minute % 10 == 0 and start + 3 < position < end - 3:
                    tick_labels[position] = f"{minute}′"
        tick_labels[start] = f"{nominal_start}′"
        if end - start >= 1:
            tick_labels[end] = f"{int(round(end - offset, 8))}′"

    timeline = np.unique(np.r_[boundary, horizon])
    offsets = np.select(
        [(timeline >= start) & (timeline <= end) for start, end, _ in periods],
        [offset for _, _, offset in periods],
    )
    clock_minutes = timeline - offsets
    clock_text = [f"{int(round(minute, 8))}′" for minute in clock_minutes]
    series = {}
    for key, (start, end, impact, final_score) in players.items():
        values = impact.loc[:end].reindex(timeline, method="ffill").fillna(0)
        # The summary provides one score per player. Spread the difference
        # from cumulative event threat across their time on the pitch.
        progress = np.clip((timeline - start) / max(end - start, 1e-9), 0, 1)
        estimate = values + progress * (final_score - values.at[end])
        series[key] = estimate.where(timeline < end, final_score).where(timeline >= start)
    scores = pd.DataFrame(series, index=timeline)
    # Columns follow the leaderboard order, including its stable tie order.
    ranks = scores.rank(axis=1, ascending=False, method="first")
    fig = go.Figure()
    for key in [*filter(lambda key: key != focus, players), focus]:
        player_team, player_name = key
        selected = key == focus
        fig.add_scatter(
            x=timeline, y=ranks[key], mode="lines",
            line=dict(color=outlines[player_team], width=6 if selected else 2.8, shape="hv"),
            opacity=1 if selected else 0.23, hoverinfo="skip", showlegend=False,
            name=player_name + " outline",
        )
        fig.add_scatter(
            x=timeline, y=ranks[key], customdata=np.column_stack((clock_text, scores[key].map(lambda value: f"{value:+.2f}"))), mode="lines+markers" if selected else "lines",
            marker=dict(size=3, color=colours[player_team],
                        line=dict(color=outlines[player_team], width=0.8)),
            line=dict(color=colours[player_team], width=3.5 if selected else 1.4, shape="hv"),
            opacity=1 if selected else 0.23, name=player_name, showlegend=selected,
            hovertemplate=f"%{{fullData.name}}<br>Match minute %{{customdata[0]}}<br>Rank #%{{y:.0f}}<br>{metric} %{{customdata[1]}}<extra></extra>",
        )
    clock_at = dict(zip(timeline, clock_text))
    for minutes, label, symbol, colour in markers:
        positions = ranks[focus].reindex(minutes.drop_duplicates()).dropna()
        if not positions.empty:
            fig.add_scatter(
                x=positions.index, y=positions, mode="markers", name=label, cliponaxis=False,
                customdata=[clock_at[minute] for minute in positions.index],
                marker=dict(symbol=symbol, size=11, color=colour, line=dict(color="#381d54", width=1)),
                hovertemplate=f"{label}<br>Match minute %{{customdata}}<br>Rank #%{{y:.0f}}<extra></extra>",
            )
    for midpoint, label in period_titles:
        fig.add_annotation(x=midpoint, y=-0.22, xref="x", yref="paper", text=label, showarrow=False)
    ticks = sorted(tick_labels)
    for start, _, _ in periods[1:]:
        fig.add_vline(x=start, line_width=1, line_dash="dot", line_color="#8c8392")
    fig.update_layout(template="plotly_white", height=435, showlegend=False, margin=dict(l=55, r=20, t=65, b=80),
                      title=dict(text=f"{html.escape(name)} - Ongoing Match Ranking",
                                 x=0.5, xanchor="center",
                                 font=dict(family="Comic Sans MS, cursive", size=22, color="#24202b")),
                      yaxis_title="Player Ranking",
                      xaxis=dict(range=[0, max(horizon, 1)], tickmode="array", tickvals=ticks, ticktext=[tick_labels[tick] for tick in ticks], tickangle=-45),
                      yaxis=dict(
                          range=[len(players) + 0.4, 0.4],
                          tickmode="array",
                          tickvals=sorted({*range(1, len(players) + 1, 2), len(players)}),
                      ), hovermode="closest")
    return fig
