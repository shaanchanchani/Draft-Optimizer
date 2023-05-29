## Metrics Achieved w/ LSTM:

### **Average Drafter Model**
Trained using every pick from 62 mock drafts (10561 input output pairs). Prediction target is position of next picked player.

Test Accuracy: 49.35%

Test Accuracy using top 2 predictions: 83.97%

### **Smart Drafter Model**
Trained using every pick made by the teams with the top 4 draft scores at the end of their respective drafts. (Same 62 mock draft dataset, 3525 input output pairs)

Test Accuracy: 50.76%

Test Accuracy using top 2 predictions: 82.60%

## Metrics Achieved w/ Random Forest:

10 fold cross validation procedure

### **Average Drafter Model**
CV Accuracy: 65.3% 
Test Accuracy: 65.2%
Top-2 accuracy: 87.85%

### **Smart Drafter Model**
CV Accuracy: 66.6% 
Test Accuracy: 64.2%
Top-2 accuracy: 87.05%