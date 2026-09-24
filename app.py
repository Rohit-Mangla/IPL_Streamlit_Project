import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

# Page config
st.set_page_config(page_title="IPL Matches 2008-2020 Dashboard",
                   page_icon="🏏", 
                   layout="wide")


# Data loading & cleaning
@st.cache_data
def load_data():
    df = pd.read_csv("IPL Matches 2008-2020.csv")
    df["date"] = pd.to_datetime(df["date"])
    df["season"] = df["date"].dt.year

    # Standardize team names that changed across seasons
    name_fix = {
        "Delhi Daredevils": "Delhi Capitals",
        "Deccan Chargers": "Sunrisers Hyderabad",
        "Kings XI Punjab": "Punjab Kings",
        "Rising Pune Supergiants": "Rising Pune Supergiant",
    }
    for col in ["team1", "team2", "toss_winner", "winner"]:
        df[col] = df[col].replace(name_fix)

    # Drop matches with no result (rain-affected, no winner)
    df = df.dropna(subset=["winner"]).copy()

    # Helper column: did the toss winner also win the match?
    df["toss_win_match_win"] = df["toss_winner"] == df["winner"]

    return df


df = load_data()

st.title("🏏 IPL Matches 2008–2020 Dashboard")

# Sidebar filters 

st.sidebar.header("Filters")

all_seasons = sorted(df["season"].unique())
all_teams = sorted(df["team1"].unique())
all_venues = sorted(df["venue"].unique())

if "seasons_sel" not in st.session_state:
    st.session_state.seasons_sel = all_seasons
if "teams_sel" not in st.session_state:
    st.session_state.teams_sel = all_teams
if "venues_sel" not in st.session_state:
    st.session_state.venues_sel = all_venues


def reset_filters():
    st.session_state.seasons_sel = all_seasons
    st.session_state.teams_sel = all_teams
    st.session_state.venues_sel = all_venues


selected_seasons = st.sidebar.multiselect(
    "Season", options=all_seasons, key="seasons_sel"
)
selected_teams = st.sidebar.multiselect(
    "Team", options=all_teams, key="teams_sel"
)
selected_venues = st.sidebar.multiselect(
    "Venue", options=all_venues, key="venues_sel"
)
st.sidebar.button("🔄 Reset Filters", on_click=reset_filters)

# Apply filters
filtered_df = df[
    (df["season"].isin(selected_seasons))
    & (df["venue"].isin(selected_venues))
    & (df["team1"].isin(selected_teams) | df["team2"].isin(selected_teams))
]

# KPI cards
total_matches_all = df["id"].nunique()
total_seasons_all = df["season"].nunique()

f_matches = filtered_df["id"].nunique()
f_teams = pd.concat([filtered_df["team1"],filtered_df["team2"]]).nunique()
f_venues = filtered_df["venue"].nunique()
f_seasons = filtered_df["season"].nunique()

c1, c2 = st.columns(2)
c1.metric("All-Time Matches", total_matches_all)
c2.metric("All-Time Seasons", total_seasons_all)

st.caption("Filtered totals")                   
k1, k2, k3, k4 = st.columns(4)
k1.metric("Matches", f_matches)
k2.metric("Distinct Teams", f_teams)
k3.metric("Distinct Venues", f_venues)
k4.metric("Seasons", f_seasons)

st.divider()

if filtered_df.empty:
    st.warning("No data matches the current filters. Adjust the sidebar and try again.")
    st.stop()

# Tabs
 
tab_overview, tab_toss, tab_players_venues, tab_h2h = st.tabs(
    ["📅 League Overview", "🪙 Toss Strategy", "🏟️ Players & Venues", "⚔️ Head-to-Head"]
)

# MAIL 1 — League Overview

with tab_overview:

    st.subheader("Matches Played per Season")
    matches_per_season = filtered_df.groupby("season")["id"].nunique()
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(matches_per_season.index.astype(str), matches_per_season.values, color="#1f77b4")
    ax.set_xlabel("Season")
    ax.set_ylabel("Matches")
    plt.xticks(rotation=45)
    st.pyplot(fig)

    st.subheader("Most Successful Teams (Total Wins)")
    wins_by_team = filtered_df["winner"].value_counts().sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=(9,4.5))
    ax.barh(wins_by_team.index, wins_by_team.values, color="#2ca02c")
    ax.set_xlabel("Total Wins")
    st.pyplot(fig)

    st.subheader("Win Rate (%) by Team")
    played = pd.concat([filtered_df["team1"], filtered_df["team2"]]).value_counts().rename("played")
    won = filtered_df["winner"].value_counts().rename("won")
    win_rate = pd.concat([played, won], axis=1).fillna(0)
    win_rate["win_pct"] = (win_rate["won"] / win_rate["played"] * 100).round(1)
    win_rate = win_rate.sort_values("win_pct")
    fig, ax = plt.subplots(figsize=(9,4.5))
    ax.barh(win_rate.index, win_rate["win_pct"], color="#ff7f0e")
    ax.set_xlabel("Win Rate (%)")
    st.pyplot(fig)

# MAIL 2 — Toss Strategy

