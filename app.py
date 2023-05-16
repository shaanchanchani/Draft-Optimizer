import streamlit as st 
import pandas as pd
import re

@st.cache_data
def loadData():
    df = pd.read_csv('FantasyPros_2022_Overall_ADP_Rankings.csv')
    df['POS'] = df['POS'].str.replace('\d+', '', regex=True)
    df = df[df['POS'].isin(['QB', 'RB', 'WR', 'TE'])]
    df = df[['Player','Team','Bye','POS','AVG']]
    df = df.dropna(how='all')
    return df

def initialize_teams(num_teams):
    for i in range(num_teams):
        positions = ['QB', 'RB1', 'RB2', 'WR1', 'WR2', 'TE', 'FLEX', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7']
        if f'{i}' not in st.session_state: st.session_state[f'{i}'] = {pos: None for pos in positions}

def handle_num_teams():
    if st.session_state.num_teams_key:
        st.session_state['num_teams'] = st.session_state.num_teams_key
        st.session_state['user_first_pick'] = 0 

def handle_user_first_pick():
    if st.session_state.ufp_key:
        st.session_state['user_first_pick'] = st.session_state.ufp_key

def main():
    APP_TITLE = 'Fantasy Football Snake Draft Optimizer'
    st.set_page_config(APP_TITLE, layout = 'wide')
    df = loadData()

    if 'num_teams' not in st.session_state: st.session_state['num_teams'] = 0
    if 'user_first_pick' not in st.session_state: st.session_state['user_first_pick'] = -1

    if st.session_state['num_teams'] == 0:
        st.number_input("How many teams are in your draft?", on_change = handle_num_teams, key = 'num_teams_key', step = 1, value = 0)

    if st.session_state['user_first_pick'] == 0:
        st.number_input("What slot are you drafting from?", on_change = handle_user_first_pick, key = 'ufp_key', step = 1, value = 0)

    if st.session_state['num_teams'] != 0 and st.session_state['user_first_pick'] != 0:
        initialize_teams(st.session_state['num_teams'])

        draft_board_column, team_info_column = st.columns([3, 1])  # adjust the numbers to adjust column width

        draft_board_column.header("Draft Board")
        draft_board_column.dataframe(df, use_container_width = True)

        with team_info_column:
            with st.expander("View another team's roster", expanded = False):
                team_to_display = st.selectbox('Select team to view', [f'Team {i}' for i in range(1, st.session_state['num_teams'] + 1) if i != st.session_state['user_first_pick']])

                teamID = int(re.sub(r'\D', '', team_to_display))

                for key, value in st.session_state[f'{teamID - 1}'].items():
                    if value is None:
                        st.write(key)
                    else:
                        st.write(value)

if __name__ == "__main__":
    main()
