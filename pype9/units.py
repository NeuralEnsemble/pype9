import numpy as np


def fincke_pohst_algorithm(A, b):
    """
    `A` -- m X m integer matrix
    `b` -- m vector

    Finds the vector x that solves Ax=b with smallest norm??
    """
    # Get the length of the vector b
    m = len(b)
    count = 0
    # Set up required arrays
    x = np.zeros(m)  # An array to hold the shortest vector
    T = np.zeros(m)  # An array to hold all the versions of T
    U = np.zeros(m)  # An array to hold all the versions of U
    # Initialise the index from m-1 not m because Python indexing starts from 0
    # not 1
    i = m - 1
    T[i] = np.sum(np.diag(A) * b ** 2)  # NB: diag extracts the diagonal elem
    U[i] = 0
    while True:
        Z = (T[i] / A[i][i]) ** 1 / 2
        UB[i] = np.floor(Z + b[i] - U[i])  # What is UB here, U * B[i]??
        x[i] = -np.floor(Z + U[i] - b[i]) - 1
        while True:
            x[i] = x[i] + 1
            if x[i] <= UB[i]:
                if i == 1:
                    count += 1
                else:
                    i -= 1
                    k = i + 1   # to save writing out i + 1
                    U[i] = np.sum(A[i, k:] * x[k:])
                    T[i] = T[k] - A[k][k] * (x[k] + U[k] - b[k]) ** 2
                    break
            else:
                i += 1
                if i > m:
                    return x[count:]  # print the count shortest multipliers??
