from scipy.stats import binom_test
import numpy as np


a = binom_test(9, 10, 0.5, "two-sided")
b = binom_test(9, 10, 0.5, "greater")
c = binom_test(9, 10, 0.5, "less")
d = np.log(b)
e = -np.log(a)
print('two-sided:', a, "\n",
      'greater:', b, "\n",
      'less:', c, "\n",
      'complement of two-sided:', 1-a, "\n",
      'complement of greater:', 1-b, "\n",
      'complement of less:', 1-c)

print(d, e)

