import streamlit as st
import pandas as pd
from statsbombpy import sb
from mplsoccer import VerticalPitch, Pitch
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

warnings.filterwarnings("ignore")

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Rodri Euro 2024 Analysis", layout="wide")

st.title("Soccermatics Pro: The 45-Minute Masterclass")
st.markdown("""
*Tactical Analysis of Rodri vs. England (Euro 2024 Final)* By Hannah Nyarkoa Oduro

In the Euro 2024 Final, Rodri was substituted at halftime. This app investigates how his *45-minute performance* compared to the full-match output of the England midfield.
""")

#  1. DATA LOADING (Cached) 
@st.cache_data
def load_data():
    # Euro 2024: Comp 55, Season 282
    match_id = 3032961 
    
    # Fetch matches to find the final
    matches = sb.matches(competition_id=55, season_id=282)
    final_match = matches[
        (matches['home_team'] == "Spain") & (matches['away_team'] == "England")
    ]
    
    if not final_match.empty:
        final_id = final_match.iloc[0]['match_id']
        events = sb.events(match_id=final_id)
        return events
    else:
        return pd.DataFrame() # Fallback

with st.spinner('Fetching StatsBomb Data (Euro 2024 Final)...'):
    df = load_data()

if df.empty:
    st.error("Could not find the Spain vs England Final data.")
    st.stop()

#  2. DATA PREPARATION 
rodri = "Rodrigo Hernández Cascante"
england_midfielders = ["Declan Rice", "Kobbie Mainoo"]

# Rodri Events
rodri_events = df[(df['player'] == rodri) & (df['period'] == 1)] # First half only

# Comparison Stats (Simple aggregation)
def get_stats(player_name):
    p_events = df[df['player'] == player_name]
    passes = p_events[p_events['type'] == 'Pass']
    succ_passes = passes[passes['pass_outcome'].isna()]
    return len(succ_passes)

rodri_pass_count = get_stats(rodri)
rice_pass_count = get_stats("Declan Rice")
mainoo_pass_count = get_stats("Kobbie Mainoo")

#  3. LAYOUT & VISUALIZATION 

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Pitch Visualisation")
    viz_type = st.radio("Select View:", ["Passing Network", "Defensive Actions"], horizontal=True)

    # DATA PREP FOR COMPATIBILITY 
    rodri_events['x'] = rodri_events['location'].apply(lambda loc: loc[0] if isinstance(loc, list) else None)
    rodri_events['y'] = rodri_events['location'].apply(lambda loc: loc[1] if isinstance(loc, list) else None)
    rodri_events['type_name'] = rodri_events['type']

    if viz_type == "Passing Network":
        # Keep the passing visualization simple
        pitch = VerticalPitch(pitch_type='statsbomb', pitch_color='#22312b', line_color='#c7d5cc')
        fig, ax = pitch.draw(figsize=(10, 8))
        
        passes = rodri_events[(rodri_events['type'] == 'Pass') & (rodri_events['pass_outcome'].isna())]
        pitch.lines(passes.location.str[0], passes.location.str[1],
                    passes.pass_end_location.str[0], passes.pass_end_location.str[1],
                    ax=ax, color='#ffd700', lw=3, alpha=0.6, comet=True, label='Completed Passes')
        pitch.scatter(passes.location.str[0], passes.location.str[1], 
                      ax=ax, color='#ffd700', edgecolors='white', s=50)
        st.pyplot(fig)

    elif viz_type == "Defensive Actions":
        
        # Filter Rodri's defensive actions
        rodri_def = rodri_events[
            rodri_events['type_name'].isin(['Pressure', 'Tackle', 'Interception'])
        ]

        # Setup figure
        fig, ax = plt.subplots(figsize=(10, 7))
        fig.set_facecolor('#FFFFFF')

        # Create pitch
        pitch = Pitch(
            pitch_type='statsbomb',
            pitch_color='#22312b',
            line_color='#c7d5cc'
        )
        pitch.draw(ax=ax)

        # Plot each type of defensive action with a different marker
        pitch.scatter(
            rodri_def.loc[rodri_def['type_name']=='Pressure', 'x'],
            rodri_def.loc[rodri_def['type_name']=='Pressure', 'y'],
            s=80, color='#ff4b4b', edgecolors='white', linewidth=1.2, alpha=0.7, ax=ax,
            label='Pressures'
        )

        pitch.scatter(
            rodri_def.loc[rodri_def['type_name']=='Interception', 'x'],
            rodri_def.loc[rodri_def['type_name']=='Interception', 'y'],
            s=100, marker='s', color='#ffc107', edgecolors='black', linewidth=1.2, alpha=0.8, ax=ax,
            label='Interceptions'
        )
        pitch.scatter(
            rodri_def.loc[rodri_def['type_name']=='Tackle', 'x'],
            rodri_def.loc[rodri_def['type_name']=='Tackle', 'y'],
            s=120, marker='^', color='#4bb3fd', edgecolors='black', linewidth=1.2, alpha=0.8, ax=ax,
            label='Tackles'
        )

        # Title
        ax.set_title(
            "Rodri – Defensive Actions vs England",
            fontsize=18, color='black', fontweight='bold', pad=15
        )

        # Legend
        legend = ax.legend(facecolor='#1e1e1e', edgecolor='white', fontsize=10)
        for text in legend.get_texts():
            text.set_color('white')
            
        #  END OF CUSTOM CODE 
        
        st.pyplot(fig)

with col2:
    st.subheader("Statistical Comparison")
    st.markdown("Passes Completed (Full Match Context)")
    
    # Simple Bar Chart Data
    comp_data = pd.DataFrame({
        'Player': ['Rodri (45 mins)', 'Rice (90 mins)', 'Mainoo (70 mins)'],
        'Passes': [rodri_pass_count, rice_pass_count, mainoo_pass_count]
    })
    
    fig2, ax2 = plt.subplots(figsize=(5, 4))
    sns.barplot(data=comp_data, x='Player', y='Passes', palette=['#ffd700', '#c7d5cc', '#c7d5cc'], ax=ax2)
    ax2.set_ylabel("Successful Passes")
    st.pyplot(fig2)

    st.markdown("""
    *Key Insight:* Despite playing only half the match, Rodri nearly matched the volume of Declan Rice and doubled Kobbie Mainoo's output.
    """)
