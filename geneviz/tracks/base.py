from __future__ import absolute_import, division, print_function

#pylint: disable=W0622,W0611
from builtins import (ascii, bytes, chr, dict, filter, hex, input,
                      int, map, next, oct, open, pow, range, round,
                      str, super, zip)

import numpy as np
from matplotlib import pyplot as plt

try:
    import seaborn as sns
except ImportError:
    sns = None


class Track(object):
    """Abstract base class representing a Geneviz track.

    Specifies one method (draw) that should be overridden in each
    Track subclass, as this is the method that is called on each
    track object by plot_tracks.

    """

    def __init__(self):
        super().__init__()

    def draw(self, axis, seqname, start, end):
        """Draws the track on the given axis.

        Args:
            axis (matplotlib.Axes): Axis to draw track on.
            seqname (str): Chromosome to draw.
            start (int): Start of draw region.
            end (int): End of draw region.
        """
        raise NotImplementedError()

    #pylint: disable=unused-argument
    def get_height(self, axis, seqname, start, end):
        """Returns the height of the track within the plotting region.

        Args:
            axis (matplotlib.Axes): Axis to draw track on.
            seqname (str): Chromosome to draw.
            start (int): Start of draw region.
            end (int): End of draw region.
        """

        return 1


def plot_tracks(tracks, seqname, start, end, figsize=None,
                height_ratios=None, tick_top=False,
                padding=(0, 0), reverse=False, despine=False):
    """Plots given tracks over the specified range on shared axes.

    Args:
        tracks (List[Track]): List of tracks to plot.
        seqname (str): Chromosome name.
        start (int): Start of plot region.
        end (int): End of plot region.
        figsize (tuple[int, int]): Size of resulting figure.
        height_ratios (List[int]): Relative heights of each track.
        tick_top (bool): Whether xticks should be plotted along top.
        padding (int, int): Amount of padding to add on the x-axis.
        reverse (bool): Whether the x-axis should be reversed.

    Returns:
        fig: Figure on which was drawn.
        axes: Each of the axes.

    """

    if height_ratios is None:
        height_ratios = _calc_height_ratios(
            tracks, seqname, start, end, figsize)

    # Create shared axes.
    figsize = _calc_figsize(figsize, height_ratios)

    fig, axes = plt.subplots(
        nrows=len(tracks), sharex=True, figsize=figsize,
        gridspec_kw={'height_ratios': height_ratios})
    axes = [axes] if len(tracks) == 1 else axes.flatten()

    # Remove spacing between tracks.
    fig.subplots_adjust(hspace=0.1)

    # Set xlim to required region.
    if reverse:
        x_end, x_start = start - padding[1], end + padding[0]
    else:
        x_start, x_end = start - padding[0], end + padding[1]

    axes[0].set_xlim(x_start, x_end)

    # Plot tracks.
    for track, ax in zip(tracks, axes):
        track.draw(ax, seqname, start, end)

    # Move x-ticks to the top of the figure if requested.
    if tick_top:
        axes[0].xaxis.tick_top()
        for lab in axes[-1].get_xticklabels():
            lab.set_visible(False)
    else:
        for ax in axes[:-1]:
            for lab in ax.get_xticklabels():
                lab.set_visible(False)

    # Turn off scientific notation on axes.
    axes[0].xaxis.get_major_formatter().set_useOffset(False)
    axes[0].xaxis.get_major_formatter().set_scientific(False)

    if despine:
        # Adjust spines and labels for more white space.
        _despine_axes(axes, tick_top)

    return fig


def _calc_height_ratios(tracks, seqname, start, end, figsize):
    """Calculates height ratios based on heights of given tracks."""

    # Create dummy figure + axes for drawing.
    figsize = _calc_figsize(figsize)
    dummy_fig, dummy_axes = plt.subplots(figsize=figsize, nrows=len(tracks))
    dummy_axes = [dummy_axes] if len(tracks) == 1 else dummy_axes.flatten()

    # Calculate heights of the tracks.
    height_ratios = [t.get_height(ax, seqname, start, end)
                     for t, ax in zip(tracks, dummy_axes)]

    # Close dummy figure to prevent drawing.
    plt.close(dummy_fig)

    return height_ratios


def _calc_figsize(figsize, height_ratios=None):
    """Calculates figsize, optionally taking height_ratios into account."""

    if figsize is None:
        fig_width, fig_height = None, None
    else:
        fig_width, fig_height = figsize

    if fig_height is None:
        if height_ratios is not None:
            fig_height = sum(height_ratios)
        else:
            fig_height = 1

    if fig_width is None:
        fig_width = plt.rcParams['figure.figsize'][0]

    return fig_width, fig_height


def _despine_axes(axes, tick_top):
    """Despines track axes using Seaborn, accounting for tick location."""

    if sns is None:
        raise ImportError('Seaborn library is required for despine')

    sns.despine(ax=axes[0], top=not tick_top, left=True, bottom=True)
    for ax in axes[1:-1]:
        sns.despine(ax=ax, bottom=True, left=True)
    sns.despine(ax=axes[-1], bottom=tick_top, left=True)
