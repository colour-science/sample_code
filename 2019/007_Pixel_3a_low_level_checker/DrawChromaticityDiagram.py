#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Chromaticity Diagram の描画を担当
"""

# 外部ライブラリのインポート
import cv2
import matplotlib.pyplot as plt
from colour import RGB_to_RGB
from colour.models import BT2020_COLOURSPACE, sRGB_COLOURSPACE

# 自作ライブラリのインポート
import test_pattern_generator2 as tpg
import plot_utility as pu
import transfer_functions as tf

# 位置パラメータ。原則、width に乗算してピクセル値に変換する
font_size = 12  # 1920x1080 相当で指定
dpi_px_rate = 7063 / 9000
dpi = 96

# define
png_file_name = './intermediate/diagram.png'
UNIVERSAL_COLOR_LIST = ["#F6AA00", "#FFF100", "#03AF7A",
                        "#005AFF", "#4DC4FF", "#804000"]


class DrawChromaticityDiagram:
    """
    特記事項なし
    """
    def __init__(self, base_param, draw_param, img):
        self.base_param = base_param
        self.draw_param = draw_param
        self.img = img

    def get_img_width(self):
        return self.img.shape[1]

    def get_img_height(self):
        return self.img.shape[0]

    def int(self, x):
        return int(x + 0.5)

    def draw_chromaticity_diagram(self):
        self.make_chromaticity_diagram_image()
        self.composite_chromaticity_diagram()

    def composite_chromaticity_diagram(self):
        img_width = self.get_img_width()

        fig_img = cv2.imread(png_file_name,
                             cv2.IMREAD_ANYDEPTH | cv2.IMREAD_COLOR)[..., ::-1]
        fig_img = fig_img / 0xFF
        fig_img = self.convert_srgb_to_bt2020(fig_img)
        fig_img = fig_img * self.base_param['reference_white']

        chromaticity_space_rate = (1 - self.base_param['pattern_space_rate'])
        width = self.int(img_width * chromaticity_space_rate)

        convert_rate = width / fig_img.shape[1]
        height = self.int(fig_img.shape[0] * convert_rate)

        fig_img = cv2.resize(fig_img, (width, height))

        tpg.merge(self.img, fig_img, (self.get_img_width() - width, 0))

        # text描画用に情報を保存
        self.width = width
        self.height = height

    def get_diagram_widgh_height(self):
        return self.width, self.height

    def convert_srgb_to_bt2020(self, img):
        """
        sRGB の 画像(range: 0.0-1.0) を BT.2020 色域、絶対輝度に変換する。
        """
        linear_srb = tf.eotf(img, tf.SRGB)
        img = RGB_to_RGB(linear_srb, sRGB_COLOURSPACE, BT2020_COLOURSPACE)
        return img

    def make_chromaticity_diagram_image(
            self, xmin=0.0, xmax=0.8, ymin=0.0, ymax=0.9):
        """
        一度、pngファイルの形式で色度図を作る。
        """
        xy_image = tpg.get_chromaticity_image(
            xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)
        cmf_xy = tpg._get_cmfs_xy()
        xlim = (min(0, xmin), max(0.8, xmax))
        ylim = (min(0, ymin), max(0.9, ymax))
        chromaticity_space_rate = (1 - self.base_param['pattern_space_rate'])
        figure_width = self.int(self.get_img_width() * chromaticity_space_rate)
        figsize_h = figure_width/dpi_px_rate/dpi
        figsize_v = figsize_h / 9 * 8
        rate = (self.get_img_height() / 1080)

        # gamut の用意
        outer_gamut = self.base_param['outer_primaries']
        inner_gamut = self.base_param['inner_primaries']
        outer_name = self.base_param['outer_gamut_name']
        inner_name = self.base_param['inner_gamut_name']
        outer_xy = self.draw_param['outer_xyY']
        inner_xy = self.draw_param['inner_xyY']

        ax1 = pu.plot_1_graph(fontsize=20 * rate,
                              dpi=dpi,
                              figsize=(figsize_h,
                                       figsize_v),
                              graph_title="CIE1931 Chromaticity Diagram",
                              graph_title_size=None,
                              xlabel=None, ylabel=None,
                              axis_label_size=None,
                              legend_size=18 * rate,
                              xlim=xlim, ylim=ylim,
                              xtick=[x * 0.1 + xmin for x in
                                     range(int((xlim[1] - xlim[0])/0.1) + 1)],
                              ytick=[x * 0.1 + ymin for x in
                                     range(int((ylim[1] - ylim[0])/0.1) + 1)],
                              xtick_size=17 * rate,
                              ytick_size=17 * rate,
                              linewidth=4 * rate,
                              minor_xtick_num=2,
                              minor_ytick_num=2)
        ax1.plot(cmf_xy[..., 0], cmf_xy[..., 1], '-k', lw=3.5*rate, label=None)
        ax1.plot((cmf_xy[-1, 0], cmf_xy[0, 0]), (cmf_xy[-1, 1], cmf_xy[0, 1]),
                 '-k', lw=3.5*rate, label=None)
        ax1.plot(inner_gamut[:, 0], inner_gamut[:, 1],
                 c=UNIVERSAL_COLOR_LIST[0], label=inner_name, lw=2.75*rate)
        ax1.plot(outer_gamut[:, 0], outer_gamut[:, 1],
                 c=UNIVERSAL_COLOR_LIST[3], label=outer_name, lw=2.75*rate)
        ax1.plot(tpg.D65_WHITE[0], tpg.D65_WHITE[1], marker='x', c='k',
                 lw=2.75*rate, label='D65', ms=10*rate, mew=2.75*rate)
        ax1.plot(inner_xy[..., 0], inner_xy[..., 1], ls='', marker='s',
                 c='#606060')
        ax1.plot(outer_xy[..., 0], outer_xy[..., 1], ls='', marker='s',
                 c='#202020')
        ax1.imshow(xy_image, extent=(xmin, xmax, ymin, ymax))
        plt.legend(loc='upper right')
        plt.savefig(png_file_name, bbox_inches='tight', dpi=dpi)
        # plt.show()


if __name__ == '__main__':
    pass
