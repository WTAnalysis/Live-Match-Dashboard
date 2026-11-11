"""Player links and live renderers adapted from the notebook's overview exports."""
import ast
import base64
from io import BytesIO
import html
import json
import re
from urllib.parse import urlencode, unquote

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.lines import Line2D
from mplsoccer import VerticalPitch, add_image
import numpy as np
import pandas as pd
from PIL import Image

TextColor = "white"
BackgroundColor = "#381d54"
PitchColor = "#f5f6fc"
PitchLineColor = "black"
HullColor = BackgroundColor
SaveColor = "#20b26b"
GoalColor = "#e63946"
title_font = FontProperties(family=["Comic Sans MS", "DejaVu Sans"], size=15)


def query_colour(value,default):
    text=str(value).strip()
    for _ in range(4):
        decoded=unquote(text)
        if decoded==text:break
        text=decoded
    return text if re.fullmatch(r'#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?',text) else default

def player_url(name,team,context):
    return '?'+urlencode({**context,'view':'player','player':name,'team':team})

def linked_name(name,team,context):
    text=html.escape(str(name))
    if not context:return text
    return f'<a href="{html.escape(player_url(name,team,context),quote=True)}" target="_self" style="color:#24202b;text-decoration:underline">{text}</a>'

def is_goalkeeper_position(value):
    position = str(value).strip().upper()

    return (
        position in {"GK", "G", "GOALKEEPER"}
        or "GOALKEEPER" in position
    )


def parse_on_goal_shot(value):
    """Convert an Opta onGoalShot value into a dictionary."""

    if isinstance(value, dict):
        return value

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    if not isinstance(value, str):
        return None

    value = value.strip()

    if not value:
        return None

    try:
        parsed = json.loads(
            value.replace("'", '"')
        )

        if isinstance(parsed, dict):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass

    try:
        parsed = ast.literal_eval(value)

        if isinstance(parsed, dict):
            return parsed
    except (ValueError, SyntaxError):
        pass

    return None


def boolean_series(values):
    """Safely interpret True/False, 1/0 and yes/no values."""

    if pd.api.types.is_bool_dtype(values):
        return values.fillna(False)

    numeric_values = pd.to_numeric(
        values,
        errors="coerce",
    )

    text_values = (
        values.astype(str)
        .str.strip()
        .str.casefold()
    )

    return (
        numeric_values.fillna(0).ne(0)
        | text_values.isin(
            ["true", "yes", "y", "blocked"]
        )
    )


def plot_comet_lines(
    axis,
    data,
    colour,
    number_of_segments=20,
    linewidth=1.5,
):
    """Draw the original fading pass/carry lines."""

    if data.empty:
        return

    for _, event in data.iterrows():
        values = pd.to_numeric(
            event[["end_y", "end_x", "y", "x"]],
            errors="coerce",
        )

        if values.isna().any():
            continue

        x_start = float(values["end_y"])
        y_start = float(values["end_x"])
        x_end = float(values["y"])
        y_end = float(values["x"])

        dx = (x_end - x_start) / number_of_segments
        dy = (y_end - y_start) / number_of_segments
        alphas = np.linspace(1, 0, number_of_segments)

        for segment_number, alpha in enumerate(alphas):
            axis.plot(
                [
                    x_start + segment_number * dx,
                    x_start + (segment_number + 1) * dx,
                ],
                [
                    y_start + segment_number * dy,
                    y_start + (segment_number + 1) * dy,
                ],
                color=colour,
                alpha=alpha,
                linewidth=linewidth,
            )


