import streamlit as st 
import pandas as pd
import re
import numpy as np
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder

def initialize_teams(num_teams):
    for i in range(1,num_teams+1):
        positions = ['QB', 'RB1', 'RB2', 'WR1', 'WR2', 'TE', 'FLEX', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7']
        if f'{i}' not in st.session_state: st.session_state[f'{i}'] = {pos: None for pos in positions}

def handle_num_teams():
    if st.session_state.num_teams_key:
        st.session_state['num_teams'] = st.session_state.num_teams_key
        st.session_state['user_first_pick'] = 0 

def handle_user_first_pick():
    if st.session_state.ufp_key:
        st.session_state['user_first_pick'] = st.session_state.ufp_key

def handle_make_pick():
    if st.session_state.pick_key: # If make pick button pressed
        st.session_state.pick_num = st.session_state.pick_num + 1 #Increment overall pick number
        #Moves picked player to the roster of the current team picking 
        st.session_state[st.session_state.current_team_picking] = assign_player(st.session_state[st.session_state.current_team_picking], st.session_state.pick_sel_key, st.session_state.df)
        #Removes picked player from dataframe
        st.session_state.df = st.session_state.df[st.session_state.df['Player'] != st.session_state.pick_sel_key]

def assign_player(team, player, df):
    position = df.loc[df['Player'] == player, 'POS'].values[0]
    if position == 'QB' and team['QB'] is None:
        team['QB'] = player
    elif position == 'RB':
        if team['RB1'] is None:
            team['RB1'] = player
        elif team['RB2'] is None:
            team['RB2'] = player
        elif team['FLEX'] is None:
            team['FLEX'] = player
        else:
            for i in range(1, 8):
                if team[f'B{i}'] is None:
                    team[f'B{i}'] = player
                    break
    elif position == 'WR':
        if team['WR1'] is None:
            team['WR1'] = player
        elif team['WR2'] is None:
            team['WR2'] = player
        elif team['FLEX'] is None:
            team['FLEX'] = player
        else:
            for i in range(1, 8):
                if team[f'B{i}'] is None:
                    team[f'B{i}'] = player
                    break
    elif position == 'TE' and team['TE'] is None:
        team['TE'] = player
    else:
        for i in range(1, 8):
            if team[f'B{i}'] is None:
                team[f'B{i}'] = player
                break
    return team


def create_pick_order():
    pick_order = []

    for i in range(1, st.session_state.num_teams * 14 + 1):
        if i % (2 * st.session_state.num_teams) <= st.session_state.num_teams:
            pick_order.append(i % st.session_state.num_teams if i % st.session_state.num_teams != 0 else st.session_state.num_teams)
        else:
            pick_order.append(2 * st.session_state.num_teams - i % (2 * st.session_state.num_teams) + 1)
    
    return pick_order

def is_starting_position(position, team):
    if position == 'QB' and team['QB'] is None:
        return True
    elif position == 'RB' and (team['RB1'] is None or team['RB2'] is None or team['FLEX'] is None):
        return True
    elif position == 'WR' and (team['WR1'] is None or team['WR2'] is None or team['FLEX'] is None):
        return True
    elif position == 'TE' and team['TE'] is None:
        return True
    else:
        return False

def teams_need_position(pos, teams_to_check):
    count = 0 
    for i in teams_to_check:
        if pos == 'RB':
            if st.session_state[f'{i}']['RB1'] is None or st.session_state[f'{i}']['RB2'] is None or (st.session_state[f'{i}']['FLEX'] is None and not st.session_state[f'{i}']['WR1'] and not st.session_state[f'{i}']['WR2']):
                count += 1
        elif pos == 'WR':
            if st.session_state[f'{i}']['WR1'] is None or st.session_state[f'{i}']['WR2'] is None or (st.session_state[f'{i}']['FLEX'] is None and not st.session_state[f'{i}']['RB1'] and not st.session_state[f'{i}']['RB2']):
                count += 1
        else:  # For 'QB' and 'TE'
            if st.session_state[f'{i}'][pos] is None:
                count += 1
    return count

def calculate_scores(df, teams_to_check):
    #df['Score'] = 1 / (df['AVG'] / (1 + df['POS'].apply(lambda pos: teams_need_position(pos,teams_to_check))))

    #Score = ADP_weight * (1/ADP) + VORP_weight * VORP + Position_weight * Position_Score + Team_Needs_weight * Team_Needs_Score

    #How can I account for position strats in draft, Teams that pick on the turn can manufacture runs on positions would that be a good strat(?)

    #Difference in ADP between top position player and the worst case scenario player they'd have to draft instead
    RB_VONA = df.loc[df['POS'] == 'RB', 'ADP'].iloc[0] - df.loc[df['POS'] == 'RB', 'ADP'].iloc[len(set(teams_to_check))] 
    WR_VONA = df.loc[df['POS'] == 'WR', 'ADP'].iloc[0] - df.loc[df['POS'] == 'WR', 'ADP'].iloc[len(set(teams_to_check))] 
    QB_VONA = df.loc[df['POS'] == 'QB', 'ADP'].iloc[0] - df.loc[df['POS'] == 'QB', 'ADP'].iloc[len(set(teams_to_check))]

    conditions = [
    df['POS'] == 'RB',
    df['POS'] == 'WR',
    df['POS'] == 'QB'
    ]
    values = [RB_VONA, WR_VONA, QB_VONA]

    df['VONA'] = np.select(conditions, values)

    df['PN'] = df['POS'].apply(lambda pos: teams_need_position(pos,teams_to_check))

    df['Score'] = st.session_state.ADP_weight*((1/df['ADP'])*10) + st.session_state.VONA_weight*(df['VONA']) + st.session_state.positional_needs_weight*(df['PN'])

    return df

def get_teams_between_picks(pick_order):
    value = pick_order[st.session_state.pick_num]
    arr_slice = []
    for i in range(st.session_state.pick_num, len(pick_order)):
        if pick_order[i] == value:
            return arr_slice
        arr_slice.append(pick_order[i])
    
    return []

def is_starting_position(position, team):
    if position == 'QB' and team['QB'] is None:
        return True
    elif position == 'RB' and (team['RB1'] is None or team['RB2'] is None or team['FLEX'] is None):
        return True
    elif position == 'WR' and (team['WR1'] is None or team['WR2'] is None or team['FLEX'] is None):
        return True
    elif position == 'TE' and team['TE'] is None:
        return True
    else:
        return False

def handle_ADP_weight_slider(): 
    if st.session_state.ADP_weight != st.session_state.ADP_slider:
        st.session_state.ADP_weight = st.session_state.ADP_slider

def handle_VONA_weight_slider(): 
    if st.session_state.VONA_weight != st.session_state.VONA_slider:
        st.session_state.VONA_weight = st.session_state.VONA_slider

def handle_positional_needs_weight_slider():
    if st.session_state.positional_needs_weight != st.session_state.PN_slider:
        st.session_state.positional_needs_weight = st.session_state.PN_slider



def draft():
    initialize_teams(st.session_state['num_teams'])

    draft_board_column, team_info_column = st.columns([3, 1])  # adjust the numbers to adjust column width

    pick_order = create_pick_order() #Initialize snaking pick order 

    st.session_state.current_team_picking = pick_order[st.session_state.pick_num - 1] # -1 bc python is index 0
    if st.session_state.current_team_picking == 0: st.session_state.current_team_picking = 1 

    with draft_board_column:
        undrafted_player_list = st.session_state.df['Player']
        selected_player = st.selectbox(f'With pick number {st.session_state.pick_num} in the draft, Team {st.session_state.current_team_picking} selected...', undrafted_player_list, key = 'pick_sel_key')
        st.button('Make pick', on_click = handle_make_pick, key = 'pick_key')

        if st.session_state.current_team_picking == st.session_state.user_first_pick:
            st.header("You're on the board!")
            st.write("Suggested picks are")
            current_draft_board = st.session_state.df.copy(deep=True)
            scores_df = calculate_scores(current_draft_board, get_teams_between_picks(pick_order))
            top_picks = scores_df.sort_values(by='Score', ascending=False).head(5)

            for _,row in top_picks.iterrows():
                st.write(f"{row['Player']} ({row['POS']}) - Score: {row['Score']} {'*' if is_starting_position(row['POS'], st.session_state[st.session_state.current_team_picking]) else ''}")

        st.header("Draft Board")
        st.dataframe(st.session_state.df, use_container_width = True)

    with team_info_column:
        with st.expander("Your Roster", expanded = False):
            for key, value in st.session_state[str(st.session_state['user_first_pick'])].items():
                if value is None:
                    st.write(key)
                else:
                    st.write(value)

        with st.expander("View another team's roster", expanded = False):
            team_to_display = st.selectbox('Select team to view', [f'Team {i}' for i in range(1, st.session_state['num_teams'] + 1) if i != st.session_state['user_first_pick']], label_visibility='hidden')

            teamID = int(re.sub(r'\D', '', team_to_display))

            for key, value in st.session_state[f'{teamID}'].items():
                if value is None:
                    st.write(key)
                else:
                    st.write(value)

def main():
    APP_TITLE = 'Fantasy Football Snake Draft Optimizer'
    st.set_page_config(APP_TITLE, layout = 'wide')
    hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
    #Initialize and cleans dataframe
    if 'df' not in st.session_state:
        df = pd.read_csv('FantasyPros_2022_Overall_ADP_Rankings.csv')
        df = df.rename(columns={'AVG': 'ADP'})
        df['POS'] = df['POS'].str.replace('\d+', '', regex=True)
        df = df[df['POS'].isin(['QB', 'RB', 'WR', 'TE'])]
        df = df[['Player','Team','Bye','POS','ADP']]
        st.session_state.df = df.dropna(how='all')
    
    #Draft Control Variables
    if 'num_teams' not in st.session_state: st.session_state['num_teams'] = 0
    if 'user_first_pick' not in st.session_state: st.session_state['user_first_pick'] = -1
    if 'current_team_picking' not in st.session_state: st.session_state['current_team_picking'] = 1 
    if 'draft_started' not in st.session_state: st.session_state['draft_started'] = False
    if 'pick_num' not in st.session_state: st.session_state['pick_num'] = 1

    #Model Parameter Coefficients
    with st.expander("Tune Model Parameters", expanded = False):
            st.slider('ADP', on_change = handle_ADP_weight_slider, max_value=100, min_value=0, value = 50, key = 'ADP_slider')
            st.slider('Positional Scarcity', on_change = handle_VONA_weight_slider, max_value=100, min_value=0, value = 50, key = 'VONA_slider')
            st.slider('Positional Need', on_change = handle_positional_needs_weight_slider, max_value=100, min_value=0, value = 50, key = 'PN_slider')
    if 'ADP_weight' not in st.session_state: st.session_state['ADP_weight'] = st.session_state.ADP_slider
    if 'positional_needs_weight' not in st.session_state: st.session_state['positional_needs_weight'] = st.session_state.PN_slider
    if 'VONA_weight' not in st.session_state: st.session_state['VONA_weight'] = st.session_state.VONA_slider


    #If the number of teams hasn't been specified yet (still is 0), prompt user to enter value
    if st.session_state['num_teams'] == 0:
        padcol1, center_col,padcol2 = st.columns([2, 1, 2])  #Padding number input widget makes it look better 
        center_col.number_input("How many teams are in your draft?", on_change = handle_num_teams, key = 'num_teams_key', step = 1, value = 0)
    
    #If the slot the user is picking from hasn't been specified yet (still is 0), prompt user to enter value
    if st.session_state['user_first_pick'] == 0:
        padcol1, center_col,padcol2 = st.columns([2, 1, 2])  
        center_col.number_input("What slot are you drafting from?", on_change = handle_user_first_pick, key = 'ufp_key', step = 1, value = 0)

    #If both the previous values are set, start draft
    if st.session_state['num_teams'] != 0 and st.session_state['user_first_pick'] != 0: st.session_state['draft_started'] = True

    if st.session_state['draft_started']: draft()


if __name__ == "__main__":
    main()
