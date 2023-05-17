import streamlit as st 
import pandas as pd
import re
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
    if st.session_state.pick_key:
        st.session_state.pick_num = st.session_state.pick_num + 1
        st.session_state[st.session_state.current_team_picking] = assign_player(st.session_state[st.session_state.current_team_picking], st.session_state.pick_sel_key, st.session_state.df)
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

def draft():
    initialize_teams(st.session_state['num_teams'])

    draft_board_column, team_info_column = st.columns([3, 1])  # adjust the numbers to adjust column width

    pick_order = create_pick_order()

    st.session_state.current_team_picking = pick_order[st.session_state.pick_num - 1]

    if st.session_state.current_team_picking == 0: st.session_state.current_team_picking = 1

    with draft_board_column:
        undrafted_player_list = st.session_state.df['Player']
        selected_player = st.selectbox(f'With pick number {st.session_state.pick_num} in the draft, Team {st.session_state.current_team_picking} selected...', undrafted_player_list, key = 'pick_sel_key')
        st.button('Make pick', on_click = handle_make_pick, key = 'pick_key')
        st.header("Draft Board")
        st.dataframe(st.session_state.df, use_container_width = True)

    with team_info_column:
        with st.expander("Roster", expanded = True):
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

    if 'num_teams' not in st.session_state: st.session_state['num_teams'] = 0
    if 'user_first_pick' not in st.session_state: st.session_state['user_first_pick'] = -1
    if 'current_team_picking' not in st.session_state: st.session_state['current_team_picking'] = 1 
    if 'draft_started' not in st.session_state: st.session_state['draft_started'] = False
    if 'df' not in st.session_state:
        df = pd.read_csv('FantasyPros_2022_Overall_ADP_Rankings.csv')
        df['POS'] = df['POS'].str.replace('\d+', '', regex=True)
        df = df[df['POS'].isin(['QB', 'RB', 'WR', 'TE'])]
        df = df[['Player','Team','Bye','POS','AVG']]
        st.session_state.df = df.dropna(how='all')
    
    if 'pick_num' not in st.session_state: st.session_state['pick_num'] = 1

    if st.session_state['num_teams'] == 0:
        st.number_input("How many teams are in your draft?", on_change = handle_num_teams, key = 'num_teams_key', step = 1, value = 0)

    if st.session_state['user_first_pick'] == 0:
        st.number_input("What slot are you drafting from?", on_change = handle_user_first_pick, key = 'ufp_key', step = 1, value = 0)

    if st.session_state['num_teams'] != 0 and st.session_state['user_first_pick'] != 0:
        st.session_state['draft_started'] = True
    
    if st.session_state['draft_started']:
        draft()


if __name__ == "__main__":
    main()