def create_player_overview(
    playername,
    player_events,
    opponentname,
    teamimage,
    wtaimaged,
    ranking,
    distance_covered_km,
    distance_rank,
    sprint_count,
    sprint_rank,
    player_face=None,
):
    completed_passes = player_events.loc[
        (player_events["typeId"] == "Pass")
        & (player_events["outcome"] == "Successful")
    ]

    incomplete_passes = player_events.loc[
        (player_events["typeId"] == "Pass")
        & (player_events["outcome"] == "Unsuccessful")
    ]

    shot_assists = player_events.loc[
        (player_events["typeId"] == "Pass")
        & (player_events["keyPass"] == 1)
    ]

    goal_assists = player_events.loc[
        (player_events["typeId"] == "Pass")
        & (player_events["assist"] == 1)
    ]

    takeons = player_events.loc[
        player_events["typeId"] == "Take On"
    ]
    successful_takeons = takeons.loc[
        takeons["outcome"] == "Successful"
    ]
    unsuccessful_takeons = takeons.loc[
        takeons["outcome"] != "Successful"
    ]

    tackles = player_events.loc[
        player_events["typeId"] == "Tackle"
    ]
    successful_tackles = tackles.loc[
        tackles["outcome"] == "Successful"
    ]
    unsuccessful_tackles = tackles.loc[
        tackles["outcome"] != "Successful"
    ]

    aerials = player_events.loc[
        player_events["typeId"] == "Aerial"
    ]
    successful_aerials = aerials.loc[
        aerials["outcome"] == "Successful"
    ]
    unsuccessful_aerials = aerials.loc[
        aerials["outcome"] != "Successful"
    ]

    fouls = player_events.loc[
        (player_events["typeId"] == "Foul")
        & (player_events["outcome"] == "Unsuccessful")
    ]

    ball_recoveries = player_events.loc[
        player_events["typeId"] == "Ball recovery"
    ]
    clearances = player_events.loc[
        player_events["typeId"] == "Clearance"
    ]
    interceptions = player_events.loc[
        player_events["typeId"] == "Interception"
    ]
    attempts_blocked = player_events.loc[
        player_events["typeId"] == "Save"
    ]
    dispossessions = player_events.loc[
        player_events["typeId"] == "Dispossessed"
    ]

    shots_off_target = player_events.loc[
        player_events["typeId"].isin(["Miss", "Post"])
    ]
    attempts = player_events.loc[player_events.typeId.eq("Attempt Saved")]
    next_position = attempts["next_player_position"].astype("string").str.strip().str.upper()
    blocked = next_position.notna() & next_position.ne("") & next_position.ne("GK")
    shots_blocked = attempts.loc[blocked]
    shots_on_target = attempts.loc[~blocked]
    goals = player_events.loc[
        player_events["typeId"] == "Goal"
    ]

    carries = player_events.loc[
        player_events["typeId"] == "Carry"
    ].copy()

    for column in ["x", "y", "end_x", "end_y"]:
        carries[column] = pd.to_numeric(
            carries[column],
            errors="coerce",
        )

    carries = carries.loc[
        carries["end_y"].between(0, 100, inclusive="neither")
        & carries["end_x"].between(0, 99.5, inclusive="neither")
        & carries["x"].gt(2.5)
    ].copy()

    carries["y_diff"] = carries["y"] - carries["end_y"]
    carries["x_diff"] = carries["x"] - carries["end_x"]

    carries = carries.loc[
        carries["y_diff"].between(-25, 25, inclusive="neither")
        & carries["x_diff"].between(-25, 25, inclusive="neither")
    ]

    fig, axes = plt.subplots(
        1,
        3,
        figsize=(24, 8.25),
        facecolor=BackgroundColor,
    )
    plt.subplots_adjust(wspace=-0.5)

    pitch_passes = VerticalPitch(
        pitch_type="opta",
        pitch_color=PitchColor,
        line_color=PitchLineColor,
    )
    pitch_touches = VerticalPitch(
        pitch_type="opta",
        pitch_color=PitchColor,
        line_color=PitchLineColor,
    )
    pitch_events = VerticalPitch(
        pitch_type="opta",
        pitch_color=PitchColor,
        line_color=PitchLineColor,
    )

    pitch_passes.draw(
        ax=axes[0],
        figsize=(8, 8.25),
        constrained_layout=True,
        tight_layout=False,
    )
    pitch_touches.draw(
        ax=axes[1],
        figsize=(8, 8.25),
        constrained_layout=True,
        tight_layout=False,
    )
    pitch_events.draw(
        ax=axes[2],
        figsize=(8, 8.25),
        constrained_layout=True,
        tight_layout=False,
    )

    axes[0].set_title(
        f"{playername} - Passes & Carries",
        fontproperties=title_font,
        color=TextColor,
    )
    axes[1].set_title(
        f"{playername} - Touch Map",
        fontproperties=title_font,
        color=TextColor,
    )
    axes[2].set_title(
        f"{playername} - Event Map",
        fontproperties=title_font,
        color=TextColor,
    )

    plot_comet_lines(axes[0], completed_passes, "green")
    plot_comet_lines(axes[0], incomplete_passes, "red")
    plot_comet_lines(axes[0], shot_assists, "orange")
    plot_comet_lines(axes[0], carries, "purple")
    plot_comet_lines(
        axes[0],
        goal_assists,
        "blue",
        number_of_segments=10,
        linewidth=2,
    )

    for _, event in player_events.iterrows():
        touch_x = pd.to_numeric(event.get("y"), errors="coerce")
        touch_y = pd.to_numeric(event.get("x"), errors="coerce")

        if pd.notna(touch_x) and pd.notna(touch_y):
            axes[1].plot(
                touch_x,
                touch_y,
                marker="o",
                markeredgecolor=HullColor,
                markerfacecolor="none",
                markersize=5,
            )

    scatter_tackle = pitch_events.scatter(
        successful_tackles.x,
        successful_tackles.y,
        ax=axes[2],
        facecolor="green",
        edgecolor="green",
        marker=">",
        label="Tackle",
        s=40,
    )
    pitch_events.scatter(
        unsuccessful_tackles.x,
        unsuccessful_tackles.y,
        ax=axes[2],
        facecolor="red",
        edgecolor="red",
        marker=">",
        s=40,
    )

    scatter_aerial = pitch_events.scatter(
        successful_aerials.x,
        successful_aerials.y,
        ax=axes[2],
        facecolor="green",
        edgecolor="green",
        marker="s",
        label="Aerial",
        s=40,
    )
    pitch_events.scatter(
        unsuccessful_aerials.x,
        unsuccessful_aerials.y,
        ax=axes[2],
        facecolor="red",
        edgecolor="red",
        marker="s",
        s=40,
    )

    scatter_block = pitch_events.scatter(
        attempts_blocked.x,
        attempts_blocked.y,
        ax=axes[2],
        facecolor="green",
        edgecolor="green",
        marker="p",
        label="Attempts Blocked",
        s=40,
    )
    scatter_recovery = pitch_events.scatter(
        ball_recoveries.x,
        ball_recoveries.y,
        ax=axes[2],
        facecolor="green",
        edgecolor="green",
        marker="d",
        label="Ball Recoveries",
        s=40,
    )
    scatter_clearance = pitch_events.scatter(
        clearances.x,
        clearances.y,
        ax=axes[2],
        facecolor="green",
        edgecolor="green",
        marker="^",
        label="Clearance",
        s=40,
    )
    scatter_takeon = pitch_events.scatter(
        successful_takeons.x,
        successful_takeons.y,
        ax=axes[2],
        facecolor="green",
        edgecolor="green",
        marker="P",
        label="Take On",
        s=40,
    )
    pitch_events.scatter(
        unsuccessful_takeons.x,
        unsuccessful_takeons.y,
        ax=axes[2],
        facecolor="red",
        edgecolor="red",
        marker="P",
        s=40,
    )
    scatter_dispossessed = pitch_events.scatter(
        dispossessions.x,
        dispossessions.y,
        ax=axes[2],
        facecolor="red",
        edgecolor="red",
        marker="x",
        label="Dispossessed",
        s=40,
    )

    pitch_events.scatter(
        shots_off_target.x,
        shots_off_target.y,
        ax=axes[2],
        facecolor="red",
        edgecolor="red",
        marker="o",
        label="Shot Off Target",
        s=40,
    )
    pitch_events.scatter(
        shots_blocked.x,
        shots_blocked.y,
        ax=axes[2],
        facecolor="yellow",
        edgecolor="goldenrod",
        marker="o",
        s=40,
    )
    scatter_on_target = pitch_events.scatter(
        shots_on_target.x,
        shots_on_target.y,
        ax=axes[2],
        facecolor="green",
        edgecolor="green",
        marker="o",
        label="Shot On Target",
        s=40,
    )
    scatter_goal = pitch_events.scatter(
        goals.x,
        goals.y,
        ax=axes[2],
        facecolor="green",
        edgecolor="green",
        marker="*",
        label="Goal",
        s=100,
    )
    pitch_events.scatter(
        fouls.x,
        fouls.y,
        ax=axes[2],
        facecolor="red",
        edgecolor="red",
        marker=">",
        s=40,
    )

    axes[2].legend(
        handles=[
            scatter_tackle,
            scatter_aerial,
            scatter_block,
            scatter_recovery,
            scatter_clearance,
            scatter_takeon,
            scatter_dispossessed,
            scatter_on_target,
            scatter_goal,
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, -0.02),
        ncol=2,
        facecolor="silver",
        frameon=False,
        labelcolor=TextColor,
    )

    pass_legend_labels = [
        "Completed Pass",
        "Incompleted Pass",
        "Shot Assist",
        "Assist",
        "Ball Carry",
    ]
    pass_legend_colours = [
        "green",
        "red",
        "orange",
        "blue",
        "purple",
    ]
    pass_legend_lines = [
        Line2D([0], [0], color=colour, linewidth=3)
        for colour in pass_legend_colours
    ]

    axes[0].legend(
        pass_legend_lines,
        pass_legend_labels,
        loc="upper center",
        bbox_to_anchor=(0.22, -0.02),
        ncol=1,
        facecolor=BackgroundColor,
        frameon=False,
        labelcolor=TextColor,
    )

    axes[0].text(
        50,
        -5,
        "Data from Opta",
        ha="center",
        fontsize=9,
        color=TextColor,
    )
    distance_text = (
        f"{distance_covered_km:.1f}km (#{int(distance_rank)})"
        if pd.notna(distance_covered_km) and pd.notna(distance_rank)
        else "N/A"
    )
    sprint_text = (
        f"{int(sprint_count)} (#{int(sprint_rank)})"
        if pd.notna(sprint_count) and pd.notna(sprint_rank)
        else "N/A"
    )

    # Restore the original left-pitch opponent and impact layout.
    axes[0].text(
        25,
        -9,
        "Opponent:",
        ha="center",
        fontsize=14,
        color=TextColor,
    )
    axes[0].text(
        25,
        -13,
        opponentname,
        ha="center",
        fontsize=14,
        color=TextColor,
        fontweight="bold",
    )
    axes[0].text(
        25,
        -19,
        "Player Ranking:",
        ha="center",
        fontsize=14,
        color=TextColor,
    )
    axes[0].text(
        25,
        -23,
        ranking,
        ha="center",
        fontsize=14,
        color=TextColor,
        fontweight="bold",
    )

    # Put the two physical metrics on the left side beneath the middle pitch.
    axes[1].text(
        94,
        -9,
        "Distance Covered:",
        ha="center",
        fontsize=14,
        color=TextColor,
    )
    axes[1].text(
        94,
        -13,
        distance_text,
        ha="center",
        fontsize=14,
        color=TextColor,
        fontweight="bold",
    )
    axes[1].text(
        94,
        -19,
        "No. of Sprints:",
        ha="center",
        fontsize=14,
        color=TextColor,
    )
    axes[1].text(
        94,
        -23,
        sprint_text,
        ha="center",
        fontsize=14,
        color=TextColor,
        fontweight="bold",
    )

    axes[1].text(
        50,
        -5,
        "All events plotted",
        ha="center",
        fontsize=9,
        color=TextColor,
    )
    axes[2].text(
        50,
        -5,
        "Green shows successful action, red shows unsuccessful",
        ha="center",
        fontsize=9,
        color=TextColor,
    )

    if teamimage is not None:
        add_image(
            teamimage,
            fig,
            left=0.5425,
            bottom=-0.049,
            width=0.055,
            alpha=1,
            interpolation="hanning",
        )

    if wtaimaged is not None:
        add_image(
            wtaimaged,
            fig,
            left=0.48715,
            bottom=-0.029,
            width=0.050875,
            alpha=1,
            interpolation="hanning",
        )

    if player_face is not None:
        add_image(player_face,fig,left=0.597,bottom=-0.029,width=0.0365,interpolation="hanning")

    return fig


