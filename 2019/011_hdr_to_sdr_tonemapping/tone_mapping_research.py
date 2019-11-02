#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import numpy as np
import matplotlib.pyplot as plt
import cv2

# 自作ライブラリのインポート
import TyImageIO as tyio
import OpenImageIO as oiio
import transfer_functions as tf
import plot_utility as pu
from scipy.interpolate import interp1d, splrep
from sympy import symbols, solve
from sympy.utilities.lambdify import lambdify

src_exr = "./img/SMPTE ST2084_ITU-R BT.2020_D65_1920x1080_rev03_type1.exr"
dst_exr = "./img/SMPTE ST2084_ITU-R BT.2020_D65_1920x1080_rev03_type1_c.exr"
after_3dlut_exr = "./img/after_3dlut_with_pq_oetf.exr"
sdr_eotf = tf.SRGB

st_pos_h = 57
st_pos_v = 289
h_sample = 1024


def dump_attr(fname, attr):
    print("attr data of {} is as follows.".format(fname))
    print(attr)


def dump_img_info(img):
    print("shape: ", img.shape)
    print("dtype: ", img.dtype)
    print("min: ", np.min(img))
    print("max: ", np.max(img))


def correct_pq_exr_gain():
    """
    exrファイルだと PQ のピークが 100.0 なので
    1.0 になるように正規化する。
    """
    reader = tyio.TyReader(src_exr)
    img = reader.read()
    dump_attr(src_exr, reader.get_attr())
    dump_img_info(img)
    writer = tyio.TyWriter(img / 100.0, dst_exr)
    writer.write(out_img_type_desc=oiio.FLOAT)


def check_after_3dlut_exr():
    """
    3DLUT通過後のデータを確認
    """
    reader = tyio.TyReader(after_3dlut_exr)
    img = reader.read()
    dump_attr(after_3dlut_exr, reader.get_attr())
    dump_img_info(img)


def plot_eetf(eetf):
    """
    EETF のプロット
    """
    x = np.linspace(0, 1, h_sample)
    y_simulation = youtube_tonemapping(x, 400, 1000)
    y = eetf[st_pos_v, st_pos_h:st_pos_h+h_sample, 1]
    ax1 = pu.plot_1_graph(
        fontsize=20,
        figsize=(12, 10),
        graph_title="Tone mapping characteristics",
        graph_title_size=None,
        xlabel="ST2084 Code Value",
        ylabel="ST2084 Code Value",
        axis_label_size=None,
        legend_size=17,
        xlim=None,
        ylim=None,
        xtick=None,
        ytick=None,
        linewidth=3,
        minor_xtick_num=None,
        minor_ytick_num=None)
    # ax1.set_xscale('log', basex=10.0)
    # ax1.set_yscale('log', basey=10.0)
    # ax1.plot(x_luminance, y_luminance, 'o', label="YouTube HDR to SDR EETF")
    ax1.plot(x, y, 'o', label="YouTube HDR to SDR EETF")
    # ax1.plot(x, y_18, '-', label="18% gray to 100% white")
    ax1.plot(x, y_simulation, '-', label="emulation")
    # x_val = [1.0 * (10 ** (x - 4)) for x in range(9)]
    # x_caption = [r"$10^{{{}}}$".format(x - 4) for x in range(9)]
    # plt.xticks(x_val, x_caption)
    # y_caption = [r"$10^{{{}}}$".format(x - 4) for x in range(9)]
    # y_val = [1.0 * (10 ** (x - 4)) for x in range(9)]
    # plt.yticks(y_val, y_caption)
    plt.legend(loc='upper left')
    plt.savefig(
        "./blog_img/eetf_codevalue.png", bbox_inches='tight', pad_inches=0.1)
    plt.show()


