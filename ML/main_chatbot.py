import numpy as np

from ML.clusters import other_possible_symptoms
# from classification_algo import calc_prob

def chat(provided):
    main_symptoms_given = []
    print('Hey there, this is Dr. Pulse, your virtual doctor')
    # symptoms_input = list(input('Kindly enter symptoms (atleast two): ').split())  # change by Vasu for backend
    symptoms_input=provided
    main_symptoms_given.extend(symptoms_input)

    possible_symptoms = other_possible_symptoms(symptoms_input)

    while possible_symptoms:
        symptoms_input_total = []
        while len(possible_symptoms)>10:
            i = 5
            print('\nSelect the symptoms that you experiencing:')
            temp=possible_symptoms[:i]
            possible_symptoms = possible_symptoms[i:]
            return (temp)

            symptoms_input = list(input().split())
            symptoms_input_total.extend(symptoms_input)


        main_symptoms_given.extend(symptoms_input_total)
        possible_symptoms = list(set(possible_symptoms) & set(other_possible_symptoms(symptoms_input_total)))
            
        if possible_symptoms:
            print('\nAre suffering from ' + possible_symptoms[0])
            if input() == 'yes':
                main_symptoms_given.append(possible_symptoms[0])
                possible_symptoms = list(set(possible_symptoms) & set(other_possible_symptoms([possible_symptoms.pop(0)])))
            else:   
                possible_symptoms.pop(0)

    # predicted_diseases, probabilities = calc_prob(main_symptoms_given)
    # print('\nDiseases you may be suffering from: ')
    # print([(d, p) for d, p in zip(predicted_diseases, probabilities)])
    print('\nSymptoms provided:')
    return (main_symptoms_given)

if __name__=='__main__':
    chat()