def keeper_shot_locations(shots_faced):
    shots_faced = shots_faced.copy()
    if "onGoalShot" not in shots_faced:
        shots_faced["onGoalShot"] = None
    shots_faced["onGoalShot"] = (
        shots_faced["onGoalShot"]
        .apply(parse_on_goal_shot)
    )

    shots_faced = shots_faced.loc[
        shots_faced["onGoalShot"].notna()
    ].copy()

    shots_faced["goal_x"] = (
        shots_faced["onGoalShot"]
        .apply(
            lambda value: value.get("x")
            if isinstance(value, dict)
            else np.nan
        )
    )

    shots_faced["goal_y"] = (
        shots_faced["onGoalShot"]
        .apply(
            lambda value: value.get("y")
            if isinstance(value, dict)
            else np.nan
        )
    )

    shots_faced["zoomratio"] = (
        shots_faced["onGoalShot"]
        .apply(
            lambda value: value.get(
                "zoomRatio",
                1,
            )
            if isinstance(value, dict)
            else 1
        )
    )

    for column in [
        "goal_x",
        "goal_y",
        "zoomratio",
        "expectedGoalsOnTarget",
    ]:
        shots_faced[column] = pd.to_numeric(
            shots_faced[column],
            errors="coerce",
        )

    shots_faced["zoomratio"] = (
        shots_faced["zoomratio"].fillna(1)
    )

    # Coordinate corrections from the original goal-placement code.
    left_mask = (
        shots_faced["goal_x"] < 0.0001
    )
    shots_faced.loc[
        left_mask,
        "goal_x",
    ] = (
        -0.5
        * shots_faced.loc[
            left_mask,
            "zoomratio",
        ]
    )

    high_mask = (
        shots_faced["goal_y"] > 0.67
    )
    shots_faced.loc[
        high_mask,
        "goal_y",
    ] = (
        0.67
        + (
            0.33
            * shots_faced.loc[
                high_mask,
                "zoomratio",
            ]
        )
    )

    if "isBlocked" in shots_faced.columns:
        blocked_mask = boolean_series(
            shots_faced["isBlocked"]
        )
    else:
        blocked_mask = pd.Series(
            False,
            index=shots_faced.index,
        )

    saves = shots_faced.loc[
        shots_faced["typeId"].eq(
            "Attempt Saved"
        )
        & ~blocked_mask
    ].copy()

    goals = shots_faced.loc[
        shots_faced["typeId"].eq(
            "Goal"
        )
    ].copy()

    return saves, goals


