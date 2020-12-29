#!/usr/bin/env python3
# coding: utf-8

import os
import sys

import matplotlib
import numpy as np
import scipy
from scipy import signal

matplotlib.use("tkAgg")
import matplotlib.pyplot as plt

sys.path.append(os.environ["REFLOW"])

import common.series as series
import common.relog as relog
import common.utils as utils
from analog.tools.parsers import ltspice_raw


def Mag(v, n=2, db=True, scale=1.0):
    if db:
        return 20 * np.log10(2 * np.abs(v) / n / scale)
    return 2 * np.abs(v) / n / scale


def Deg(v):
    ang = 180 / np.pi * np.arctan2(v.imag, v.real)
    return np.where(ang > 0, ang, 360 + ang)


def main(db):
    warnings, errors = 0, 0
    time = db["time"]

    n = len(time)
    Ts = (np.max(time) - np.min(time)) / n
    relog.info("N=%d\tFs=%e" % (n, 1 / Ts))

    # resample since spice is variable timestep
    Nn = 2 ** 16
    Ts = (np.max(time) - np.min(time)) / Nn
    time = np.linspace(np.min(time), np.max(time), Nn)
    freq = np.fft.fftfreq(Nn, d=Ts)

    # fft window
    # beta 	Window shape
    # 0 	Rectangular
    # 5 	Similar to a Hamming
    # 6 	Similar to a Hanning
    # 8.6 	Similar to a Blackman
    beta = 6
    db_unit = True
    window = np.kaiser(Nn, beta)

    # get maximum of window to compensate amplitude
    TFwindow = scipy.fft.fft(window)
    Amax = np.max(Mag(TFwindow, Nn, False))

    relog.info("kaiser(beta=%.3f) ScaleAmp=%.3f" % (beta, Amax))

    # read V(out), V(out_ref)
    tmp = signal.resample(db["values"].get("V(out)"), Nn)
    vout = series.Series(time, tmp)

    tmp = signal.resample(db["values"].get("V(out_ref)"), Nn)
    vout_ref = series.Series(time, tmp)

    # calculate the fft
    TFvout = scipy.fft.fft(np.multiply(vout.y, window))
    TFvout_ref = scipy.fft.fft(np.multiply(vout_ref.y, window))

    utils.graphs.default_plot_style()
    plt.figure(figsize=(4, 6))
    plt.subplot(311)
    plt.semilogx(freq, Mag(TFvout, Nn, db_unit, Amax), "r-")
    plt.semilogx(freq, Mag(TFvout_ref, Nn, db_unit, Amax), "b-")
    plt.xlabel("Frequency [Hz]")
    plt.ylabel("Magnitude [%s]" % ("dB" if db_unit else "V"))
    plt.grid(True, which="both")
    if db_unit:
        plt.axis([1e6, 5e8, -120, 0])
    else:
        plt.axis([1e6, 5e8, 0, 0.6])

    plt.subplot(312)
    plt.semilogx(freq, Deg(TFvout), "r--")
    plt.semilogx(freq, Deg(TFvout_ref), "b--")
    plt.xlabel("Frequency [Hz]")
    plt.ylabel("Magnitude [$^\circ$]")
    plt.grid(True, which="both")
    plt.axis([1e6, 5e8, 0, 360])

    plt.subplot(313)
    plt.plot(db["time"], db["values"].get("V(out)"), "g-")
    plt.plot(vout.x * 1e9, vout.y, "r-")
    plt.plot(vout_ref.x * 1e9, vout_ref.y, "b--")
    plt.xlabel("Time [ns]")
    plt.ylabel("Voltage [V]")
    plt.axis([750, 800, 0.5, 2])

    plt.tight_layout()
    plt.savefig("%s/spectrum.svg" % os.getenv("WORK_DIR"))

    # return values for regressions
    return warnings, errors


if __name__ == "__main__":
    raw_path = next((f for f in sys.argv[1:] if f != __file__))
    db = ltspice_raw.load_raw(raw_path)
    main(db)