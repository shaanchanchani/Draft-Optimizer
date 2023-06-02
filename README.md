### Datasets:

Average Drafter: Every pick from
every team in 266 drafts (12 Team PPR 15 Rounds)

44,422 Input Output Pairs (Excluding First Round Picks)

Smart Drafter: Every pick from teams that ended with a top 4 draft score.

14,830 Input Output Pairs (Excluding First Round Picks)

### Random Forest Classifier

All models trained with a 10-fold cross validation procedure.

#### Average Drafter Dataset:

CV Accuracy: 72.684%
Test Accuracy: 72.747%
Top-2 accuracy: 92.504%

Classwise Accuracy: (First Guess, Top 2 Guesses)
DST: 87.36%, 94.68%
K: 92.22%, 98.44%
QB: 58.53%, 77.38%
RB: 65.86%, 93.97%
TE: 60.24%, 81.24%
WR: 79.44%, 96.76%

#### Smart Drafter Dataset:

CV Accuracy: 75.455%
Test Accuracy: 75.680%
Top-2 accuracy: 92.493%

Classwise Accuracy: (First Guess, Top 2 Guesses)
DST: 87.54%, 93.93%
K: 95.39%, 98.03%
QB: 58.35%, 79.69%
RB: 72.16%, 94.70%
TE: 59.23%, 78.42%
WR: 80.69%, 95.89%