def create_goalkeeper_overview(
    goalkeeper_name, goalkeeper_events, shots_faced, teamimage, wtaimaged,
    player_face=None,
):
    completed_passes = goalkeeper_events.loc[
        goalkeeper_events["typeId"].eq(
            "Pass"
        )
        & goalkeeper_events["outcome"].eq(
            "Successful"
        )
    ].copy()

    incomplete_passes = goalkeeper_events.loc[
        goalkeeper_events["typeId"].eq(
            "Pass"
        )
        & goalkeeper_events["outcome"].eq(
            "Unsuccessful"
        )
    ].copy()

    shot_assists = goalkeeper_events.loc[
        goalkeeper_events["typeId"].eq(
            "Pass"
        )
        & goalkeeper_events["keyPass"].eq(1)
    ].copy()

    goal_assists = goalkeeper_events.loc[
        goalkeeper_events["typeId"].eq(
            "Pass"
        )
        & goalkeeper_events["assist"].eq(1)
    ].copy()

    carries = goalkeeper_events.loc[
        goalkeeper_events["typeId"].eq(
            "Carry"
        )
    ].copy()

    for column in [
        "x",
        "y",
        "end_x",
        "end_y",
    ]:
        carries[column] = pd.to_numeric(
            carries[column],
            errors="coerce",
        )

    carries = carries.loc[
        carries["end_y"].between(
            0,
            100,
            inclusive="neither",
        )
        & carries["end_x"].between(
            0,
            99.5,
            inclusive="neither",
        )
        & carries["x"].gt(2.5)
    ].copy()

    carries["y_diff"] = (
        carries["y"] - carries["end_y"]
    )
    carries["x_diff"] = (
        carries["x"] - carries["end_x"]
    )

    carries = carries.loc[
        carries["y_diff"].between(
            -25,
            25,
            inclusive="neither",
        )
        & carries["x_diff"].between(
            -25,
            25,
            inclusive="neither",
        )
    ].copy()

    saves, goals = keeper_shot_locations(shots_faced)

    # ------------------------------------------------------------------------
    # Goals Prevented
    # ------------------------------------------------------------------------

    relevant_xgot = pd.concat(
        [
            saves["expectedGoalsOnTarget"],
            goals["expectedGoalsOnTarget"],
        ],
        ignore_index=True,
    )

    total_xgot_faced = float(
        pd.to_numeric(
            relevant_xgot,
            errors="coerce",
        )
        .fillna(0)
        .sum()
    )

    goals_conceded = int(
        len(goals)
    )

    goals_prevented = (
        total_xgot_faced
        - goals_conceded
    )

    size_factor = 800

    save_sizes = (
        saves["expectedGoalsOnTarget"]
        .fillna(0)
        .clip(lower=0.01)
        * size_factor
    )

    goal_sizes = (
        goals["expectedGoalsOnTarget"]
        .fillna(0)
        .clip(lower=0.01)
        * size_factor
    )

    # ------------------------------------------------------------------------
    # Figure layout
    # ------------------------------------------------------------------------

    fig = plt.figure(
        figsize=(14, 10),
        facecolor=BackgroundColor,
    )

    passing_axis = fig.add_axes([
        0.025,
        0.075,
        0.415,
        0.865,
    ])

    goal_axis = fig.add_axes([
        0.525,
        0.500,
        0.380,
        0.220,
    ])

    # ------------------------------------------------------------------------
    # Passes and carries
    # ------------------------------------------------------------------------

    passing_pitch = VerticalPitch(
        pitch_type="opta",
        pitch_color=PitchColor,
        line_color=PitchLineColor,
    )

    passing_pitch.draw(
        ax=passing_axis,
        constrained_layout=False,
        tight_layout=False,
    )

    passing_axis.set_title(
        f"{goalkeeper_name} - Passes & Carries",
        fontproperties=title_font,
        color=TextColor,
        pad=12,
    )

    plot_comet_lines(
        passing_axis,
        completed_passes,
        "green",
    )
    plot_comet_lines(
        passing_axis,
        incomplete_passes,
        "red",
    )
    plot_comet_lines(
        passing_axis,
        shot_assists,
        "orange",
    )
    plot_comet_lines(
        passing_axis,
        carries,
        "purple",
    )
    plot_comet_lines(
        passing_axis,
        goal_assists,
        "blue",
        number_of_segments=10,
        linewidth=2,
    )

    fig.text(
        0.232,
        0.052,
        "Data from Opta",
        ha="center",
        va="center",
        fontsize=11,
        color=TextColor,
    )

    # ------------------------------------------------------------------------
    # Goal frame and net
    # ------------------------------------------------------------------------

    goal_axis.set_facecolor(
        BackgroundColor
    )

    goal_axis.plot(
        [0, 0],
        [0, 0.66],
        color=TextColor,
        linewidth=4,
        solid_capstyle="butt",
        zorder=5,
    )
    goal_axis.plot(
        [2, 2],
        [0, 0.66],
        color=TextColor,
        linewidth=4,
        solid_capstyle="butt",
        zorder=5,
    )
    goal_axis.plot(
        [0, 2],
        [0.66, 0.66],
        color=TextColor,
        linewidth=4,
        solid_capstyle="butt",
        zorder=5,
    )

    for net_x in np.arange(
        0.2,
        2.0,
        0.2,
    ):
        goal_axis.plot(
            [net_x, net_x],
            [0, 0.66],
            color="#a7a7a7",
            linewidth=0.55,
            alpha=0.65,
            zorder=1,
        )

    for net_y in np.arange(
        0.0825,
        0.66,
        0.0825,
    ):
        goal_axis.plot(
            [0, 2],
            [net_y, net_y],
            color="#a7a7a7",
            linewidth=0.55,
            alpha=0.65,
            zorder=1,
        )

    # Saves: filled green circles
    goal_axis.scatter(
        saves["goal_x"],
        saves["goal_y"],
        s=save_sizes,
        marker="o",
        c=SaveColor,
        edgecolors="white",
        linewidths=1.25,
        alpha=0.95,
        zorder=10,
    )

    # Conceded goals: filled red stars
    goal_axis.scatter(
        goals["goal_x"],
        goals["goal_y"],
        s=goal_sizes,
        marker="*",
        c=GoalColor,
        edgecolors="red",
        linewidths=1.25,
        alpha=1,
        zorder=11,
    )

    goal_axis.set_xlim(
        -0.02,
        2.02,
    )
    goal_axis.set_ylim(
        -0.02,
        0.68,
    )
    goal_axis.set_xticks([])
    goal_axis.set_yticks([])

    for side in [
        "top",
        "right",
        "left",
        "bottom",
    ]:
        goal_axis.spines[
            side
        ].set_visible(False)

    # ------------------------------------------------------------------------
    # Goals Prevented summary
    # ------------------------------------------------------------------------

    fig.text(
        0.715,
        0.450,
        "Goals Prevented",
        ha="center",
        va="center",
        fontsize=17,
        color=TextColor,
    )

    fig.text(
        0.715,
        0.405,
        f"{goals_prevented:+.2f}",
        ha="center",
        va="center",
        fontsize=26,
        fontweight="bold",
        color=(
            SaveColor
            if goals_prevented >= 0
            else GoalColor
        ),
    )

    summary_text = (
        f"xGOT faced: {total_xgot_faced:.2f}  |  "
        f"Saves: {len(saves)}  |  "
        f"Goals conceded: {goals_conceded}"
    )

    fig.text(
        0.715,
        0.365,
        summary_text,
        ha="center",
        va="center",
        fontsize=10,
        color=TextColor,
    )

    # ------------------------------------------------------------------------
    # Save and goal marker key
    # ------------------------------------------------------------------------

    marker_key_axis = fig.add_axes([
        0.640,
        0.315,
        0.260,
        0.040,
    ])
    marker_key_axis.set_axis_off()

    marker_key_axis.scatter(
        [0.10],
        [0.50],
        s=115,
        marker="o",
        c=SaveColor,
        edgecolors="white",
        linewidths=1,
    )
    marker_key_axis.text(
        0.15,
        0.50,
        "Save",
        ha="left",
        va="center",
        fontsize=10,
        color=TextColor,
    )

    marker_key_axis.scatter(
        [0.55],
        [0.50],
        s=140,
        marker="*",
        c=GoalColor,
        edgecolors="white",
        linewidths=1,
    )
    marker_key_axis.text(
        0.61,
        0.50,
        "Goal conceded",
        ha="left",
        va="center",
        fontsize=10,
        color=TextColor,
    )

    marker_key_axis.set_xlim(
        0,
        1,
    )
    marker_key_axis.set_ylim(
        0,
        1,
    )

    # ------------------------------------------------------------------------
    # Pass and carry legend
    # ------------------------------------------------------------------------

    passing_legend_labels = [
        "Completed Pass",
        "Incomplete Pass",
        "Shot Assist",
        "Assist",
        "Ball Carry",
    ]

    passing_legend_colours = [
        "green",
        "red",
        "orange",
        "blue",
        "purple",
    ]

    passing_legend_handles = [
        Line2D(
            [0],
            [0],
            color=colour,
            linewidth=3,
        )
        for colour in passing_legend_colours
    ]

    fig.legend(
        passing_legend_handles,
        passing_legend_labels,
        loc="upper left",
        bbox_to_anchor=(
            0.475,
            0.305,  # moved down to align with both logos
        ),
        frameon=False,
        ncol=1,
        labelcolor=TextColor,
        fontsize=11,
        handlelength=2,
        handletextpad=0.7,
    )

    # ------------------------------------------------------------------------
    # Logos
    # ------------------------------------------------------------------------

    if wtaimaged is not None:
        add_image(
            wtaimaged,
            fig,
            left=0.650,
            bottom=0.175,
            width=0.125,
            alpha=1,
            interpolation="hanning",
        )

    if teamimage is not None:
        add_image(
            teamimage,
            fig,
            left=0.835,
            bottom=0.145,
            width=0.120,
            alpha=1,
            interpolation="hanning",
        )

    if player_face is not None:
        add_image(player_face,fig,left=0.665,bottom=0.770,width=0.095,interpolation="hanning")

    return fig


