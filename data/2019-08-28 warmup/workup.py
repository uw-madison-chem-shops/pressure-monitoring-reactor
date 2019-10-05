import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

xi, yi = np.genfromtxt("1567016596.txt", delimiter=",").T
print(xi, yi)

failed = (np.abs(np.diff(yi)) > 0.5)

xi = xi[1:]
xi -= xi.min()
xi /= 60
yi = yi[1:]

for shift in range(-2, 2):
    yi[np.roll(failed, shift)] = np.nan

for f, y in zip(failed, yi):
    print(f, y)

plt.scatter(xi, yi)
plt.grid()
plt.xlabel("time elapsed (min)", fontsize=20)
plt.ylabel("temp (deg C)", fontsize=20)
plt.savefig("warmup.png", bbox_inches="tight")
