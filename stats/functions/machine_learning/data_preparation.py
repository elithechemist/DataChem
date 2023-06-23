"""
data_preparation.py: Contains functions for preprocessing datasets including feature-based pre-selection,
splitting data into training and test sets, and transforming response variables.

__author__ = "Eli Jones"
"""

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import stats.functions.machine_learning.kennardstone_algorithm as ks


def transform_response_variable(y, transform_type=None):
    """
    Apply specified transformation to the response variable y.
    
    Parameters:
        y: Response variable as a numpy array.
        transform_type (str): Optional. Specifies the type of transformation to apply.
            Supported transformation types are:
                - 'exp': Applies the exponential transformation by computing np.exp(y).
                - 'log': Applies the logarithmic transformation by computing np.log(y + 0.0001).
                - 'abs': Applies the absolute value transformation by computing np.abs(y).
            If transform_type is not provided or not one of the supported types, the function
            returns y unchanged.
    
    Returns:
        The transformed variable or array-like object.
    """
    if transform_type == 'exp':
        return np.exp(y)
    elif transform_type == 'log':
        return np.log(y + 0.0001)
    elif transform_type == 'abs':
        return np.abs(y)
    else:
        return y
    

def feature_based_preselection(X, y, X_labels, select_features, thresholds):
    """
    Pre-select samples from dataset based on the values of particular features.
    
    Parameters:
        X (array-like): The dataset with shape (n_samples, n_features).
        y (array-like): The response variable with shape (n_samples,).
        X_labels (list): A list of strings representing the names of the features (columns) in X.
        select_features (list of str): A list of names of the features to use for pre-selection.
        thresholds (list of float): A list of threshold values for pre-selection. Samples with values of 
            select_features less than the corresponding thresholds will be selected.
    
    Returns:
        tuple: A tuple containing:
            - array-like: The dataset with pre-selected samples.
            - array-like: The response variable with pre-selected samples.
            - array-like: A boolean mask indicating which samples were selected.
    
    Example:
        X = [[1, 2], [3, 4], [5, 6]]
        y = [7, 8, 9]
        X_labels = ["feature1", "feature2"]
        selected_X, selected_y, mask = feature_based_preselection(X, y, X_labels, ["feature2"], [5])
        # selected_X will be [[1, 2], [3, 4]]
        # selected_y will be [7, 8]
        # mask will be [True, True, False]
    """
    if len(select_features) != len(thresholds):
        raise ValueError("Length of select_features must be equal to length of thresholds")
    
    # Create an initial boolean mask where all values are True
    mask = [True] * len(X)
    
    # Update the mask based on each select_feature and threshold
    for select_feature, threshold in zip(select_features, thresholds):
        # Get the index of the feature based on the feature name
        feature_index = X_labels.index(select_feature)
        # Update the boolean mask where True indicates that the sample meets the criteria
        mask = mask & (X[:, feature_index] < threshold)
    
    # Return the pre-selected samples and the mask
    return X[mask], y[mask], mask


def remove_data_by_index(X, y, exclude_indices):
    """
    Remove samples from the dataset (both features and response variable) based on their indices.
    
    Parameters:
        X (array-like): The dataset with shape (n_samples, n_features).
        y (array-like): The response variable with shape (n_samples,).
        exclude_indices (list): A list of indices that should be excluded from the dataset.
    
    Returns:
        tuple: A tuple containing:
            - array-like: The dataset with excluded samples removed.
            - array-like: The response variable with excluded samples removed.
    
    Example:
        X = [[1, 2], [3, 4], [5, 6], [7, 8]]
        y = [10, 20, 30, 40]
        new_X, new_y = remove_data_by_index(X, y, [1, 3])
        # new_X will be [[1, 2], [5, 6]]
        # new_y will be [10, 30]
    """
    # Create a list of indices representing the samples that are not in the exclusion list
    include_indices = [i for i in range(len(y)) if i not in exclude_indices]
    
    # Select the rows in X and y that are not in the exclusion list
    new_X = [X[i] for i in include_indices]
    new_y = [y[i] for i in include_indices]
    
    # Return the modified X and y
    return new_X, new_y