def plot_eetf_luminance(eetf):
    """
    EETF のプロットを輝度値ベースで
    """
    img = cv2.imread("./img/youtubed_sdr_tp.png")
    y_ref = ((img[3, :, 1] / 255.0) ** 2.4) * 100
    x = np.linspace(0, 1, h_sample)
    y_simulation = youtube_tonemapping(x, 400, 1000)
    y = eetf[st_pos_v, st_pos_h:st_pos_h+h_sample, 1]
    y_sim_luminance = tf.eotf_to_luminance(y_simulation, tf.ST2084)
    y_luminance = tf.eotf_to_luminance(y, tf.ST2084)
    x_luminance = tf.eotf_to_luminance(x, tf.ST2084)
    ax1 = pu.plot_1_graph(
        fontsize=20,
        figsize=(12, 10),
        graph_title="Tone mapping characteristics",
        graph_title_size=None,
        xlabel="Luminance [cd/m2]",
        ylabel="Luminance [cd/m2]",
        axis_label_size=None,
        legend_size=17,
        xlim=(-75, 1200),
        ylim=(-5, 105),
        xtick=[x * 100 for x in range(13)],
        ytick=[x * 10 for x in range(11)],
        linewidth=3,
        minor_xtick_num=None,
        minor_ytick_num=None)
    # ax1.set_xscale('log', basex=10.0)
    # ax1.set_yscale('log', basey=10.0)
    # ax1.plot(x_luminance, y_luminance, 'o', label="YouTube HDR to SDR EETF")
    ax1.plot(x_luminance, y_luminance, 'o', label="YouTube HDR to SDR EETF")
    ax1.plot(x_luminance, y_sim_luminance, '-', label="approximation")
    ax1.plot(x_luminance, y_ref, 'o', label="youtube")
    # x_val = [1.0 * (10 ** (x - 4)) for x in range(9)]
    # x_caption = [r"$10^{{{}}}$".format(x - 4) for x in range(9)]
    # plt.xticks(x_val, x_caption)
    # y_caption = [r"$10^{{{}}}$".format(x - 4) for x in range(9)]
    # y_val = [1.0 * (10 ** (x - 4)) for x in range(9)]
    # plt.yticks(y_val, y_caption)
    plt.legend(loc='upper left')
    plt.savefig(
        "./blog_img/eetf_luminance.png", bbox_inches='tight', pad_inches=0.1)
    plt.show()


def dump_eetf_info(eetf):
    """
    18% Gray, 100% White などの情報をダンプする
    """

    x_18_gray = tf.oetf_from_luminance(18.0, tf.ST2084)
    x_100_white = tf.oetf_from_luminance(100.0, tf.ST2084)
    x_ref_white = tf.oetf_from_luminance(250.0, tf.ST2084)
    x_18_idx = int(np.round(x_18_gray * 1023))
    x_100_idx = int(np.round(x_100_white * 1023))
    x_ref_idx = int(np.round(x_ref_white * 1023))
    print(x_18_gray, x_100_white, x_ref_white)
    print(x_18_idx, x_100_idx, x_ref_idx)
    y = eetf[st_pos_v, st_pos_h:st_pos_h+h_sample, 1]
    print("18 Gray = {}".format(y[x_18_idx]))
    print("100 white = {}".format(y[x_100_idx]))
    print("250 white = {}".format(y[x_ref_idx]))
    a = (y[x_100_idx] - y[x_18_idx]) / (x_100_white - x_18_gray)
    b = a * -x_18_gray + y[x_18_idx]
    print(a)
    print(b)
    a = 0.74
    b = a * -x_100_white + y[x_100_idx]
    print(a)
    print(b)
    print(tf.eotf_to_luminance(0.0117522745451, tf.ST2084))
    print(tf.eotf_to_luminance(0.3877303064680016, tf.ST2084))


def analyze_eetf():
    reader = tyio.TyReader(after_3dlut_exr)
    img = reader.read()
    # img_after_sdr_eotf = tf.eotf(img, sdr_eotf)
    img_after_sdr_eotf = img ** 2.4
    img_after_pq_oetf = tf.oetf(img_after_sdr_eotf / 100, tf.ST2084)
    eetf = img_after_pq_oetf
    # dump_eetf_info(eetf)
    plot_eetf(eetf)
    plot_eetf_luminance(eetf)


