#!/usr/bin/env python3
# coding: utf-8

import os
import sys
import matplotlib

matplotlib.use("tkAgg")
import matplotlib.pyplot as plt

sys.path.append(os.environ["REFLOW"])

import common.series as series
import common.relog as relog
import common.utils as utils
from packages.parsers import ltspice_raw


def main(db):
    warnings, errors = 0, 0
    time = db["time"]
    # 1.5 ns after V(a)/V(b) change
    va = series.Series(time, db["values"].get("V(a)"))
    vb = series.Series(time, db["values"].get("V(a)"))
    crossing_times = va.cross(va.max_value() / 2)
    crossing_times.extend(vb.cross(vb.max_value() / 2))
    # check results V(out) = V(out_ref)
    vout = series.Series(time, db["values"].get("V(q)"))
    vout_ref = series.Series(time, db["values"].get("V(q_ref)"))

    nb_steps = db["nb_steps"]
    steps_idx = db["steps_idx"]

    utils.graphs.default_plot_style()
    plt.figure(figsize=(4, max(3, nb_steps * 1.5)))
    for i, idxs in enumerate(steps_idx):
        l, h = idxs
        plt.subplot(311 + i)
        plt.plot(vout_ref.x[l:h] * 1e9, vout_ref.y[l:h])
        plt.plot(vout.x[l:h] * 1e9, vout.y[l:h])
        plt.xlabel("Time [ns]")
        plt.ylabel("Voltage [V]")
    plt.tight_layout()
    plt.savefig("%s/xor.svg" % os.getenv("WORK_DIR"))

    tolerance = (vout_ref.max_value() - vout_ref.min_value()) * 0.01
    for t_change in crossing_times:
        t_check = t_change + 1.5e-9
        y = vout.value_at(t_check)
        y_ref = vout_ref.value_at(t_check)
        # check value and give more details
        if abs(y_ref - y) > tolerance:
            relog.error(
                "unexpected output at t = %e: get %.3f V and expect %.3f V +- %.3f V"
                % (t_check, y, y_ref, tolerance)
            )
            errors += 1
    # return values for regressions
    return warnings, errors


if __name__ == "__main__":
    raw_path = next((f for f in sys.argv[1:] if f != __file__))
    db = ltspice_raw.load_raw(raw_path)
    main(db)
