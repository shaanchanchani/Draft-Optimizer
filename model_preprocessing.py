import os 
import pandas as pd
import numpy as np

#Representation 1: Accounts for players left on the board

#Returns 4 element lists for each position. First element is the number of players at that position
#that haven't been drafted. Next 3 elements are smallest ADP values of undrafted players at that position
def get_remaining_players_repr(df, current_pick_num):
    default_adp = df['ADP'].max() + 10
    remaining_players = df[df['pick_num'] > current_pick_num]
    remaining_players = remaining_players.sort_values('ADP')

    positions = ['QB', 'RB', 'WR', 'TE', 'DST', 'K']

    remaining_repr = {}
    for pos in positions:
        pos_players = remaining_players[remaining_players['player_pos'] == pos]
        pos_count = len(pos_players)
        pos_adp_values = pos_players['ADP'].nsmallest(3).tolist()

        # If less than 3 players, pad w/ default_adp (max + 10)
        while len(pos_adp_values) < 3:
            pos_adp_values.append(default_adp)

        remaining_repr[pos] = [pos_count] + pos_adp_values
    ret_df = pd.DataFrame(remaining_repr).T
    return ret_df.values

#Representation 2: Accounts for current roster of the team picking 

#Returns list of team's roster indicating position slots that can be filled 
# 0 = Slot filled 
def get_team_roster_repr(df, team_name, current_pick_num):
    df = df[df['pick_num'] < current_pick_num]
    team_df = df[df['team_name'] == team_name]

    positions = {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'DST' : 0, 'K' : 0, 'Bench' : 0}
    starting_lineup = []
    bench = []
    team_df = team_df.sort_values('ADP')

    for index,row in team_df.iterrows():
            pos = row['player_pos']

            if ((pos in ['RB', 'WR'] and positions[pos] < 2) or
                (pos in ['QB', 'TE', 'DST', 'K'] and positions[pos] < 1)):
                positions[pos] += 1
            elif (pos == 'RB' and positions[pos] >= 2 and positions['FLEX'] < 1):
                positions['FLEX'] += 1

            elif (pos == 'WR' and positions[pos] >= 2 and positions['FLEX'] < 1):
                positions['FLEX'] += 1
            else:
                positions['Bench'] += 1

    curr_roster = [x for x in positions.values()]
    return np.array(curr_roster)

#Forms a single state representation based on the two representations 
def get_state_representation(df, current_pick_num, team_name, max_players=180):
    team_roster_repr = get_team_roster_repr(df, team_name, current_pick_num)
    remaining_players_repr = get_remaining_players_repr(df, current_pick_num)
    state_repr = np.concatenate([team_roster_repr, remaining_players_repr], axis=None)
    return state_repr

def get_best_teams(df):
    df = df[df['player_pos'] != 'K']
    df = df[df['player_pos'] != 'DST']

    draft_scores = {}

    for team in df['team_name'].unique().tolist():
        starting_lineup = []
        bench = []
        team_df = df[df['team_name'] == f'{team}']
        team_df = team_df.sort_values('ADP')
        for index,row in team_df.iterrows():
            pos = row['player_pos']
            positions = {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'Bench': 0}

            if ((pos in ['RB', 'WR'] and positions[pos] < 2) or
                (pos in ['QB', 'TE'] and positions[pos] < 1)):
                positions[pos] += 1
                starting_lineup.append(row['ADP'])

            elif (pos == 'RB' and positions[pos] >= 2 and positions['FLEX'] < 1):
                positions['FLEX'] += 1
                starting_lineup.append(row['ADP'])

            elif (pos == 'WR' and positions[pos] >= 2 and positions['FLEX'] < 1):
                positions['FLEX'] += 1
                starting_lineup.append(row['ADP'])

            else:
                positions['Bench'] += 1
                bench.append(row['ADP'])
        
        team_draft_score = sum([i*1.5 for i in starting_lineup]) + sum(bench)
        draft_scores[team] =  team_draft_score

    draft_score_df = pd.DataFrame.from_dict(draft_scores, orient='index').reset_index()
    draft_score_df.columns = ['team_name', 'score']
    draft_score_df = draft_score_df.sort_values(by='score', ascending=True)

    return list(draft_score_df[:4]['team_name'])

def preprocess_data(data_folders):
    inputs = []
    outputs = []
    
    inputs_best = []
    outputs_best = []

    best_team_distribution = []

    expected_draft_order = (list(range(1, 13)) + list(range(12, 0, -1)))*15
    expected_draft_order = expected_draft_order[:int(len(expected_draft_order)/2)]

    for folder_path in data_folders:
        for filename in os.listdir(folder_path):
            if not os.path.isdir(os.path.join(folder_path, filename)):
                file_path = os.path.join(folder_path, filename)
                df = pd.read_csv(file_path)

                best_teams = get_best_teams(df)
                
                for pick_num in range(1, df['pick_num'].max()):
                    # generate the state representation for the current pick
                    teamID = expected_draft_order[pick_num - 1]
                    state_repr = get_state_representation(df, pick_num, f'Team{teamID}')  # replace team_name with actual team name
                    # get the position of the player picked next
                    next_pick_pos = df.loc[df['pick_num'] == pick_num+1, 'player_pos'].values[0]
                    # store the input-output pair
                    inputs.append(state_repr)
                    outputs.append(next_pick_pos)

                    if f'Team{teamID}' in best_teams:
                        inputs_best.append(state_repr)
                        outputs_best.append(next_pick_pos)
                        best_team_distribution.append(f'Team{teamID}')

    inputs = np.array(inputs)
    outputs = np.array(outputs)
    inputs_best = np.array(inputs_best)
    outputs_best = np.array(outputs_best)

    return inputs,outputs,inputs_best,outputs_best,best_team_distribution

def simulate_pick(df,current_pick_num,team_name):
    next_pick_pos = df.loc[df['pick_num'] == current_pick_num+1, 'player_pos'].values[0]

    input_vector = get_state_representation(df, current_pick_num, team_name, max_players)

    input_vector = input_vector.reshape(1, 1, -1)

    y_pred = model.predict(input_vector)

    top_two_indices = np.argsort(y_pred[0])[-2:]

    top_two_predictions = encoder.inverse_transform(top_two_indices)

    top_two_probabilities = y_pred[0][top_two_indices]

    for pred, prob in zip(top_two_predictions, top_two_probabilities):
        print(f'Predicted label: {pred}, Probability: {prob}')

def get_top_two_accuracy(model, X_test,y_test_encoded):
    y_pred = model.predict(X_test)

    top_two_pred = np.argsort(y_pred, axis=-1)[:, -2:]

    y_test_class_indices = np.argmax(y_test_encoded, axis=-1)

    correct = [y in pred for y, pred in zip(y_test_class_indices, top_two_pred)]
    accuracy = np.mean(correct)

    print(f'Top-2 accuracy: {accuracy * 100:.2f}%')

    

def main():
    data_folders = ['./dataset1_12_PPR_15','./dataset2_12_PPR_15']

    inputs,outputs,inputs_best,outputs_best,best_team_distribution = preprocess_data(data_folders)

    np.save('inputs_batch1', inputs)
    np.save('outputs_batch1', outputs)

    np.save('inputs_best_batch1', inputs_best)
    np.save('outputs_best_batch1', outputs_best)

    np.save('batch1_best_team_distribution', best_team_distribution)


    


if __name__ == "__main__":
    main()