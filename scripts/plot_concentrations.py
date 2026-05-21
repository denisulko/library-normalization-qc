import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("results/normalized_samples.csv")

df["conc_ng_ul"].hist()

plt.xlabel("Concentration (ng/uL)")
plt.ylabel("Sample count")
plt.title("Library concentration distribution")

plt.savefig("results/concentration_distribution.png")