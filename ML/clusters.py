import numpy as np
import pandas as pd
dataset = pd.read_csv('ML/Training.csv')
X = dataset.iloc[:, :-1].values
y = dataset.iloc[:, -1].values

from sklearn.preprocessing import LabelEncoder
label_encoder = LabelEncoder()
y = label_encoder.fit_transform(y)

for i in range(1, 42):
    temp = y[i-1]
    j = i
    while (j<len(y) and y[j]==temp):
        j+=1
        X[i-1] = np.logical_or(X[i-1, :], X[j-1, :])
    X = np.delete(X, range(i, j), 0)
    y = np.delete(y, range(i, j), 0)

loc_non_zero = np.nonzero(X)

def other_possible_symptoms(input_sym):
    lst = []
    for symptom in input_sym:
        similar_symptoms = []
        similar_disease = []
        index = dataset.columns.get_loc(symptom)
        for i in range(len(loc_non_zero[1])):
            if loc_non_zero[1][i]==index:
                similar_disease.append(loc_non_zero[0][i])
        
        for i in range(len(similar_disease)):
            for j in range(len(loc_non_zero[0])):
                if similar_disease[i] == loc_non_zero[0][j]:
                    if dataset.columns[loc_non_zero[1][j]] not in similar_symptoms:
                        similar_symptoms.append(dataset.columns[loc_non_zero[1][j]])
                elif loc_non_zero[0][j] > similar_disease[i]:
                    break
        similar_symptoms.remove(symptom)
        if not lst:        
            lst = set(similar_symptoms)
        else:
            lst = lst & set(similar_symptoms)
    return(list(lst))

