import io
import uuid
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, Ridge
from chemstats.utils.storage import s3_generate_presigned_url, s3_temp_store
from stats.functions.machine_learning.mlr_forward_stepwise_selection import forward_step_candidates, find_best_models
from stats.functions.machine_learning.mlr_forward_stepwise_selection import find_best_models
from stats.models import ExperimentalResponse, ResponseEntry, Statistics, User
from django.core.exceptions import ObjectDoesNotExist
from stats.functions.machine_learning.data_preparation import data_preparation
from stats.functions.machine_learning.cross_and_interaction_terms import cross_and_interaction_terms

def perform_regression_and_save_plot():
    try:
        user_experimental_responses = ExperimentalResponse.objects.filter(user__username='chemstats_admin')
        
        if not user_experimental_responses.exists():
            raise ValueError("No experimental response found for the user.")

        experimental_response = user_experimental_responses.first()

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
                # Collect labels if not collected yet
                if not X_labels:
                    X_labels = [param.parameter_type for param in parameters]
                # Check if x_values has any missing valu\
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

        # Convert to numpy arrays
        X = np.array(X)
        y = np.array(y)
        print(X)
        print(y)

        # Split the data into training/testing sets
        X_train, X_test, y_train, y_test = data_preparation(X, y, test_ratio=0.33, X_labels=X_labels, split_method='ks', random_state=42)

        # Parameters for forward_step_candidates function
        n_steps = 3
        n_candidates = 20
        collin_criteria = 0.5

        # Generate candidate models using forward_step_candidates
        fitted_models, selected_features_list = forward_step_candidates(X_train, y_train, n_steps, n_candidates, collin_criteria)

        # Find the best models
        n_best_models = 20  # Get all models
        best_models, selected_features, predictions, metrics = find_best_models(fitted_models, selected_features_list, X_train, X_test, y_train, y_test, n_best_models)
        
        # Placeholder for presigned urls
        presigned_urls = []

        # Iterate over each model to generate plots
        for idx, model in enumerate(best_models):
            # Extract the predictions for this model
            y_pred_train, y_pred_test = predictions[idx]

            # Compute R2 and Q2 scores
            trainr2, q2, testr2, model_quality = metrics[idx]
            
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
        return presigned_urls

    except ObjectDoesNotExist:
        return "User chemstats_admin not found"