def spline_example():
    data = [[0.5, 0.5], [0.8, 1.0], [1.0, 1.0]]
    func = get_top_side_bezier(data)
    x = np.linspace(data[0][0], data[2][0], 256)
    y = func(x)
    ax1 = pu.plot_1_graph(
        fontsize=20,
        figsize=(12, 10),
        graph_title="interpolation",
        graph_title_size=None,
        xlabel=None,
        ylabel=None,
        axis_label_size=None,
        legend_size=17,
        xlim=None,
        ylim=None,
        xtick=None,
        ytick=None,
        linewidth=3,
        minor_xtick_num=None,
        minor_ytick_num=None)
    ax1.plot(x, y, 'o', label="Original Sample")
    # ax1.plot(x2, y2_linear, '-', label="linear interpolation")
    # ax1.plot(x2, y2_cubic, '-', label="cubic interpolation")
    plt.legend(loc='upper left')
    # plt.savefig("./blog_img/eetf.png", bbox_inches='tight', pad_inches=0.1)
    plt.show()


def get_top_side_bezier(param=[[0.6, 0.7], [0.8, 1.0], [1.0, 1.0]]):
    """
    Note
    ----
    An example of ```top_param``` is bellow.
        {'x0': 0.5, 'y0': 0.5,
         'x1': 0.7, 'y1': 0.7,
         'x2': 1.0, 'y2': 0.7}
    """
    a_val = param[0][0]
    b_val = param[1][0]
    c_val = param[2][0]
    p_val = param[0][1]
    q_val = param[1][1]
    r_val = param[2][1]

    a, b, c, t, x = symbols('a, b, c, t, x')
    f = (1 - t)**2 * a + 2 * (1 - t) * t * b + t**2 * c - x

    # x について解く
    # ----------------------
    t = solve(f, t)[1]
    t = t.subs({a: a_val, b: b_val, c: c_val})

    # y と t(ここでは u と置いた) の関係式を記述
    # -------------------------------------------
    p, q, r, u, y = symbols('p, q, r, u, y')
    y = (1 - u)**2 * p + 2 * (1 - u) * u * q + u**2 * r

    # パラメータ u と事前に求めた t で置き換える
    # -------------------------------------------
    y = y.subs({p: p_val, q: q_val, r: r_val, u: t})

    func = lambdify(x, y, 'numpy')

    return func


def youtube_linear(x):
    return 0.74 * x + 0.01175


def youtube_tonemapping(x, ks_luminance=400, ke_luminance=1000):
    """
    YouTube の HDR to SDR のトーンマップを模倣してみる。
    中間階調までは直線で、高階調部だけ2次ベジェ曲線で丸める。

    直線の数式は $y = 0.74x + 0.01175$。
    y軸の最大値は 0.508078421517 (100nits)。
    この時の x は $x = (0.508078421517 - 0.01175) / 0.74$ より
    0.6707140831310812 。ちなみに、リニアなら 473.5 nits。

    ks は knee start の略。ke は knee end.
    """
    ks_x = tf.oetf_from_luminance(ks_luminance, tf.ST2084)
    ks_y = youtube_linear(ks_x)
    ke_x = tf.oetf_from_luminance(ke_luminance, tf.ST2084)
    ke_y = tf.oetf_from_luminance(100, tf.ST2084)
    mid_x = 0.6707140831310812
    mid_y = ke_y
    bezie = get_top_side_bezier([[ks_x, ks_y], [mid_x, mid_y], [ke_x, ke_y]])
    y = np.select(
        (x < ks_x, x <= ke_x, x > ke_x),
        (youtube_linear(x), bezie(x), ke_y))

    return y


def test_plot_youtube_tonemapping(ks_luminance=400, ke_luminance=1000):
    x = np.linspace(0, 1, 1024)
    y = youtube_tonemapping(x, ks_luminance, ke_luminance)
    ax1 = pu.plot_1_graph(
        fontsize=20,
        figsize=(12, 10),
        graph_title="Tone mapping characteristics",
        graph_title_size=None,
        xlabel="ST2084 Code Value",
        ylabel="ST2084 Code Value",
        axis_label_size=None,
        legend_size=17,
        xlim=None,
        ylim=None,
        xtick=None,
        ytick=None,
        linewidth=3,
        minor_xtick_num=None,
        minor_ytick_num=None)
    ax1.plot(x, y, 'o', label="emulation")
    plt.legend(loc='upper left')
    plt.show()


def analyze_gamut_mapping():
    pass


def main_func():
    # correct_pq_exr_gain()
    # check_after_3dlut_exr()
    analyze_eetf()
    analyze_gamut_mapping()
    # spline_example()
    # test_plot_youtube_tonemapping()


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main_func()