def physical_summary(roster, selected):
    """Match-wide ranks with ties sharing the best applicable rank."""
    result = []
    for metric in ("physical_distanceCoveredKm", "physical_numberOfSprints"):
        value = rank = np.nan
        if metric in roster and not selected.empty:
            values = pd.to_numeric(roster[metric], errors="coerce")
            index = selected.index[0]
            value = values.loc[index]
            rank = values.rank(method="min", ascending=False).loc[index]
        result.extend((value, rank))
    return result


def match_rankings(roster, metric):
    scores = pd.to_numeric(roster.get(metric), errors="coerce")
    minutes = pd.to_numeric(roster.get("minutes_played"), errors="coerce")
    return (
        roster.assign(_performance=scores, _minutes=minutes)
        .loc[lambda rows: rows._minutes.gt(0)]
        .dropna(subset=["_performance"])
        .sort_values("_performance", ascending=False, kind="stable")
    )


def player_ranking(rankings, selected):
    matches = rankings.index.isin(selected.index).nonzero()[0]
    return f"#{matches[0] + 1} of {len(rankings)}" if len(matches) else "N/A"


def overview_image(events, name, team, opponent, badge, brand_path, roster, rankings):
    team_events = events.loc[events.team.eq(team)]
    source_team = team_events.team_name.iloc[0]
    player = team_events.loc[team_events.playerName.eq(name)].copy()
    if "next_player_position" not in player:
        # The live processor calls this field next_position.
        next_position = events.get("next_position", pd.Series(pd.NA, index=events.index))
        player["next_player_position"] = next_position.reindex(player.index)
    for column in ("x", "y", "end_x", "end_y", "keyPass", "assist"):
        player[column] = pd.to_numeric(player.get(column, np.nan), errors="coerce")
    player = player.loc[
        ~player.typeId.isin(["Out", "Player off", "Player on"])
        & ~(player.x.fillna(0).eq(0) & player.y.fillna(0).eq(0))
    ]
    from possession_chains import supported_carries

    valid_carries = supported_carries(team_events).index
    player = player.loc[~player.typeId.eq("Carry") | player.index.isin(valid_carries)]
    teamimage = None
    if badge:
        with Image.open(BytesIO(base64.b64decode(badge.split(",", 1)[1]))) as image:
            teamimage = image.convert("RGBA")
    with Image.open(brand_path) as image:
        wtaimaged = image.convert("RGBA")

    roster_names = roster.get("player_name", roster.get("playerName", pd.Series("", index=roster.index)))
    roster_team = roster.get("team_name", pd.Series("", index=roster.index))
    selected = roster.loc[roster_team.isin([team, source_team]) & roster_names.eq(name)]
    positions = [
        frame[column].map(is_goalkeeper_position).any()
        for frame, columns in (
            (selected, ("position", "position1")),
            (player, ("playing_position",)),
        )
        for column in columns if column in frame
    ]
    from player_faces import portrait
    player_face=portrait(selected)
    shots_available = {"playing_GK", "onGoalShot"}.issubset(events.columns)
    ranking = player_ranking(rankings, selected)
    if any(positions):
        shots = events.loc[events.playing_GK.eq(name) & events.team.ne(team)].copy() if shots_available else events.iloc[:0].copy()
        for column in ("onGoalShot", "expectedGoalsOnTarget"):
            if column not in shots:
                shots[column] = np.nan
        fig = create_goalkeeper_overview(name, player, shots, teamimage, wtaimaged,player_face=player_face)
    else:
        fig = create_player_overview(
            name, player, opponent, teamimage, wtaimaged,
            ranking,
            *physical_summary(roster, selected),
            player_face=player_face,
        )

    buffer = BytesIO()
    try:
        fig.savefig(buffer, format="png", dpi=150, facecolor=BackgroundColor, bbox_inches="tight")
    finally:
        plt.close(fig)
    return buffer.getvalue(), len(player), any(positions) and not shots_available
