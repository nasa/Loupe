import numpy as np
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator

from src import helper_functions
from src import log_parsing


def autoscale_y(ax, margin=0.1):

    def get_bottom_top(line):
        xd = line.get_xdata()
        yd = line.get_ydata()
        if len(xd) > 1 and len(yd) > 1:
            lo,hi = ax.get_xlim()
            y_displayed = yd[((xd>lo) & (xd<hi))]
            h = np.max(y_displayed) - np.min(y_displayed)
            bot = np.min(y_displayed)-margin*h
            top = np.max(y_displayed)+margin*h
            return bot,top
        else:
            return None, None

    lines = ax.get_lines()
    bot,top = np.inf, -np.inf

    for line in lines:
        new_bot, new_top = get_bottom_top(line)
        if new_bot is not None and new_top is not None:
            if new_bot < bot: bot = new_bot
            if new_top > top: top = new_top

    ax.set_ylim(bot,top)


def get_major_wavenumber_ticks(x_range, laser, wavenum_spacing):
    # list of positions (0,1) on the upper axis for each wavenumber
    wavenumber_label = []
    #list with values of tick mark locations
    wavenumber_location = []
    # the wavenumber values at the extreme ends of the plot
    wn_low = ((10**7)/laser) - ((10**7)/x_range[0])
    wn_high = ((10**7)/laser) - ((10**7)/x_range[1])

    # the number of major ticks
    wavenum_ticks = int(wn_high//wavenum_spacing)

    for loc in range(wavenum_ticks):
        wavenumber_i=int(wn_high - wavenum_spacing*loc)
        wavenumber_i = wavenumber_i - (wavenumber_i%wavenum_spacing)
        if int(wavenumber_i) not in wavenumber_label and wavenumber_i >= wn_low:
            wavenumber_label.append(int(wavenumber_i))
            wvl = 1/((1/laser)-(wavenumber_i/(10**7)))
            #define location as a fraction between [0,1]
            location = (wvl-x_range[0])/(x_range[1]-x_range[0])
            wavenumber_location.append(location)

    return wavenumber_label, wavenumber_location

# wavenum_minor_ticks is the number of minor tick marks between major ticks
def get_minor_wavenumber_ticks(x_range, laser, wavenum_spacing, wavenumber_location, wavenumber_label, wavenum_minor_ticks=3):
    #list with values of minor tick mark locations (0,1)
    minor_locator = []
    wn_low = ((10**7)/laser) - ((10**7)/x_range[0])
    wn_high = ((10**7)/laser) - ((10**7)/x_range[1])

    #places minor ticks between major ticks
    for i in range(len(wavenumber_location)-1):
        wavenumber_i = wavenumber_label[i+1]
        for j in range(wavenum_minor_ticks):
            wavenumber_j = wavenumber_i+((j+1)*wavenum_spacing/(wavenum_minor_ticks+1))
            # convert wavenumber_j to wavelength
            wavelength_j = helper_functions.shift_to_wavelength([wavenumber_j])[0]
            # find axis location for wavelength (between 0-1)
            minor_pos = (wavelength_j-x_range[0])/(x_range[1]-x_range[0])
            minor_locator.append(minor_pos)

    # add first minor ticks
    # the wavenumber location for the 0th wavenumber major label (this is off the left side of the plot)
    wavenumber_i = int(wn_low) - (int(wn_low)%wavenum_spacing)
    for j in range(wavenum_minor_ticks):
        wavenumber_j = wavenumber_i+((j+1)*wavenum_spacing/(wavenum_minor_ticks+1))
        # convert wavenumber_j to wavelength
        wavelength_j = helper_functions.shift_to_wavelength([wavenumber_j])[0]
        # find axis location for wavelength
        minor_pos = (wavelength_j-x_range[0])/(x_range[1]-x_range[0])
        if minor_pos > 0:
            minor_locator.append(minor_pos)

    # add last minor ticks
    # the wavenumber location for the n+1 wavenumber major label (this is off the right side of the plot)
    wavenumber_i = (int(wn_high) - (int(wn_high)%wavenum_spacing))+wavenum_spacing
    for j in range(wavenum_minor_ticks):
        wavenumber_j = wavenumber_i-((j+1)*wavenum_spacing/(wavenum_minor_ticks+1))
        # convert wavenumber_j to wavelength
        wavelength_j = helper_functions.shift_to_wavelength([wavenumber_j])[0]
        # find axis location for wavelength
        minor_pos = (wavelength_j-x_range[0])/(x_range[1]-x_range[0])
        if minor_pos < 1:
            minor_locator.append(minor_pos)

    return minor_locator

def formatWavelengthWavenumber(view, x, x1_title = 'Wavelength (nm)', x2_title = 'Raman shift (cm$^{-1}$)', y_title = '', x_range = [50, 2098], y_range=False, laser=248.5794, wavenum_spacing = 1000, wavenum_minor_ticks = 3):
    ax = view.traceCanvasMainPlot1.axes
    ax.grid(b=True, which='major', linestyle='--')
    ax.set_ylabel(y_title, fontsize=10)
    ax.set_xlabel(x1_title, fontsize=10)

    if x_range:
        ax.set_xlim(left=x_range[0], right=x_range[1])
    if y_range:
        ax.set_ylim(bottom=y_range[0], top=y_range[1])

    ax.xaxis.set_minor_locator(AutoMinorLocator(4))

    # plot wavenumber on top axis
    ax_top = ax.twiny()
    x_range_get = ax.get_xlim()
    x_range_wvl = [x[int(x_range_get[0])], x[int(x_range_get[1])]]

    wavenumber_label, wavenumber_location = get_major_wavenumber_ticks(x_range_wvl, laser, wavenum_spacing)
    minor_locator = get_minor_wavenumber_ticks(x_range_wvl, laser, wavenum_spacing, wavenumber_location, wavenumber_label, wavenum_minor_ticks=wavenum_minor_ticks)

    ax_top.set_xticks(wavenumber_location)
    ax_top.set_xticklabels(wavenumber_label)
    ax_top.xaxis.set_minor_locator(plt.FixedLocator(minor_locator))

    ax_top.set_xlabel(x2_title, fontsize=10)

    def format_x_coord(x):
        x_wvl = x*(x_range_wvl[1]-x_range_wvl[0])+x_range_wvl[0]
        x_wvn = helper_functions.wavelength_to_shift([x_wvl], laser=laser)[0]
        return '{0:.2f} nm, {1:.2f} cm\u207B\u00B9, '.format(x_wvl, x_wvn)

    ax_top.axes.fmt_xdata = format_x_coord
    ax_top.axes.fmt_ydata = lambda y: '{0:.2f}'.format(y)

    if x_range:
        view.traceCanvasMainPlot1.axes.set_xlim(left = x[int(x_range_get[0])], right=x[int(x_range_get[1])])
        autoscale_y(view.traceCanvasMainPlot1.axes, margin=0.1)

    return ax, ax_top


def formatCCDPixelCosmic(view, x, x1_title = 'CCD Pixel', x2_title = '', y_title = '', x_range = [50, 2098], y_range=False):
    ax = view.traceCanvasCosmicPlot2.axes
    ax.grid(b=True, which='major', linestyle='--')
    ax.set_ylabel(y_title, fontsize=10)
    ax.set_xlabel(x1_title, fontsize=10)

    if x_range:
        ax.set_xlim(left=x_range[0], right=x_range[1])
    if y_range:
        ax.set_ylim(bottom=y_range[0], top=y_range[1])

    ax.xaxis.set_minor_locator(AutoMinorLocator(4))

    ax_top = ax.twiny()
    x_range_get = ax.get_xlim()
    x_range_pix = [x[int(x_range_get[0])], x[int(x_range_get[1])]]

    ax_top.set_xlabel(x2_title, fontsize=10)

    for t in ax_top.get_xticklabels():
        t.set_alpha(0.0)
    ax_top.tick_params(axis='x', length=0)

    def format_x_coord_pix(x):
        x_pix = x*(x_range_pix[1]-x_range_pix[0])+x_range_pix[0]
        return '{0:.2f} pixel, '.format(x_pix)

    ax_top.axes.fmt_xdata = format_x_coord_pix
    ax_top.axes.fmt_ydata = lambda y: '{0:.2f}'.format(y)

    if x_range:
        view.traceCanvasCosmicPlot2.axes.set_xlim(left = x[int(x_range_get[0])], right=x[int(x_range_get[1])])
        autoscale_y(view.traceCanvasCosmicPlot2.axes, margin=0.1)

    return ax, ax_top



def formatWavelengthWavenumberCosmic(view, x, x1_title = 'Wavelength (nm)', x2_title = 'Raman shift (cm$^{-1}$)', y_title = '', x_range_channel = [50, 2098], x_range = False, y_range=False, laser=248.5794, wavenum_spacing = 1000, wavenum_minor_ticks = 3):
    ax = view.traceCanvasCosmicPlot2.axes
    ax.grid(b=True, which='major', linestyle='--')
    ax.set_ylabel(y_title, fontsize=10)
    ax.set_xlabel(x1_title, fontsize=10)

    if x_range:
        ax.set_xlim(left = x_range[0], right=x_range[1])
        ax.xaxis.set_minor_locator(AutoMinorLocator(4))
        # plot wavenumber on top axis
        ax_top = ax.twiny()
        x_range_wvl = [x_range[0], x_range[1]]
    elif x_range_channel:
        ax.set_xlim(left=x_range_channel[0], right=x_range_channel[1])
        ax.xaxis.set_minor_locator(AutoMinorLocator(4))
        # plot wavenumber on top axis
        ax_top = ax.twiny()
        x_range_get = ax.get_xlim()
        x_range_wvl = [x[int(x_range_get[0])], x[int(x_range_get[1])]]

    wavenumber_label, wavenumber_location = get_major_wavenumber_ticks(x_range_wvl, laser, wavenum_spacing)
    minor_locator = get_minor_wavenumber_ticks(x_range_wvl, laser, wavenum_spacing, wavenumber_location, wavenumber_label, wavenum_minor_ticks=wavenum_minor_ticks)

    ax_top.set_xticks(wavenumber_location)
    ax_top.set_xticklabels(wavenumber_label)
    ax_top.xaxis.set_minor_locator(plt.FixedLocator(minor_locator))

    ax_top.set_xlabel(x2_title, fontsize=10)

    def format_x_coord(x):
        x_wvl = x*(x_range_wvl[1]-x_range_wvl[0])+x_range_wvl[0]
        x_wvn = helper_functions.wavelength_to_shift([x_wvl], laser=laser)[0]
        return '{0:.2f} nm, {1:.2f} cm\u207B\u00B9, '.format(x_wvl, x_wvn)

    ax_top.axes.fmt_xdata = format_x_coord
    ax_top.axes.fmt_ydata = lambda y: '{0:.2f}'.format(y)

    if y_range:
        ax.set_ylim(bottom = y_range[0], top=y_range[1])
        view.traceCanvasCosmicPlot2.axes.set_ylim(bottom = y_range[0], top=y_range[1])
    if x_range:
        ax.set_xlim(left = x_range[0], right=x_range[1])
        view.traceCanvasCosmicPlot2.axes.set_xlim(left = x_range[0], right=x_range[1])
    elif x_range_channel:
        view.traceCanvasCosmicPlot2.axes.set_xlim(left = x[int(x_range_get[0])], right=x[int(x_range_get[1])])
        autoscale_y(view.traceCanvasCosmicPlot2.axes, margin=0.1)

    return ax, ax_top


def formatWavelengthWavenumberMap(view, x, x1_title = 'Wavelength (nm)', x2_title = 'Raman shift (cm$^{-1}$)', y_title = '', x_range = [50, 2098], y_range=False, laser=248.5794, wavenum_spacing = 1000, wavenum_minor_ticks = 3):
    ax = view.traceCanvasMapPlot2.axes
    ax.grid(b=True, which='major', linestyle='--')
    ax.set_ylabel(y_title, fontsize=10)
    ax.set_xlabel(x1_title, fontsize=10)

    if x_range:
        ax.set_xlim(left=x_range[0], right=x_range[1])
    if y_range:
        ax.set_ylim(bottom=y_range[0], top=y_range[1])

    ax.xaxis.set_minor_locator(AutoMinorLocator(4))

    # plot wavenumber on top axis
    ax_top = ax.twiny()
    x_range_get = ax.get_xlim()
    x_range_wvl = [x[int(x_range_get[0])], x[int(x_range_get[1])]]

    wavenumber_label, wavenumber_location = get_major_wavenumber_ticks(x_range_wvl, laser, wavenum_spacing)
    minor_locator = get_minor_wavenumber_ticks(x_range_wvl, laser, wavenum_spacing, wavenumber_location, wavenumber_label, wavenum_minor_ticks=wavenum_minor_ticks)

    ax_top.set_xticks(wavenumber_location)
    ax_top.set_xticklabels(wavenumber_label)
    ax_top.xaxis.set_minor_locator(plt.FixedLocator(minor_locator))

    ax_top.set_xlabel(x2_title, fontsize=10)

    def format_x_coord(x):
        x_wvl = x#*(x_range_wvl[1]-x_range_wvl[0])+x_range_wvl[0]
        x_wvn = helper_functions.wavelength_to_shift([x_wvl], laser=laser)[0]
        return '{0:.2f} nm, {1:.2f} cm\u207B\u00B9, '.format(x_wvl, x_wvn)

    #ax_top.axes.fmt_xdata = format_x_coord
    #ax_top.axes.fmt_ydata = lambda y: '{0:.2f}'.format(y)

    if x_range:
        view.traceCanvasMapPlot2.axes.set_xlim(left = x[int(x_range_get[0])], right=x[int(x_range_get[1])])
        try:
            autoscale_y(view.traceCanvasMapPlot2.axes, margin=0.1)
        except:
            log_parsing.log_info(view, 'could not autoscale RGB tab - spectrum not yet drawn')

    # required for event handling (click + drag with upper axis)
    ax_top_top = ax.twiny()
    ax_top_top.set_xbound(ax.get_xbound())
    ax_top_top.set_xticks([])
    ax_top_top.set_xticklabels([])
    ax_top_top.xaxis.set_minor_locator(plt.FixedLocator([]))
    ax_top_top.set_xlabel('', fontsize=10)

    ax_top_top.axes.fmt_xdata = format_x_coord
    ax_top_top.axes.fmt_ydata = lambda y: '{0:.2f}'.format(y)

    return ax, ax_top, ax_top_top

def formatCCDPixel(view, x, x1_title = 'CCD Pixel', x2_title = '', y_title = '', x_range = [50, 2098], y_range=False):
    ax = view.traceCanvasMainPlot1.axes
    ax.grid(b=True, which='major', linestyle='--')
    ax.set_ylabel(y_title, fontsize=10)
    ax.set_xlabel(x1_title, fontsize=10)

    if x_range:
        ax.set_xlim(left=x_range[0], right=x_range[1])
    if y_range:
        ax.set_ylim(bottom=y_range[0], top=y_range[1])

    ax.xaxis.set_minor_locator(AutoMinorLocator(4))

    ax_top = ax.twiny()
    x_range_get = ax.get_xlim()
    x_range_pix = [x[int(x_range_get[0])], x[int(x_range_get[1])]]

    ax_top.set_xlabel(x2_title, fontsize=10)

    for t in ax_top.get_xticklabels():
        t.set_alpha(0.0)
    ax_top.tick_params(axis='x', length=0)

    def format_x_coord_pix(x):
        x_pix = x*(x_range_pix[1]-x_range_pix[0])+x_range_pix[0]
        return '{0:.2f} pixel, '.format(x_pix)

    ax_top.axes.fmt_xdata = format_x_coord_pix
    ax_top.axes.fmt_ydata = lambda y: '{0:.2f}'.format(y)

    if x_range:
        view.traceCanvasMainPlot1.axes.set_xlim(left = x[int(x_range_get[0])], right=x[int(x_range_get[1])])
        autoscale_y(view.traceCanvasMainPlot1.axes, margin=0.1)

    return ax, ax_top



def formatSparWavelengthWavenumber(view, x, x1_title = 'Wavelength (nm)', x2_title = 'Raman shift (cm$^{-1}$)', y_title = '', x_range_channel = [50, 2098], x_range = False, y_range=False, laser=248.5794, wavenum_spacing = 1000, wavenum_minor_ticks = 3):
    ax = view.traceCanvasMainPlot2.axes
    ax.grid(b=True, which='major', linestyle='--')
    ax.set_ylabel(y_title, fontsize=10)
    ax.set_xlabel(x1_title, fontsize=10)

    if x_range:
        ax.set_xlim(left = x_range[0], right=x_range[1])
        ax.xaxis.set_minor_locator(AutoMinorLocator(4))
        # plot wavenumber on top axis
        ax_top = ax.twiny()
        x_range_wvl = [x_range[0], x_range[1]]
    elif x_range_channel:
        ax.set_xlim(left=x_range_channel[0], right=x_range_channel[1])
        ax.xaxis.set_minor_locator(AutoMinorLocator(4))
        # plot wavenumber on top axis
        ax_top = ax.twiny()
        x_range_get = ax.get_xlim()
        x_range_wvl = [x[int(x_range_get[0])], x[int(x_range_get[1])]]

    wavenumber_label, wavenumber_location = get_major_wavenumber_ticks(x_range_wvl, laser, wavenum_spacing)
    minor_locator = get_minor_wavenumber_ticks(x_range_wvl, laser, wavenum_spacing, wavenumber_location, wavenumber_label, wavenum_minor_ticks=wavenum_minor_ticks)

    ax_top.set_xticks(wavenumber_location)
    ax_top.set_xticklabels(wavenumber_label)
    ax_top.xaxis.set_minor_locator(plt.FixedLocator(minor_locator))

    ax_top.set_xlabel(x2_title, fontsize=10)

    def format_x_coord(x):
        x_wvl = x*(x_range_wvl[1]-x_range_wvl[0])+x_range_wvl[0]
        x_wvn = helper_functions.wavelength_to_shift([x_wvl], laser=laser)[0]
        return '{0:.2f} nm, {1:.2f} cm\u207B\u00B9,'.format(x_wvl, x_wvn)

    ax_top.axes.fmt_xdata = format_x_coord
    ax_top.axes.fmt_ydata = lambda y: '{0:.2f}'.format(y)

    if y_range:
        ax.set_ylim(bottom = y_range[0], top=y_range[1])
        view.traceCanvasMainPlot2.axes.set_ylim(bottom = y_range[0], top=y_range[1])
    if x_range:
        ax.set_xlim(left = x_range[0], right=x_range[1])
        view.traceCanvasMainPlot2.axes.set_xlim(left = x_range[0], right=x_range[1])
    elif x_range_channel:
        view.traceCanvasMainPlot2.axes.set_xlim(left = x[int(x_range_get[0])], right=x[int(x_range_get[1])])
        autoscale_y(view.traceCanvasMainPlot2.axes, margin=0.1)

    return ax, ax_top

def formatSparCCDPixel(view, x, x1_title = 'CCD Pixel', x2_title = '', y_title = '', x_range = [50, 2098], y_range=False):
    ax = view.traceCanvasMainPlot2.axes
    ax.grid(b=True, which='major', linestyle='--')
    ax.set_ylabel(y_title, fontsize=10)
    ax.set_xlabel(x1_title, fontsize=10)

    if x_range:
        ax.set_xlim(left=x_range[0], right=x_range[1])
    if y_range:
        ax.set_ylim(bottom=y_range[0], top=y_range[1])

    ax.xaxis.set_minor_locator(AutoMinorLocator(4))

    ax_top = ax.twiny()
    x_range_get = ax.get_xlim()
    ax_top.set_xlabel(x2_title, fontsize=10)

    def format_x_coord(x):
        return '{0:.2f} pixel,'.format(x)

    ax_top.axes.fmt_xdata = format_x_coord
    ax_top.axes.fmt_ydata = lambda y: '{0:.2f}'.format(y)

    if x_range:
        view.traceCanvasMainPlot2.axes.set_xlim(left = x[int(x_range_get[0])], right=x[int(x_range_get[1])])
        autoscale_y(view.traceCanvasMainPlot2.axes, margin=0.1)

    return ax, ax_top


def formatSparReset(view):
    ax = view.traceCanvasMainPlot2.axes
    plot = ax.plot([0], [0])
    ax.grid(b=True, which='major', linestyle='--')
    ax.set_ylabel('', fontsize=10)
    ax.set_xlabel('', fontsize=10)

    # plot nothing on top axis
    ax_top = ax.twiny()

    ax_top.set_xticks([])
    ax_top.set_xticklabels([])
    ax_top.xaxis.set_minor_locator(plt.FixedLocator([]))

    ax_top.set_xlabel('', fontsize=10)

    return ax

def plot_single(ax, x, y, color='k', alpha=1.0, label='', std = None):
    plot = ax.plot(x, y, color=color, linewidth=1, alpha=alpha, label=label)
    if std is not None:
        plot = ax.fill_between(x, y, y+std, color=color, alpha=alpha/2.0, label='_'+label)
        plot = ax.fill_between(x, y, y-std, color=color, alpha=alpha/2.0, label='_'+label)
    return ax

def plot_single_spar(ax, x, y, color='k', alpha=1.0, label='', x_range=False, y_range=False):
    plot = ax.plot(x, y, color=color, linewidth=1, alpha=alpha, label=label)[0]
    if x_range:
        ax.set_xlim(left = x_range[0], right = x_range[1])
    if y_range:
        ax.set_ylim(bottom = y_range[0], top = y_range[1])
    return plot


def plotMainTrace(view, x1, y, color, alpha=0.5, label='', std = None):
    axes = view.traceCanvasMainPlot1.axes
    ax = plot_single(axes, x1, y, color=color, alpha=alpha, label=label, std = std)
    return ax

def plotCosmicTrace(view, x1, y, color, alpha=0.5, label='', std = None):
    axes = view.traceCanvasCosmicPlot2.axes
    ax = plot_single(axes, x1, y, color=color, alpha=alpha, label=label, std = std)
    return ax

def plotCosmicHist(view, hist, edges, color, alpha=0.5, label='', threshold=None):
    axes = view.traceCanvasCosmicPlot1.axes
    ax = plot_hist(axes, (hist, edges), color=color, alpha=alpha, label=label, fill=False, threshold=threshold)
    return ax

def plotCosmicFill(ax, x1, x2, color, alpha=0.5, label=''):
    plot = ax.axvspan(x1, x2, alpha=alpha, color=color, label=label)
    return ax

def plotMainSingleTrace(view, x1, y, color, alpha=0.5, label='', x_range=False, y_range=False):
    axes = view.traceCanvasMainPlot2.axes
    ax = plot_single_spar(axes, x1, y, color=color, alpha=alpha, label=label, x_range=x_range, y_range=y_range)
    #axes.grid(b=True, which='major', linestyle='--')
    return ax

def plotCosmicSingleTrace(view, x1, y, color, alpha=0.5, label='', x_range=False, y_range=False):
    axes = view.traceCanvasCosmicPlot2.axes
    ax = plot_single_spar(axes, x1, y, color=color, alpha=alpha, label=label, x_range=x_range, y_range=y_range)
    return ax


def plotMapTrace(view, x1, y, color, alpha=0.5, label='', std = None):
    axes = view.traceCanvasMapPlot2.axes
    ax = plot_single(axes, x1, y, color=color, alpha=alpha, label=label, std = std)
    return ax

def plotTrace(axes, x1, y, color, alpha=0.5, label=''):
    ax = plot_single(axes, x1, y, color=color, alpha=alpha, label=label)
    axes.grid(b=True, which='major', linestyle='--')
    return ax


def plot_hist(ax, hist, color='w', alpha=1.0, label='', fill=True, threshold=None):
    hist_vals, edges = hist
    left,right = edges[:-1],edges[1:]
    X = np.array([left,right]).T.flatten()
    Y = np.array([hist_vals, hist_vals]).T.flatten()
    plot = ax.plot(X, Y, color=color, alpha = alpha, label=label)
    if fill:
        ax.fill_between(X, 0, Y, color=color, alpha=alpha, label=label)
    if threshold is not None:
        ax.fill_between([threshold, threshold+1], 0, ax.get_ylim()[1], color='c', alpha=0.5, label=label+'_threshold')
    return plot

def plotRGBHistogram(axes, hist, color, alpha=0.8, label='_redHist'):
    ax = plot_hist(axes, hist, color=color, alpha=alpha, label=label)
    return ax
