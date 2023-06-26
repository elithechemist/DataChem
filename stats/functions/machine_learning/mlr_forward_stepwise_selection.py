from sklearn.linear_model import LinearRegression
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from stats.functions.machine_learning.forward_step_candidates import ForwardStep_py as fsc
import stats.functions.machine_learning.loo_q2 as loo
from stats.functions.machine_learning.r2_val import r2_val

def forward_step_candidates(X_train, y_train, n_steps, n_candidates, collin_criteria):
    # Combining the features and response in a DataFrame
    df = pd.DataFrame(np.hstack((X_train, y_train[:, None])))
    newcols = ["x" + str(i + 1) for i in range(X_train.shape[1])]
    df.columns = newcols + ["y"]

    # Calling the ForwardStep_py function
    results, models, scores, sortedmodels, candidates = fsc(df,'y',
                    n_steps=n_steps, n_candidates=n_candidates, collin_criteria=collin_criteria)
    
    # List to store fitted models and selected features
    fitted_models = []
    selected_features_list = []
    
    # Loop through each step
    for index, row in results.iterrows():
        model_sel = row["Model"]
        selected_feats = sorted([newcols.index(i) for i in models[model_sel].terms])
        X_train_sel = X_train[:, selected_feats]
        
        # Fitting the linear regression model using the selected features
        lr = LinearRegression().fit(X_train_sel, y_train)
        
        # Append the model and features to the lists
        fitted_models.append(lr)
        selected_features_list.append(selected_feats)
    
    # Return the lists of fitted models and selected features
    return fitted_models, selected_features_list


def find_best_models(fitted_models, selected_features_list, X_train, X_test, y_train, y_test, n_best_models=3):
    model_data = []
    
    # Iterate through each model and selected features
    for i, (model, selected_feats) in enumerate(zip(fitted_models, selected_features_list)):
        X_train_sel = X_train[:, selected_feats]
        X_test_sel = X_test[:, selected_feats]
        
        # Fitting the model with selected features
        lr = LinearRegression().fit(X_train_sel, y_train)
        
        # Making predictions
        y_train_pred = lr.predict(X_train_sel)
        y_test_pred = lr.predict(X_test_sel)
        
        # Calculating metrics
        testr2 = np.round(r2_val(y_test, y_test_pred, y_train), 4)
        trainr2 = lr.score(X_train_sel, y_train)
        q2, _ = loo.q2(X_train_sel, y_train) # Assuming Q2 calculation is done by some custom method
        
        # Custom 'Model Quality' metric
        model_quality = trainr2 * q2 * testr2
        if testr2 <= 0:
            model_quality = 0
        if abs(testr2 - q2) > 0.15:
            model_quality -= 0.1
        if testr2 > trainr2:
            model_quality -= 0.1
        
        # Storing the model, selected features, predictions and metrics
        model_data.append((lr, selected_feats, (y_train_pred, y_test_pred), (trainr2, q2, testr2, model_quality)))
    
    # Sorting based on 'Model Quality'
    model_data.sort(key=lambda x: x[3][3], reverse=True)
    
    # Extracting the top n_best_models
    best_models = [data[0] for data in model_data[:n_best_models]]
    selected_features_list = [data[1] for data in model_data[:n_best_models]]
    predictions = [data[2] for data in model_data[:n_best_models]]
    model_metrics = [data[3] for data in model_data[:n_best_models]]
    
    return best_models, selected_features_list, predictions, model_metrics