def split_data(X, y, split_method, test_ratio, test_indices=None, random_state=42):
    """
    Split data into training and test sets based on the specified method.
    
    Parameters:
        X: Features as a numpy array or pandas DataFrame.
        y: Response variable as a numpy array or pandas Series.
        split_method (str): Method used for splitting the data.
            Supported methods are:
                - 'random': Randomly splits the data into training and test sets.
                - 'define': Splits the data by manually specifying indices to include in the test set.
                - 'ks': Splits the data using the Kennard-Stone algorithm.
                - 'y_equidist': Splits the data such that y values are as equidistant as possible.
        test_ratio (float): Proportion of the data to include in the test set.
        test_indices (list): Optional. List of indices to exclude in the 'define' split method.
    
    Returns:
        X_train, X_test, y_train, y_test: Training and test sets of features X and response variable y.
    """
    if split_method == 'random':
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_ratio, random_state=random_state)
        TS = [np.argwhere(np.all(X==i, axis=1))[0, 0] for i in X_train]
        VS = [np.argwhere(np.all(X==i, axis=1))[0, 0] for i in X_test]
    elif split_method == 'define':
        TS = [i for i in range(X.shape[0]) if i not in test_indices]
        VS = test_indices
        X_train, y_train, X_test, y_test = X[TS], y[TS], X[VS], y[VS]
    elif split_method == 'ks':
        TS, VS = ks.kennardstonealgorithm(X, int((1 - test_ratio) * X.shape[0]))
        X_train, y_train, X_test, y_test = X[TS], y[TS], X[VS], y[VS]
        TS = [np.argwhere(np.all(X==i, axis=1))[0, 0] for i in X_train]
        VS = [np.argwhere(np.all(X==i, axis=1))[0, 0] for i in X_test]
    elif split_method == 'y_equidist':
        no_extrapolation = True
        if no_extrapolation:
            minmax = [np.argmin(y), np.argmax(y)]
            y_ks = np.array([i for i in y if i not in [np.min(y), np.max(y)]])
            y_ks_indices = [i for i in range(len(y)) if i not in minmax]
            # indices relative to y_ks:
            VS_ks, TS_ks = ks.kennardstonealgorithm(y_ks.reshape(len(y_ks), 1), int(test_ratio * (2 + len(y_ks))))
            # indices relative to y:
            TS = sorted([y_ks_indices[i] for i in TS_ks] + minmax)
            VS = sorted([y_ks_indices[i] for i in VS_ks])
        else:
            VS, TS = ks.kennardstonealgorithm(y.reshape(len(y), 1), int(test_ratio * len(y)))
        X_train, y_train, X_test, y_test = X[TS], y[TS], X[VS], y[VS]
    else:
        raise ValueError("split option not recognized")

    return X_train, X_test, y_train, y_test


def normalize_predictors(X_train, X_test):
    """
    Normalize features by mean/variance using StandardScaler.
    
    This function uses StandardScaler from sklearn.preprocessing to normalize the features in the training and test datasets.
    Normalizing the features is important to ensure that all features are on the same scale, which can improve the performance
    of many machine learning algorithms.
    
    Parameters:
        X_train (array-like): The training dataset with shape (n_samples, n_features).
        X_test (array-like): The test dataset with shape (n_samples, n_features).
    
    Returns:
        tuple: A tuple containing:
            - array-like: The normalized training dataset.
            - array-like: The normalized test dataset.
    
    Example:
        X_train = [[1, 2], [3, 4], [5, 6]]
        X_test = [[7, 8], [9, 10]]
        X_train_normalized, X_test_normalized = normalize_predictors(X_train, X_test)
    """
    from sklearn.preprocessing import StandardScaler

    # Initialize the StandardScaler
    scaler = StandardScaler()

    # Fit the scaler on the training data and transform the training data
    X_train_normalized = scaler.fit_transform(X_train)
    
    # Transform the test data using the same scaler
    X_test_normalized = scaler.transform(X_test)

    # Return the normalized training and test data
    return X_train_normalized, X_test_normalized


def data_preparation(X, y, X_labels, select_features=None, thresholds=None, transform_type=None,
         split_method='random', test_ratio=0.20, test_indices=None, exclude_indices=None, random_state=42):
    """
    Pre-process and split the data into training and test sets.
    
    Parameters:
        X (array-like): The dataset with shape (n_samples, n_features).
        y (array-like): The response variable with shape (n_samples,).
        X_labels (list): A list of strings representing the names of the features (columns) in X.
        select_features (list of str): Optional. A list of names of the features to use for pre-selection.
        thresholds (list of float): Optional. A list of threshold values for pre-selection corresponding to select_features.
        transform_type (str): Optional. Specifies the type of transformation to apply to y.
        split_method (str): Method used for splitting the data ('random', 'define', 'ks', 'y_equidist').
        test_ratio (float): Proportion of the data to include in the test set.
        exclude_indices (list): Optional. List of indices to exclude in the 'define' split method.
        random_state (int): Random state for reproducibility.
    
    Returns:
        tuple: A tuple containing the training and test sets of features X and response variable y.
    
    Example:
        X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
        y = np.array([10, 20, 30, 40])
        X_labels = ["feature1", "feature2"]
        X_train, X_test, y_train, y_test = main(X, y, X_labels, select_features=["feature2"],
                                                thresholds=[5], transform_type='log', split_method='random',
                                                test_ratio=0.2)
    """
    
    # If exclude_indices is provided, remove the data points from X and y
    if exclude_indices is not None:
        X, y = remove_data_by_index(X, y, exclude_indices)
    # If select_features and thresholds are provided, perform feature-based pre-selection
    if select_features and thresholds:
        if len(select_features) != len(thresholds):
            raise ValueError("Length of select_features must be equal to length of thresholds")
        # Create a mask for preselection
        mask = np.ones(len(X), dtype=bool)
        # Update the mask based on each feature and threshold
        for select_feature, threshold in zip(select_features, thresholds):
            feature_index = X_labels.index(select_feature)
            mask &= (X[:, feature_index] < threshold)
        # Apply the mask
        X = X[mask]
        y = y[mask]
    # Transform the response variable if specified
    y = transform_response_variable(y, transform_type)
    # Split the data into training and test sets based on the specified method
    X_train, X_test, y_train, y_test = split_data(
        X, y, split_method, test_ratio, test_indices, random_state)
    # Normalize the predictors to have zero mean and unit standard deviation
    X_train, X_test = normalize_predictors(X_train, X_test)
    
    # Return the training and test sets
    return X_train, X_test, y_train, y_test