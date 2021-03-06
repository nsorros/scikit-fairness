import numpy as np
import warnings


def equal_opportunity_score(sensitive_column, positive_target=1):
    r"""
    The equality opportunity score calculates the ratio between the probability of a **true positive** outcome
    given the sensitive attribute (column) being true and the same probability given the
    sensitive attribute being false.

    .. math::
        \min \left(\frac{P(\hat{y}=1 | z=1, y=1)}{P(\hat{y}=1 | z=0, y=1)},
        \frac{P(\hat{y}=1 | z=0, y=1)}{P(\hat{y}=1 | z=1, y=1)}\right)

    This is especially useful to use in situations where "fairness" is a theme.

    Usage:
    `equal_opportunity_score('gender')(clf, X, y)`

    Source:
    - M. Hardt, E. Price and N. Srebro (2016), Equality of Opportunity in Supervised Learning

    :param sensitive_column:
        Name of the column containing the binary sensitive attribute (when X is a dataframe)
        or the index of the column (when X is a numpy array).
    :param positive_target: The name of the class which is associated with a positive outcome
    :return: a function (clf, X, y_true) -> float that calculates the equal opportunity score for z = column
    """

    def impl(estimator, X, y_true):
        """Remember: X is the thing going *in* to your pipeline."""
        sensitive_col = (
            X[:, sensitive_column] if isinstance(X, np.ndarray) else X[sensitive_column]
        )

        if not np.all((sensitive_col == 0) | (sensitive_col == 1)):
            raise ValueError(
                f"equal_opportunity_score only supports binary indicator columns for `column`. "
                f"Found values {np.unique(sensitive_col)}"
            )

        y_hat = estimator.predict(X)
        y_given_z1_y1 = y_hat[(sensitive_col == 1) & (y_true == positive_target)]
        y_given_z0_y1 = y_hat[(sensitive_col == 0) & (y_true == positive_target)]

        # If we never predict a positive target for one of the subgroups, the model is by definition not
        # fair so we return 0
        if len(y_given_z1_y1) == 0:
            warnings.warn(
                f"No samples with y_hat == {positive_target} for {sensitive_column} == 1, returning 0",
                RuntimeWarning,
            )
            return 0

        if len(y_given_z0_y1) == 0:
            warnings.warn(
                f"No samples with y_hat == {positive_target} for {sensitive_column} == 0, returning 0",
                RuntimeWarning,
            )
            return 0

        p_y1_z1 = np.mean(y_given_z1_y1 == positive_target)
        p_y1_z0 = np.mean(y_given_z0_y1 == positive_target)
        score = np.minimum(p_y1_z1 / p_y1_z0, p_y1_z0 / p_y1_z1)
        return score if not np.isnan(score) else 1

    return impl
