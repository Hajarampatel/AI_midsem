

import math
import re
import sys

import numpy as np

"""# Initialization"""

# number of states in the model
N = 2

# number of observation symbols
M = 27

# state transition probabilities
A = np.array([[0.47468, 0.52532], [0.51656, 0.48344]])

# observation probability matrix
B = np.array([[0.03735, 0.03408, 0.03455, 0.03828, 0.03782, 0.03922, 0.03688, 0.03408, 0.03875, 0.04062, 0.03735, 0.03968, 0.03548, 0.03735, 0.04062, 0.03595, 0.03641, 0.03408, 0.04062, 0.03548, 0.03922, 0.04062, 0.03455, 0.03595, 0.03408, 0.03408, 0.03688], 
              [0.03909, 0.03537,  0.03537, 0.03909, 0.03583,  0.03630, 0.04048, 0.03537, 0.03816, 0.03909, 0.03490, 0.03723, 0.03537, 0.03909, 0.03397, 0.03397, 0.03816, 0.03676, 0.04048, 0.03443, 0.03537, 0.03955, 0.03816,  0.03723,  0.03769, 0.03955, 0.03397]])

# initial state distribution
pi = np.array([[0.51316, 0.48684]])

max_iters = 100

old_log_prob = -math.inf

# observation sequence

O = np.zeros(50000, dtype=int)

file = "war_and_peace.txt"

f = open(file, "r", encoding='utf-8')
content = f.read()
f.close()

# Remove the punctuations
content = re.sub('[^a-zA-Z]', " ", content)
content = " ".join(content.split()).lower()[:50000]

# map the letters and the space to the respective indexes
dictionary = {}
for i in range(26):
    # ASCII value for the each character in the alphabet
    dictionary[chr(i+97)] = i
dictionary[" "] = 26


# adding the values to the observation list/sequence
for i in range(len(content)):
    O[i] = dictionary[content[i]]

# length of the observation sequence
T = len(O)


def estimate(A, B, pi, T, M, O, old_log_prob):
    # alpha-pass
    c = np.zeros([T, 1])
    alpha = np.zeros([T, N])
    c[0][0] = 0

    for i in range(N):
        alpha[0][i] = pi[0][i]*B[i][O[0]]
        c[0][0] = c[0][0] + alpha[0][i]

    # scale the alpha[0][i]
    c[0][0] = 1/c[0][0]
    for i in range(N):
        alpha[0][i] = c[0][0]*alpha[0][i]

    # compute alpha[t][i]
    for t in range(1, T):
        c[t][0] = 0
        for i in range(N):
            alpha[t][i] = 0
            for j in range(N):
                alpha[t][i] = alpha[t][i] + alpha[t-1][j]*A[j][i]

            alpha[t][i] = alpha[t][i]*B[i][O[t]]
            c[t][0] = c[t][0] + alpha[t][i]

        c[t][0] = 1/c[t][0]
        for i in range(N):
            alpha[t][i] = c[t][0]*alpha[t][i]


    # beta-pass
    beta = np.zeros([T, N])

    for i in range(N):
        beta[T-1][i] = c[T-1][0]

    for t in range(T-2, -1, -1):
        for i in range(N):
            beta[t][i] = 0
            for j in range(N):
                beta[t][i] = beta[t][i] + A[i][j]*B[j][O[t+1]]*beta[t+1][j]
            
            # scale the beta[t][i]
            beta[t][i] = c[t][0]*beta[t][i]


    # compute gamma[t][i][j] and gamma[t][i]
    di_gamma = np.zeros([T, N, N])
    gamma = np.zeros([T, N])

    for t in range(T-1):
        for i in range(N):
            gamma[t][i] = 0
            for j in range(N):
                di_gamma[t][i][j] = alpha[t][i]*A[i][j]*B[j][O[t+1]]*beta[t+1][j]
                gamma[t][i] = gamma[t][i] + di_gamma[t][i][j]


    # handling the case for gamma[T-1][i]
    for i in range(N):
        gamma[T-1][i] = alpha[T-1][i]


    # re-estimate A, B and pi
    # re-estimate pi
    for i in range(N):
        pi[0][i] = gamma[0][i]

    # re-estimate A
    for i in range(N):
        denominator = 0
        for t in range(T-1):
            denominator = denominator + gamma[t][i]

        for j in range(N):
            numerator = 0
            for t in range(T-1):
                numerator = numerator + di_gamma[t][i][j]
            A[i][j] = numerator/denominator


    # re-estimate B
    for i in range(N):
        denominator = 0
        for t in range(T):
            denominator = denominator + gamma[t][i]
        
        for j in range(M):
            numerator = 0
            for t in range(T):
                if O[t] == j:
                    numerator = numerator + gamma[t][i]
            
            B[i][j] = numerator/denominator


    # compute log(P(O/lambda))
    log_prob = 0
    for i in range(T):
        log_prob = log_prob + math.log(c[i][0])

    log_prob = -1 * log_prob



    if log_prob > old_log_prob:
        old_log_prob = log_prob

    return A, B, pi, old_log_prob


a, b, p, log_probability = estimate(A, B, pi, T, M, O, old_log_prob)

for i in range(max_iters):
    sys.stdout.write("\r")
    sys.stdout.write("Percentage completed: %d%%" % ((i * 100)/ max_iters))
    sys.stdout.flush()
    a, b, p, log_probability = estimate(a, b, p, T, M, O, log_probability)

print("\n")
print("\nState transition matrix: \n", a)
print("\n Observation probability matrix: \n", b)
print("\n Pi: \n", p)
print("\nLog Probability log(P(O/lambda)): ", log_probability)
