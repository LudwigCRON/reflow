#!/usr/bin/env python3
# coding: utf-8

import matplotlib as mpl


def default_plot_style():
    mpl.rcParams["font.family"] = "serif"
    mpl.rcParams["font.size"] = 8
    mpl.rcParams["figure.figsize"] = (4, 3)
    mpl.rcParams["figure.dpi"] = 200
    mpl.rcParams["savefig.dpi"] = 300
    mpl.rcParams["axes.labelsize"] = 8
    mpl.rcParams["xtick.labelsize"] = 10
    mpl.rcParams["ytick.labelsize"] = 10
    mpl.rcParams["legend.fontsize"] = 10
    mpl.rcParams["lines.linewidth"] = 1
    mpl.rcParams["errorbar.capsize"] = 3
    mpl.rcParams["mathtext.fontset"] = "cm"
    mpl.rcParams["mathtext.rm"] = "serif"
    mpl.rcParams["text.usetex"] = False
    mpl.rcParams["image.cmap"] = "cividis"
