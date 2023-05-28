import os 
import pandas as pd
import numpy as np
from keras.models import Sequential
from keras.layers import Dense, LSTM, Embedding
from keras.utils import to_categorical
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split


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
    team_picks = df[df['team_name'] == team_name]
    position_counts = pd.get_dummies(team_picks['player_pos']).sum()

    positions = ['QB', 'RB', 'WR', 'TE', 'DST', 'K']
    max_players = {'QB': 1, 'RB': 2, 'WR': 2, 'TE': 1, 'DST': 1, 'K': 1}
    flex = 1  # flex position
    bench = 6

    roster_repr = []
    for pos in positions:
        if pos in position_counts:
            roster_repr.append(max_players[pos] - position_counts[pos])
        else:
            roster_repr.append(max_players[pos])

    # Handle flex position
    if 'RB' in position_counts:
        rb_extra = max(0, position_counts['RB'] - max_players['RB'])
        if rb_extra > 0:
            flex -= 1
            bench -= rb_extra - 1
    if 'WR' in position_counts and flex > 0:
        wr_extra = max(0, position_counts['WR'] - max_players['WR'])
        if wr_extra > 0:
            flex -= 1
            bench -= wr_extra - 1

    roster_repr.append(flex)
    bench -= sum(max(0, position_counts.get(pos, 0) - max_players[pos]) for pos in positions)
    roster_repr.append(bench)
    return np.array(roster_repr)

#Forms a single state representation based on the two representations 
def get_state_representation(df, current_pick_num, team_name, max_players=180):
    team_roster_repr = get_team_roster_repr(df, team_name, current_pick_num)
    remaining_players_repr = get_remaining_players_repr(df, current_pick_num)
    state_repr = np.concatenate([team_roster_repr, remaining_players_repr], axis=None)
    return state_repr

def preprocess_data(data_folders):
    inputs = []
    outputs = []
    inputs_f = []
    outputs_f = []

    expected_draft_order = (list(range(1, 13)) + list(range(12, 0, -1)))*15
    expected_draft_order = expected_draft_order[:int(len(expected_draft_order)/2)]

    for folder_path in data_folders:
        for filename in os.listdir(folder_path):
            if not os.path.isdir(os.path.join(folder_path, filename)):
                file_path = os.path.join(folder_path, filename)
                df = pd.read_csv(file_path)
                
                for pick_num in range(1, df['pick_num'].max()):
                    # generate the state representation for the current pick
                    teamID = expected_draft_order[pick_num - 1]
                    state_repr = get_state_representation(df, pick_num, f'Team{teamID}')  # replace team_name with actual team name
                    # get the position of the player picked next
                    next_pick_pos = df.loc[df['pick_num'] == pick_num+1, 'player_pos'].values[0]
                    # store the input-output pair
                    inputs.append(state_repr)
                    outputs.append(next_pick_pos)
        
        for input_val, output_val in zip(inputs, outputs):
            if output_val not in ["K", "DST"]:
                inputs_f.append(input_val)
                outputs_f.append(output_val)

    inputs_f = np.array(inputs_f)
    outputs_f = np.array(outputs_f)

    return inputs_f,outputs_f

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

    

def main():
    data_folders = ['./dataset1','./dataset2']

    inputs,outpus = preprocess_data(data_folders)

    X_train, X_test, y_train, y_test = train_test_split(inputs, outpus, test_size=0.3, random_state=42)

    X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=0.2, random_state=42)

    X_train = X_train.reshape((X_train.shape[0], 1, X_train.shape[1]))
    X_val = X_val.reshape((X_val.shape[0], 1, X_val.shape[1]))
    X_test = X_test.reshape((X_test.shape[0], 1, X_test.shape[1]))

    encoder = LabelEncoder()
    y_train_encoded = encoder.fit_transform(y_train)
    y_val_encoded = encoder.transform(y_val)
    y_test_encoded = encoder.transform(y_test)
    y_train_encoded = to_categorical(y_train_encoded)
    y_val_encoded = to_categorical(y_val_encoded)
    y_test_encoded = to_categorical(y_test_encoded)

    model = Sequential()
    model.add(LSTM(50, input_shape=(X_train.shape[1], X_train.shape[2])))
    model.add(Dense(y_train_encoded.shape[1], activation='softmax'))

    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

    history = model.fit(X_train, y_train_encoded, epochs=100, validation_data=(X_val, y_val_encoded))

    loss, accuracy = model.evaluate(X_test, y_test_encoded)

    print(f'Test loss: {loss}')
    print(f'Test accuracy: {accuracy}')

    


if __name__ == "__main__":
    main()