with tab_toss:

    st.subheader("Toss Decision Split (Bat vs Field)")
    toss_split = filtered_df["toss_decision"].value_counts()
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.pie(toss_split.values, labels=toss_split.index, autopct="%1.1f%%",
           colors=["#1f77b4", "#ff7f0e"], startangle=90)
    ax.set_title("Toss Decision Split")
    st.pyplot(fig)

    st.subheader("Does Winning the Toss Help?")
    overall_conv = filtered_df["toss_win_match_win"].mean() * 100
    st.metric("Overall Toss → Match Win Conversion", f"{overall_conv:.1f}%")

    conv_by_season = (
        filtered_df.groupby("season")["toss_win_match_win"].mean().sort_index() * 100
    )
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(conv_by_season.index.astype(str), conv_by_season.values, marker="o", color="#d62728")
    ax.set_xlabel("Season")
    ax.set_ylabel("Toss → Win Conversion (%)")
    ax.axhline(50, color="gray", linestyle="--", linewidth=1)
    plt.xticks(rotation=45)
    st.pyplot(fig)

    st.subheader("Bat-First vs Field-First: Match Win Rate")
    decision_win_rate = (
        filtered_df.groupby("toss_decision")["toss_win_match_win"].mean() * 100
    )
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.bar(decision_win_rate.index, decision_win_rate.values, color=["#9467bd", "#8c564b"])
    ax.set_ylabel("Win Rate (%)")
    st.pyplot(fig)

    st.subheader("Toss Success by Team")
    toss_by_team = filtered_df[filtered_df["toss_winner"].isin(selected_teams)]
    team_toss_conv = (
        toss_by_team.groupby("toss_winner")["toss_win_match_win"].mean().sort_values() * 100
    )
    fig, ax = plt.subplots(figsize=(9, max(4.5, 0.35 * len(team_toss_conv))))
    ax.barh(team_toss_conv.index, team_toss_conv.values, color="#17becf")
    ax.set_xlabel("Toss → Win Conversion (%)")
    st.pyplot(fig)

# MAIL 3 — Players & Venues 

with tab_players_venues:

    st.subheader("Top 10 Player of the Match Awards")
    top_players = filtered_df["player_of_match"].value_counts().head(10).sort_values()
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(top_players.index, top_players.values, color="#e377c2")
    ax.set_xlabel("Awards")
    st.pyplot(fig)

    st.subheader("Busiest Venues & Cities")
    colA, colB = st.columns(2)

    top_venues = filtered_df["venue"].value_counts().head(10).sort_values()
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.barh(top_venues.index, top_venues.values, color="#1f77b4")
    ax.set_xlabel("Matches")
    ax.set_title("Top Venues")
    colA.pyplot(fig)

    top_cities = filtered_df["city"].dropna().value_counts().head(10).sort_values()
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.barh(top_cities.index, top_cities.values, color="#2ca02c")
    ax.set_xlabel("Matches")
    ax.set_title("Top Cities")
    colB.pyplot(fig)

    st.subheader("Home Advantage at Busiest Venues")
    top5_venues = filtered_df["venue"].value_counts().head(5).index
    venue_df = filtered_df[filtered_df["venue"].isin(top5_venues)]
    wins_pivot = (
        venue_df.groupby(["venue", "winner"]).size().unstack(fill_value=0)
    )
    # Keep only the teams with the most total wins across these venues for readability
    top_win_teams = wins_pivot.sum().sort_values(ascending=False).head(6).index
    wins_pivot = wins_pivot[top_win_teams]

    fig, ax = plt.subplots(figsize=(10, 5))
    wins_pivot.plot(kind="bar", ax=ax)
    ax.set_ylabel("Wins")
    ax.set_xlabel("Venue")
    plt.xticks(rotation=30, ha="right")
    ax.legend(title="Team", bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
    st.pyplot(fig)

    st.subheader("Win Margins: Runs vs Wickets")
    margin_df = filtered_df.dropna(subset=["result_margin"])
    margin_df = margin_df[margin_df["result"].isin(["runs", "wickets"])]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for result_type, color in [("runs", "#1f77b4"), ("wickets", "#ff7f0e")]:
        subset = margin_df[margin_df["result"] == result_type]["result_margin"]
        ax.hist(subset, bins=15, alpha=0.6, label=result_type, color=color)
    ax.set_xlabel("Result Margin")
    ax.set_ylabel("Number of Matches")
    ax.legend()
    st.pyplot(fig)

# MAIL 4 — Head-to-Head & Interactivity 

with tab_h2h:

    st.subheader("Head-to-Head Explorer")
    col1, col2 = st.columns(2)
    team_a = col1.selectbox("Select Team A", options=all_teams, index=0)
    team_b = col2.selectbox("Select Team B", options=all_teams, index=1 if len(all_teams) > 1 else 0)

    if team_a == team_b:
        st.info("Pick two different teams to compare.")
    else:
        h2h_df = filtered_df[
            ((filtered_df["team1"] == team_a) & (filtered_df["team2"] == team_b))
            | ((filtered_df["team1"] == team_b) & (filtered_df["team2"] == team_a))
        ]

        matches_played = len(h2h_df)
        wins_a = (h2h_df["winner"] == team_a).sum()
        wins_b = (h2h_df["winner"] == team_b).sum()

        m1, m2, m3 = st.columns(3)
        m1.metric("Matches Played", matches_played)
        m2.metric(f"{team_a} Wins", wins_a)
        m3.metric(f"{team_b} Wins", wins_b)

        if matches_played > 0:
            fig, ax = plt.subplots(figsize=(5, 4))
            ax.bar([team_a, team_b], [wins_a, wins_b], color=["#1f77b4", "#d62728"])
            ax.set_ylabel("Wins")
            ax.set_title(f"{team_a} vs {team_b}")
            st.pyplot(fig)
        else:
            st.warning("These two teams haven't played each other under the current filters.")