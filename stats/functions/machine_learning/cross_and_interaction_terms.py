"""
cross_and_interaction_terms.py: Contains a function for creating cross and interaction terms.

__author__ = "Eli Jones"
"""

from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from scipy import stats
import re
import numpy as np


def cross_and_interaction_terms(X_train, X_test, y_train, X_labelname_dict, p_val_cutoff=0.005):
    """
    Generate polynomial and interaction features and select them based on p-values.
    
    Parameters:
        X_train (array-like): The training dataset with shape (n_samples, n_features).
        X_test (array-like): The test dataset with shape (n_samples, n_features).
        y_train (array-like): The response variable for the training dataset with shape (n_samples,).
        X_labelname_dict (dict): A dictionary mapping feature indices to feature names.
        p_val_cutoff (float): The p-value cutoff for feature selection.
    
    Returns:
        tuple: A tuple containing:
            - array-like: The normalized and selected features in the training dataset.
            - array-like: The normalized and selected features in the test dataset.
            - list: The names of the selected features.
            - list: The label names of the selected features.
    """
    
    def add_to_x(matchobj):
        if "^" in matchobj.group(0):
            n = int(matchobj.group(0).split("^")[0]) + 1
            return "{} x{}".format(n, n)
        else:
            return str(int(matchobj.group(0)) + 1)
    
    def sub_label_to_name(matchobj):
        index = int(matchobj.group(0)[1:]) - 1
        return str(X_labelname_dict[index])
    
    def sub_labelname(matchobj):
        # Convert x1, x2, etc. to 0, 1, etc.
        index = int(matchobj.group(0)[1:]) - 1
        # Return the corresponding label
        return matchobj.group(0) + " " + str(X_labelname_dict[index])  # Convert to string explicitly
    
    polyfeats = PolynomialFeatures(degree=2, interaction_only=False, include_bias=False)
    
    X_train_p = polyfeats.fit_transform(X_train)
    X_test_p = polyfeats.transform(X_test)
    
    r2s = []
    pvals = []
    for feature in X_train_p.T:
        if np.var(feature) != 0:
            _, _, r_value, p_value, _ = stats.linregress(feature, y_train)
            r2s.append(r_value ** 2)
            pvals.append(p_value)
        else:
            r2s.append(0)
            pvals.append(1)
    
    keep_p_ = [i[0] for i in np.argwhere(np.asarray(pvals) < p_val_cutoff) if i not in range(X_train.shape[1])]
    keep_p = list(range(X_train.shape[1])) + keep_p_
    
    pfnames = np.asarray([re.sub("[0-9]+(\^[0-9])*", add_to_x, st) for st in polyfeats.get_feature_names_out()])
    X_p_labels = list(np.reshape(pfnames[keep_p], len(keep_p)))
    X_p_names = [re.sub("x[0-9]+", sub_label_to_name, st) for st in X_p_labels]
    X_p_labelname = [re.sub("x[0-9]+", sub_labelname, st) for st in X_p_labels]
    
    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train_p[:, keep_p])
    X_test_sc = scaler.transform(X_test_p[:, keep_p])
    
    return X_train_sc, X_test_sc, X_p_names, X_p_labelname