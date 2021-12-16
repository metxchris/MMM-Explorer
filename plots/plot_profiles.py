# Standard Packages
from dataclasses import dataclass
import copy
import sys
sys.path.insert(0, '../')

# 3rd Party Packages
import numpy as np
import matplotlib.pyplot as plt

# Local Packages
from main import constants, utils, calculations
from main.enums import ProfileType, ShotType
from main.options import Options
from plots.styles import standard as ps
import settings


# Subplot row and column counts
ROWS, COLS = ps.ROWS, ps.COLS


@dataclass
class PlotData:
    '''
    Stores data that will be sent to the plotting loop

    Members:
    * title (str): The title of the subplot
    * xvar (Variable): The Variable object containing data for the x-axis of all yvars
    * yvars (list of Variable): List of Variable objects containing data for the y-axis
    '''

    title: str
    xvar: object
    yvars: list


def init_figure(profile_type, xvar_points):
    '''
    Initializes a new figure and figure subplots

    Parameters:
    * profile_type (ProfileType): The type of profiles being plotted
    * xvar_points (int): The number of points the xvar being plotted has
    '''

    runid = Options.instance.runid
    shot_type = Options.instance.shot_type
    time = Options.instance.time_str
    points = xvar_points

    # Init figure and subplots
    fig, axs = plt.subplots(ROWS, COLS)

    # Set figure title and subtitle
    modifier = 'Smoothed' if Options.instance.apply_smoothing else 'Unsmoothed'
    title_txt = f'MMM {profile_type.name.capitalize()} Profiles Using {modifier} Input Profiles'
    subtitle_txt = f'{shot_type.name} Shot {runid}, Measurement Time {time}s, {points} Radial Points'
    plt.figtext(*ps.TITLEPOS, title_txt, fontsize=15, ha='center')
    plt.figtext(*ps.SUBTITLEPOS, subtitle_txt, fontsize=10, ha='center')

    return fig, axs


def make_plot(ax, data, profile_type, time_idx=None):
    '''
    Creates one individual plot on the specified axis

    Parameters:
    * data (PlotData): The data to be plotted
    * profile_type (ProfileType): The type of profile being plotted
    * time_idx (int): The index of the time value being plotted (Optional)
    '''

    xvals = data.xvar.values if time_idx is None else data.xvar.values[:, time_idx]

    for i, yvar in enumerate(data.yvars):
        yvals = yvar.values if time_idx is None else yvar.values[:, time_idx]
        ax.plot(xvals, yvals, label=yvar.label)

    ax.set(title=data.title, xlabel=data.xvar.label, ylabel=data.yvars[0].units_label, xlim=(xvals.min(), xvals.max()))
    ax.axis('on')

    # Check for ylim adjustment (needed when y-values are nearly constant and not nearly 0)
    ymax, ymin = yvals.max(), yvals.min()
    if round(ymax - ymin, 3) == 0 and round(ymax, 3) > 0:
        ax.set(ylim=(ymin - 5, ymax + 5))

    # Legend disabled for output type profiles
    if profile_type != ProfileType.OUTPUT:
        ax.legend()


def run_plotting_loop(plotdata, profile_type):
    '''
    Runs a loop to create figures and plots for each PlotData object in plotdata

    Parameters:
    * plotdata (list of PlotData): Contains all data being plotted
    * profile_type (ProfileType): The type of profiles being plotted
    '''

    from plots.styles import standard as ps
    from plots.colors import mmm

    opts = Options.instance

    print(f'Creating {profile_type.name.lower()} profile figures...')

    for i, data in enumerate(plotdata):

        # Logic to count (row, col) by col first, then by row; (0, 0), (0, 1), (0, 2), (1, 0), etc.
        row = int(i / COLS) % ROWS
        col = i % COLS

        # Create a new figure when we're on the first subplot
        if row == 0 and col == 0:
            fig, axs = init_figure(profile_type, data.xvar.values.shape[0])

            # Disable all subplot axes until they are used
            for sub_axs in axs:
                for ax in sub_axs:
                    ax.axis('off')

        # Create subplot and enable axis.  Setting data to None will leave the subplot position empty
        if data is not None:
            if profile_type in [ProfileType.INPUT, ProfileType.COMPARED, ProfileType.ADDITIONAL]:
                make_plot(axs[row, col], data, profile_type, opts.time_idx)
            elif profile_type == ProfileType.OUTPUT:
                make_plot(axs[row, col], data, profile_type)

        # Figure is full of subplots, so save the sheet
        if (i + 1) % (ROWS * COLS) == 0:
            fig.savefig(utils.get_temp_path(f'{profile_type.name.lower()}_profiles_{int((i + 1) / 6)}.pdf'))

    # Save any remaining subplots to one final sheet
    if (i + 1) % (ROWS * COLS) != 0:
        fig.savefig(utils.get_temp_path(f'{profile_type.name.lower()}_profiles_{int((i + 1) / 6) + 1}.pdf'))

    merged_pdf = utils.merge_profile_sheets(opts.runid, opts.scan_num, profile_type.name.capitalize())

    # File opening may only work on Windows
    if settings.AUTO_OPEN_PDFS:
        utils.open_file(merged_pdf)

    # Clear plots from memory
    plt.close('all')


