import pathlib
import os
import numpy as np
import matplotlib.pyplot as plt
import tidy_headers


__here__ = pathlib.Path(__file__).absolute().parent


with open(__here__ / "colors.txt", "r") as f:
    colors = [line.strip() for line in f]


def plot_file(path):
    path = str(os.path.abspath(path))
    #
    array = np.genfromtxt(path).T
    xi = array[0] - array[0].min()
    xi /= 60  # seconds to minutes
    # absolute pressure
    plt.subplot(211)
    plt.grid()
    plt.xlim(0, xi.max())
    plt.setp(plt.gca().get_xticklabels(), visible=False)
    plt.ylabel("PSI")
    for i in range(12):
        c = colors[i]
        plt.plot(xi, array[i + 2], c=c, label=f"sensor {i}")
    # differential pressure
    plt.subplot(212)
    plt.grid()
    plt.xlim(0, xi.max())
    plt.xlabel("time elapsed (min)")
    plt.ylabel("ΔPSI")
    for i in range(12):
        c = colors[i]
        yi = array[i + 2]
        yi -= np.nanmax(yi)
        plt.plot(xi, yi, c=c, label=f"sensor {i}")
    plt.gca().legend(loc=(1.05, 0.5), framealpha=0)
    # save
    fpath = path.replace(".txt", ".png")
    plt.savefig(fpath, bbox_inches="tight", dpi=300, transparent=True)


if __name__ == "__main__":
    path = pathlib.Path(os.path.expanduser("~"))
    path /= "Desktop"
    path /= "gas-uptake-data"
    path /= "gas-uptake_2019-10-30_08-41-20.txt"
    plot_file(path)
