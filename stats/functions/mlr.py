import io
import uuid
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.linear_model import LinearRegression, Ridge
from chemstats.utils.storage import s3_generate_presigned_url, s3_temp_store
from stats.functions.machine_learning.mlr_forward_stepwise_selection import forward_step_candidates, find_best_models
from stats.functions.machine_learning.mlr_forward_stepwise_selection import find_best_models
from stats.models import ExperimentalResponse, ResponseEntry, Statistics, User
from django.core.exceptions import ObjectDoesNotExist
from stats.functions.machine_learning.data_preparation import data_preparation
from stats.functions.machine_learning.cross_and_interaction_terms import cross_and_interaction_terms

def perform_regression_and_save_plot(project, has_interaction_terms, test_ratio, split_method, n_models, n_iterations, collin_criteria, max_parameters):
    try:
        experimental_response = ExperimentalResponse.objects.get(user__username='chemstats_admin', project=project)

        # Collect y values and X values
        y = []
        X = []
        X_labels = []  # Collecting labels for the X features

        for response_entry in experimental_response.responseentry_set.all():
            conformational_ensemble = response_entry.conformational_ensemble
            statistics = Statistics.objects.filter(conformational_ensemble=conformational_ensemble).first()
            
            if statistics:
                parameters = statistics.parameters.all()
                x_values = [param.value for param in parameters]
                # Collect labels if not collected yet__
                if not X_labels:
                    X_labels = [str(param.parameter_type.group) + "_" + str(param.parameter_type.variant) + "_" + str(param.condensed_property_key) for param in parameters]
                # Check if x_values has any missing value
                if None not in x_values:
                    X.append(x_values)
                    y.append(response_entry.values[0])  # Assuming values is a list and we take the first value
        
        # Check if all x_values lists have the same length
        lengths = [len(x) for x in X]
        unique_lengths = set(lengths)
        if len(unique_lengths) > 1:
            print(f"Inconsistent X values lengths: {unique_lengths}")
            # Find the most common length
            most_common_length = max(set(lengths), key=lengths.count)
            # Keep only the lists with the most common length
            X = [x_values for x_values in X if len(x_values) == most_common_length]
            # Filter y accordingly
            y = [y_val for x_values, y_val in zip(X, y) if len(x_values) == most_common_length]


        print("X_Lables: " + str(X_labels))
        print("XLABEL1" + str(X_labels[1]))

        # Convert to numpy arrays
        X = np.array(X)
        y = np.array(y)
        print(X)
        print(y)

        # Split the data into training/testing sets
        X_train, X_test, y_train, y_test = data_preparation(X, y, test_ratio=test_ratio, X_labels=X_labels, split_method=split_method, random_state=42)

        # Generate candidate models using forward_step_candidates
        # Parameters for forward_step_candidates function
        n_steps = n_iterations
        n_candidates = n_models
        collin_criteria = 0.5

        print("n_steps: " + str(n_steps))
        print("n_candidates: " + str(n_candidates))
        print("collin_criteria: " + str(collin_criteria))

        fitted_models, selected_features_list = forward_step_candidates(X_train, y_train, n_steps, n_candidates, collin_criteria)

        # Find the best models
        n_best_models = 2  # Get all models
        best_models, selected_features, predictions, metrics = find_best_models(fitted_models, selected_features_list, X_train, X_test, y_train, y_test, n_best_models)
        
        # (2) Initialize lists to store the required information
        presigned_urls = []
        equation_strings = []  # <-- (2.1) For storing equation strings
        training_r2_scores = []  # <-- (2.2) For storing training R2 scores
        q2_scores = []  # <-- (2.3) For storing Q2 scores
        four_fold_r2_scores = []  # <-- (2.4) For storing 4-fold cross-validation R2 scores
        validation_r2_scores = []  # <-- (2.5) For storing validation R2 scores
        mean_absolute_errors = []  # <-- (2.6) For storing Mean Absolute Errors (MAEs)

        # Iterate over each model to generate plots
        for idx, model in enumerate(best_models):
            # Extract the predictions for this model
            y_pred_train, y_pred_test = predictions[idx]
            print("y_pred_train: " + str(y_pred_train))

            # Compute R2 and Q2 scores
            trainr2, q2, testr2, model_quality = metrics[idx]
            print("trainr2: " + str(trainr2))

            # (3) Composing the equation string and computing additional metrics
            coeffs = model.coef_
            print("coeffs: " + str(coeffs))

            # Composing the equation string
            equation_string = "y_pre = {:.2f}".format(model.intercept_)
            print("equation_string: " + str(equation_string))
            
            # Iterating through coefficients and feature indices
            for coef, feature_index in zip(coeffs, selected_features[idx]):
                # Retrieve the parameter_type object using the feature index
                print("Feature index: " + str(feature_index))
                parameter_type = X_labels[feature_index]
                print("Parameter type: " + str(parameter_type))
                
                # Add term to the equation string
                equation_string += " + {:.2f} {}".format(coef, parameter_type)
            
            # Append equation string
            equation_strings.append(equation_string)  # <-- (3.1) Append equation string
            
            # 4-fold cross-validation R2 score
            four_fold_r2 = np.mean(cross_val_score(model, X_train, y_train, cv=4))  # <-- (3.2) Compute 4-fold R2
            four_fold_r2_scores.append(four_fold_r2)  # Append 4-fold R2 score
            
            # Compute Mean Absolute Error (MAE)
            mae = mean_absolute_error(y_test, y_pred_test)  # <-- (3.3) Compute MAE
            mean_absolute_errors.append(mae)  # Append MAE
            
            # Append scores
            training_r2_scores.append(trainr2)  # <-- (3.4) Append training R2 score
            q2_scores.append(q2)  # <-- (3.5) Append Q2 score
            validation_r2_scores.append(testr2)  # <-- (3.6) Append validation R2 score
            
            # Plot
            plt.scatter(y_train, y_pred_train, color='blue', label="Training data")
            plt.scatter(y_test, y_pred_test, color='red', label="Test data")
            
            # Best fit line (using training data)
            slope, intercept = np.polyfit(y_train, y_pred_train, 1)
            plt.plot([min(y_train), max(y_train)], [min(y_train) * slope + intercept, max(y_train) * slope + intercept], color='black', label="Best fit")
            
            plt.xlabel("True values")
            plt.ylabel("Predicted values")
            plt.legend(loc='upper left') # You can specify location here, e.g., 'upper left'
            
            # Add R2 and Q2 scores to the plot
            # Use a higher value for the first parameter to move the text to the right
            plt.text(0.75, 0.95, f"Train R2: {trainr2:.2f}\nTest R2: {testr2:.2f}\nQ2: {q2:.2f}", transform=plt.gca().transAxes, fontsize=9, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            
            # Save the plot to an in-memory bytes buffer
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png')
            
            # Clear the current figure for the next plot
            plt.clf()

            # Generate a unique filename for the plot image
            file_name = f"{uuid.uuid4()}.png"
            
            # Upload the plot image to the temporary directory in S3
            s3_key = s3_temp_store(file_name, buffer.getvalue())
            
            # Generate a pre-signed URL for the uploaded plot image
            presigned_url = s3_generate_presigned_url(file_name, as_temp=True)
            
            # Append presigned url to list
            presigned_urls.append(presigned_url)
        
        # Returning the array of pre-signed URLs for the plot images
        print("FINISHED")
        return presigned_urls, equation_strings, training_r2_scores, q2_scores, four_fold_r2_scores, validation_r2_scores, mean_absolute_errors  # <-- (4) Modified return statement

    except ObjectDoesNotExist:
        return "User chemstats_admin not found"