def get_compared_data(mmm_vars, cdf_vars):
    '''
    Gets plotdata for comparisons of calculated values with values found in the CDF

    Use these Options for the most accurate comparison when verifying calculations against CDF variables:
    * Options.instance.apply_smoothing = False
    * Options.instance.input_points = None

    Parameters:
    * cdf_vars (InputVariables): All CDF variables
    * mmm_vars (InputVariables): All calculated variables to be used as MMM input
    '''

    # Set compare_list, a list of variables that were both calculated in calculations.py and found in the CDF
    calculated_vars_list = calculations.get_calculated_vars()
    cdf_var_list = cdf_vars.get_cdf_variables()
    compare_list = [var for var in calculated_vars_list if var in cdf_var_list]

    plotdata = []

    # Automatically build plotdata list with variables that we want to compare
    for var_name in compare_list:

        # Make deep copies since we are modifying the labels below
        cdf_var = copy.deepcopy(getattr(cdf_vars, var_name))
        calc_var = copy.deepcopy(getattr(mmm_vars, var_name))

        # Skip this variable if there are any issues
        if cdf_var.values is None or cdf_var.values.ndim != calc_var.values.ndim:
            continue

        cdf_var.label += f' ({cdf_var.cdfvar})'
        calc_var.label += ' (MMM)'

        plotdata.append(PlotData(cdf_var.name, mmm_vars.rho, [cdf_var, calc_var]))

    return plotdata


