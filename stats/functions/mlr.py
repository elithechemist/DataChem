import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import Ridge
from sklearn import metrics
from sklearn.model_selection import train_test_split

def perform_regression_and_save_plot(image_path="static/plot.png"):
    # Hardcoded random test data
    X = np.random.rand(100, 75)
    y = X.dot(np.random.rand(75)) + np.random.rand(100)
    
    # Split the data into training/testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=42)
    
    # Features to select
    features_py = [48, 72] # corresponding to x49 and x73 (0-indexed)

    # Select the desired features
    X_train_sel = X_train[:, features_py]
    X_test_sel = X_test[:, features_py]
    
    # Fit the Ridge regression model
    lr = Ridge(alpha=1E-5).fit(X_train_sel, y_train)
    
    # Make predictions using the model
    y_pred_train = lr.predict(X_train_sel)
    y_pred_test = lr.predict(X_test_sel)
    
    # Plot
    plt.scatter(y_train, y_pred_train, color='blue', label="Training data")
    plt.scatter(y_test, y_pred_test, color='red', label="Test data")
    plt.xlabel("True values")
    plt.ylabel("Predicted values")
    plt.legend()
    plt.savefig(image_path) # Saving the plot to an image file
    
    # For now, just returning the path where the image is saved
    return image_path