def plot_profiles(profile_type, vars, cdf_vars=None):
    '''
    Sets the plotdata (list of PlotData) to be plotted, then runs the plotting loop

    Setting None as a list item in plotdata will leave the associated subplot for that item empty.  For example,
    items can be set to None to force a group of related PlotData to be plotted together on a new figure.

    Parameters:
    * vars (InputVariables or OutputVariables): The object containing variable data to plot
    * profile_type (ProfileType): The type of profiles to plot
    '''

    if profile_type == ProfileType.INPUT:
        plotdata = [
            PlotData('Temperatures', vars.rho, [vars.te, vars.ti]),
            PlotData(vars.q.name, vars.rho, [vars.q]),
            PlotData(vars.wexbs.name, vars.rho, [vars.wexbs]),
            PlotData(r'Temperature Gradients', vars.rho, [vars.gte, vars.gti]),
            PlotData(vars.gq.name, vars.rho, [vars.gq]),
            PlotData(vars.btor.name, vars.rho, [vars.btor]),
            PlotData('Densities', vars.rho, [vars.ne, vars.ni, vars.nf, vars.nd]),
            PlotData(vars.nz.name, vars.rho, [vars.nz]),
            PlotData(vars.nh.name, vars.rho, [vars.nh]),
            PlotData('Density Gradients', vars.rho, [vars.gne, vars.gni]),
            PlotData(vars.gnz.name, vars.rho, [vars.gnz]),
            PlotData(vars.gnh.name, vars.rho, [vars.gnh]),
            PlotData(vars.vpol.name, vars.rho, [vars.vpol]),
            PlotData(vars.vtor.name, vars.rho, [vars.vtor]),
            PlotData(vars.vpar.name, vars.rho, [vars.vpar]),
            PlotData(vars.gvpol.name, vars.rho, [vars.gvpol]),
            PlotData(vars.gvtor.name, vars.rho, [vars.gvtor]),
            PlotData(vars.gvpar.name, vars.rho, [vars.gvpar]),
            PlotData(vars.aimp.name, vars.rho, [vars.aimp]),
            PlotData(vars.aimass.name, vars.rho, [vars.aimass]),
            PlotData(vars.ahyd.name, vars.rho, [vars.ahyd]),
            PlotData(vars.zimp.name, vars.rho, [vars.zimp]),
            PlotData(vars.zeff.name, vars.rho, [vars.zeff]),
            PlotData(vars.elong.name, vars.rho, [vars.elong]),
            PlotData(vars.rmaj.name, vars.rho, [vars.rmaj])]

    elif profile_type == ProfileType.ADDITIONAL:
        plotdata = [
            PlotData(vars.tau.name, vars.rho, [vars.tau]),
            PlotData(vars.beta.name, vars.rho, [vars.beta, vars.betae]),
            PlotData('Gradient Ratios', vars.rho, [vars.etae, vars.etai]),
            PlotData(vars.nuei.name, vars.rho, [vars.nuei]),
            PlotData('Collisionalities', vars.rho, [vars.nuste, vars.nusti]),
            PlotData('Magnetic Shear', vars.rho, [vars.shear, vars.shat]),
            PlotData(vars.alphamhd.name, vars.rho, [vars.alphamhd]),
            PlotData(vars.gave.name, vars.rho, [vars.gave]),
            PlotData(vars.gmax.name, vars.rho, [vars.gmax]),
            PlotData(vars.gyrfi.name, vars.rho, [vars.gyrfi]),
            PlotData(vars.vthe.name, vars.rho, [vars.vthe]),
            PlotData(vars.vthi.name, vars.rho, [vars.vthi])]

    elif profile_type == ProfileType.OUTPUT:
        plotdata = [
            PlotData(vars.xti.name, vars.rho, [vars.xti]),
            PlotData(vars.xdi.name, vars.rho, [vars.xdi]),
            PlotData(vars.xte.name, vars.rho, [vars.xte]),
            PlotData(vars.xdz.name, vars.rho, [vars.xdz]),
            PlotData(vars.xvt.name, vars.rho, [vars.xvt]),
            PlotData(vars.xvp.name, vars.rho, [vars.xvp]),
            PlotData(vars.xtiW20.name, vars.rho, [vars.xtiW20]),
            PlotData(vars.xdiW20.name, vars.rho, [vars.xdiW20]),
            PlotData(vars.xteW20.name, vars.rho, [vars.xteW20]),
            PlotData(vars.xtiDBM.name, vars.rho, [vars.xtiDBM]),
            PlotData(vars.xdiDBM.name, vars.rho, [vars.xdiDBM]),
            PlotData(vars.xteDBM.name, vars.rho, [vars.xteDBM]),
            PlotData(vars.xteETG.name, vars.rho, [vars.xteETG]),
            PlotData(vars.xteMTM.name, vars.rho, [vars.xteMTM]),
            PlotData(vars.xteETGM.name, vars.rho, [vars.xteETGM]),
            PlotData(vars.xdiETGM.name, vars.rho, [vars.xdiETGM]),
            PlotData(vars.gmaW20ii.name, vars.rho, [vars.gmaW20ii]),
            PlotData(vars.gmaW20ie.name, vars.rho, [vars.gmaW20ie]),
            PlotData(vars.gmaW20ei.name, vars.rho, [vars.gmaW20ei]),
            PlotData(vars.gmaW20ee.name, vars.rho, [vars.gmaW20ee]),
            PlotData(vars.omgW20ii.name, vars.rho, [vars.omgW20ii]),
            PlotData(vars.omgW20ie.name, vars.rho, [vars.omgW20ie]),
            PlotData(vars.omgW20ei.name, vars.rho, [vars.omgW20ei]),
            PlotData(vars.omgW20ee.name, vars.rho, [vars.omgW20ee]),
            PlotData(vars.gmaDBM.name, vars.rho, [vars.gmaDBM]),
            PlotData(vars.omgDBM.name, vars.rho, [vars.omgDBM]),
            PlotData(vars.gmaMTM.name, vars.rho, [vars.gmaMTM]),
            PlotData(vars.omgMTM.name, vars.rho, [vars.omgMTM]),
            PlotData(vars.gmaETGM.name, vars.rho, [vars.gmaETGM]),
            PlotData(vars.omgETGM.name, vars.rho, [vars.omgETGM]),
            PlotData(vars.dbsqprf.name, vars.rho, [vars.dbsqprf])]

    else:
        raise TypeError(f'The ProfileType {profile_type} does not have a plotdata definition')

    run_plotting_loop(plotdata, profile_type)


def plot_profile_comparison(cdf_vars, mmm_vars):
    '''
    Compares profiles of calculated values with values found in the CDF

    Use these Options for the most accurate comparison when verifying calculations against CDF variables:
    * Options.instance.apply_smoothing = False
    * Options.instance.input_points = None

    Parameters:
    * cdf_vars (InputVariables): All CDF variables
    * mmm_vars (InputVariables): All calculated variables to be used as MMM input
    '''

    # Set compare_list, a list of variables that were both calculated in calculations.py and found in the CDF
    calculated_vars_list = calculations.get_calculated_vars()
    cdf_var_list = cdf_vars.get_cdf_variables()
    compare_list = [var for var in calculated_vars_list if var in cdf_var_list]

    plotdata = []

    # Automatically build plotdata list with variables that we want to compare
    for var_name in compare_list:

        # Make deep copies since we are modifying the labels below
        cdf_var = copy.deepcopy(getattr(cdf_vars, var_name))
        calc_var = copy.deepcopy(getattr(mmm_vars, var_name))

        # Skip this variable if there are any issues
        if cdf_var.values is None or cdf_var.values.ndim != calc_var.values.ndim:
            continue

        cdf_var.label += f' ({cdf_var.cdfvar})'
        calc_var.label += ' (MMM)'

        plotdata.append(PlotData(cdf_var.name, mmm_vars.rho, [cdf_var, calc_var]))

    run_plotting_loop(plotdata, ProfileType.COMPARED)


if __name__ == '__main__':
    # For testing purposes
    print(plt.rcParams.keys())
