"""Handles values of controls used in the header of the MMM input file

A control is any value in the MMM input file that is not dependent on rmin,
the minor radius of the plasma.  Controls are generally used for switches or
scalar coefficients by MMM.  Some controls may also be scanned over, such as
kyrhoe in any of the component models. The InputControls class stores all
control values needed by MMM, and also handles generating the header of the
MMM input file, as used by the MMM wrapper.

The InputControls class is coupled with the Options class, which is used for
storing options needed for plotting, checking values, and both saving and
loading control data.  An Options object must be instantiated and passed in
when instantiating InputControls objects.  When loading control data from
CSVs, it is advised to load the options data first, and then use the loaded
options to load the controls.

Example Usage:
    # Instantiate Options for New InputControls
    options = modules.options.Options(
        runid='132017T01',
        shot_type=ShotType.NSTX,
        input_points=101,
    )

    # Instantiate InputControls and Set Values
    controls = InputControls(
        options,
        input_points=101,
        cmodel_weiland=1,
        cmodel_dribm=0,
        cmodel_etg=0,
    )

    # Get MMM Header
    controls.get_mmm_header()

    # Load Options for Loading InputControls
    options = modules.options.Options()
    options.load(runid='132017T01', scan_num=1)

    # Load Controls
    controls = InputControls(options)
    controls.load_from_csv()

    # Save Controls
    controls.save()
"""

# Standard Packages
import sys; sys.path.insert(0, '../')
import logging

# 3rd Party Packages
import numpy as np

# Local Packages
import modules.utils as utils
import modules.constants as constants
from modules.enums import SaveType


_log = logging.getLogger(__name__)


class InputControls:
    '''
    Input Controls for the MMM input file

    Please refer to the documentation for MMM for more information about the
    various controls used here.

    Notes:
    * Controls defined here are will be placed into the header of the MMM input file
    * Controls with vtype=int are expected as Fortran Integer types in the input file
    * Controls with vtype=float are expected as Fortran Real types in the input file
    * The value defined in each Control object is the default value of that control

    Raises:
    * ValueError: If keyword arguments (kwargs) are provided on init and options are not
    '''

    def __init__(self, options=None, **kwargs):
        if kwargs and not options:
            # options is only allowed to be None when instantiating the class solely for membership checks
            raise ValueError('options must be provided when providing keyword arguments')

        self.input_points = Control('Number of radial points', int, None)
        # Switches for component models
        self.cmodel_weiland = Control('Weiland', float, 1)
        self.cmodel_dribm = Control('DRIBM', float, 1)
        self.cmodel_etg = Control('ETG', float, 1)
        self.cmodel_etgm = Control('ETGM', float, 1)
        self.cmodel_mtm = Control('MTM', float, 1)
        # Weiland options
        self.weiland_exbs = Control('ExB shear coefficient', float, 1)
        self.weiland_mpsf = Control('Momentum pinch scaling factor', float, 1)
        self.weiland_lbetd = Control('Lower bound of electron thermal diffusivity', float, 0)
        self.weiland_ubetd = Control('Upper bound of electron thermal diffusivity', float, 100)
        self.weiland_lbitd = Control('Lower bound of ion thermal diffusivity', float, 0)
        self.weiland_ubitd = Control('Upper bound of ion thermal diffusivity', float, 100)
        # DRIBM options
        self.dribm_exbs = Control('ExB shear coefficient', float, 1)
        self.dribm_kyrhos = Control('kyrhos', float, 0.1, label=r'$k_y \rho_s$')
        # MTM options
        self.mtm_kyrhos_loops = Control('kyrhos scan iterations', int, 2000)
        self.mtm_capsw = Control('capsw', int, 1)
        self.mtm_ky_kx = Control('ky/kx', float, 0.2, label=r'$k_y/k_x$')
        self.mtm_cf = Control('calibration factor', float, 1)
        self.mtm_kyrhos_min = Control('lower limit of kyrhos scan', float, 0.005, label=r'$k_\mathrm{y}\rho_\mathrm{s}$')
        self.mtm_kyrhos_max = Control('upper limit of kyrhos scan', float, 10, label=r'$(k_\mathrm{y}\rho_\mathrm{s})_\mathrm{max}$')
        self.mtm_gmax_mult = Control('gmax coefficient', float, 1, label=r'$g_\mathrm{max, mtm}$')
        # ETG options
        self.etg_jenko_threshold = Control('Jenko threshold', int, 2)
        self.etg_cees_scale = Control('CEES scale', float, 0.06)
        self.etg_ceem_scale = Control('CEEM scale', float, 0.06)
        # ETGM options
        self.etgm_cl = Control('1: Collisional limit, 0: collisionless', int, 1)
        self.etgm_sat_expo = Control('Saturation ratio exponent (min 0)', int, 2)
        self.etgm_sum_modes = Control('Sum modes, 0: Use most unstable mode', int, 0)
        self.etgm_exbs = Control('ExB shear coefficient', float, 0)
        self.etgm_kyrhos_type = Control('1: Exponential kyrhos increments, 0: Linear kyrhos increments', int, 1)
        self.etgm_kyrhos_min = Control('lower limit of kyrhos scan', float, 1, label=r'$k_\mathrm{y}\rho_\mathrm{s}$')
        self.etgm_kyrhos_max = Control('upper limit of kyrhos scan', float, 50)
        self.etgm_kyrhos_scan = Control('Number of kyrhos scan loops (min 50), 0: disable kyrhos scan', int, 50)
        self.etgm_diffusivity_type = Control('0: Default diffusivity, 1: Alternate diffusivity', int, 0)
        self.etgm_kxoky = Control('kx / ky', float, 0.1)
        self.etgm_gmax_mult = Control('gmax multiplier', float, 2)
        self.etgm_xte_max_cal = Control('xte calibration (max)', float, 1)
        self.etgm_xte_sum_cal = Control('xte calibration (sum)', float, 1)
        self.etgm_xte2_max_cal = Control('xte2 calibration (max)', float, 1)
        self.etgm_xte2_sum_cal = Control('xte2 calibration (max)', float, 1)
        self.etgm_disable_geometry = Control('1: Theta, alpha = 0, 0: Default G_ave', int, 0)
        self.etgm_electrostatic = Control('1: Electrostatic, 0: Electromagnetic', int, 0)
        self.etgm_empty_int = Control('empty', int, 1)
        self.etgm_xte_min_gte = Control('empty', float, 0.01)
        self.etgm_alpha_mult = Control('alphaMHD mult', float, 1, label=r'$\alpha_\mathrm{MHD,u}$')
        self.etgm_betae_mult = Control('betae mult', float, 1, label=r'$\beta_\mathrm{e,u}$')
        self.etgm_nuei_mult = Control('nuei mult', float, 1, label=r'$\nu_\mathrm{ei}$')
        self.etgm_vthe_mult = Control('vthe mult', float, 1, label=r'$v_\mathrm{Te}$')
        self.etgm_betaep_mult = Control('beta_prime mult', float, 1, label=r'$\beta^\prime$')
        self.etgm_extra_mult = Control('extra', float, 1)

        # Verbose level
        self.lprint = Control('Verbose Level', values=0, vtype=int)

        self.input_points.values = options.input_points if options else None
        self.options = options
        self.set(**kwargs)

    def set(self, **kwargs):
        '''Sets specified control values'''
        for key, value in kwargs.items():
            if not hasattr(self, key):
                raise ValueError(f'Invalid control specified: {key}')
            getattr(self, key).values = value

        self.verify_values()

    def verify_values(self):
        '''Verifies that certain control values are correct and fixes them if needed'''
        ...

    def get_mmm_header(self):
        '''
        Gets the header for the MMM input file

        Raises:
        * TypeError: If input_points.values is None
        * TypeError: If input_points.values is of type np.ndarray
        '''

        if not self.input_points.values and self.options.input_points:
            self.input_points.values = self.options.input_points

        if not self.input_points.values:
            raise TypeError('input_points must be set to generate the MMM header')
        if isinstance(self.input_points.values, np.ndarray):
            raise TypeError('Unable to create MMM header for controls loaded with array values')
        return (
            '&testmmm_input_control\n'
            f'   npoints = {self.input_points.get_input_line()}'
            f'   input_kind = 1\n'
            '/\n'
            '&testmmm_input_1stkind\n'
            '\n'
            '!.. Switches for component models (1D0 - ON, 0D0 - OFF)\n'
            'cmodel  =\n'
            f'   {self.cmodel_weiland.get_input_line()}'
            f'   {self.cmodel_dribm.get_input_line()}'
            f'   {self.cmodel_etg.get_input_line()}'
            f'   {self.cmodel_mtm.get_input_line()}'
            f'   {self.cmodel_etgm.get_input_line()}'
            '\n'
            '!.. Weiland real options\n'
            'cW20 =\n'
            f'   {self.weiland_exbs.get_input_line()}'
            f'   {self.weiland_mpsf.get_input_line()}'
            f'   {self.weiland_lbetd.get_input_line()}'
            f'   {self.weiland_ubetd.get_input_line()}'
            f'   {self.weiland_lbitd.get_input_line()}'
            f'   {self.weiland_ubitd.get_input_line()}'
            '\n'
            '!.. DRIBM real options\n'
            'cDBM =\n'
            f'   {self.dribm_exbs.get_input_line()}'
            f'   {self.dribm_kyrhos.get_input_line()}'
            '\n'
            '!.. MTM integer options\n'
            'lMTM =\n'
            f'   {self.mtm_kyrhos_loops.get_input_line()}'
            f'   {self.mtm_capsw.get_input_line()}'
            '\n'
            '!.. MTM real options\n'
            'cMTM =\n'
            f'   {self.mtm_ky_kx.get_input_line()}'
            f'   {self.mtm_cf.get_input_line()}'
            f'   {self.mtm_kyrhos_min.get_input_line()}'
            f'   {self.mtm_kyrhos_max.get_input_line()}'
            f'   {self.mtm_gmax_mult.get_input_line()}'
            '\n'
            '!.. ETG integer options\n'
            'lETG =\n'
            f'   {self.etg_jenko_threshold.get_input_line()}'
            '\n'
            '!.. ETG real options\n'
            'cETG =\n'
            f'   {self.etg_cees_scale.get_input_line()}'
            f'   {self.etg_ceem_scale.get_input_line()}'
            '\n'
            '!.. ETGM integer options\n'
            'lETGM =\n'
            f'   {self.etgm_cl.get_input_line()}'
            f'   {self.etgm_kyrhos_scan.get_input_line()}'
            f'   {self.etgm_diffusivity_type.get_input_line()}'
            f'   {self.etgm_sat_expo.get_input_line()}'
            f'   {self.etgm_sum_modes.get_input_line()}'
            f'   {self.etgm_kyrhos_type.get_input_line()}'
            f'   {self.etgm_empty_int.get_input_line()}'
            f'   {self.etgm_empty_int.get_input_line()}'
            f'   {self.etgm_empty_int.get_input_line()}'
            f'   {self.etgm_empty_int.get_input_line()}'
            # f'   {self.etgm_disable_geometry.get_input_line()}'
            # f'   {self.etgm_electrostatic.get_input_line()}'
            '\n'
            '!.. ETGM real options\n'
            'cETGM =\n'
            f'   {self.etgm_exbs.get_input_line()}'
            f'   {self.etgm_kyrhos_min.get_input_line()}'
            f'   {self.etgm_kyrhos_max.get_input_line()}'
            f'   {self.etgm_kxoky.get_input_line()}'
            f'   {self.etgm_gmax_mult.get_input_line()}'
            f'   {self.etgm_xte_min_gte.get_input_line()}'
            f'   {self.etgm_xte_max_cal.get_input_line()}'
            f'   {self.etgm_xte_sum_cal.get_input_line()}'
            f'   {self.etgm_xte2_max_cal.get_input_line()}'
            f'   {self.etgm_xte2_sum_cal.get_input_line()}'
            # f'   {self.etgm_alpha_mult.get_input_line()}'
            # f'   {self.etgm_betae_mult.get_input_line()}'
            # f'   {self.etgm_nuei_mult.get_input_line()}'
            # f'   {self.etgm_vthe_mult.get_input_line()}'
            # f'   {self.etgm_betaep_mult.get_input_line()}'
            '\n'
            f'lprint = {self.lprint.get_input_line()}'
            '\n'
        )

    def get_scanned_control(self):
        return getattr(self, self.options.var_to_scan)

    def get_keys(self):
        '''Returns (list): All keys of input controls'''
        return [o for o in dir(self) if isinstance(getattr(self, o), Control)]

    def get_key_values_pairs(self):
        '''Returns (list): All key-values pairs of input controls'''
        keys = self.get_keys()
        return [f'{o}, {getattr(self, o).values}' for o in keys]

    def print_key_values_pairs(self):
        '''Prints: All key-values pairs of input controls'''
        kvps = self.get_key_values_pairs()
        for kvp in kvps:
            print(kvp)

    def save(self, scan_factor=None):
        '''
        Saves InputControls data to CSV

        If scan_factor is specified, then var_to_scan must also be specified

        Parameters:
        * scan_factor (float): The value of the scan factor (Optional)
        '''

        runid = self.options.runid
        scan_num = self.options.scan_num
        var_to_scan = self.options.var_to_scan

        if scan_factor:
            scan_factor_str = f'{scan_factor:{constants.SCAN_FACTOR_FMT}}'
            save_dir = utils.get_var_to_scan_path(runid, scan_num, var_to_scan)
            file_name = (f'{save_dir}\\{SaveType.CONTROLS.name.capitalize()} {var_to_scan}'
                         f'{constants.SCAN_FACTOR_VALUE_SEPARATOR}{scan_factor_str}.csv')
        else:
            save_dir = utils.get_scan_num_path(runid, scan_num)
            file_name = f'{save_dir}\\{SaveType.CONTROLS.name.capitalize()}.csv'

        control_data = self.get_key_values_pairs()

        with open(file_name, 'w') as f:
            for data in control_data:
                f.write(f'{data}\n')

        _log.info(f'\n\tSaved: {file_name}\n')

    def load_from_csv(self, scan_factor=None, use_rho=False):
        '''
        Loads Controls data from a CSV into the current Controls object

        If either parameter use_rho or scan_factor are specified, then
        var_to_scan must also be specified.

        Parameters:
        * scan_factor (float): The scan_factor, if doing a variable scan (optional)
        * use_rho (bool): True if the CSV to load is in the rho folder (optional)
        '''

        runid = self.options.runid
        scan_num = self.options.scan_num
        var_to_scan = self.options.var_to_scan
        controls_name = SaveType.CONTROLS.name.capitalize()

        if use_rho:
            dir_path = utils.get_rho_path(runid, scan_num, var_to_scan)
            control_files = utils.get_files_in_dir(dir_path, f'{controls_name}*', show_warning=False)

            if scan_factor:
                _log.warning(f'\n\tThe scan_factor input parameter is not used when use_rho is True')

        elif scan_factor is not None:
            dir_path = utils.get_var_to_scan_path(runid, scan_num, var_to_scan)
            control_files = utils.get_files_in_dir(dir_path, f'{controls_name}*', show_warning=False)
            scan_factor_str = f'{scan_factor:{constants.SCAN_FACTOR_FMT}}'
            control_files = [file for file in control_files if scan_factor_str in file]

        else:
            dir_path = utils.get_scan_num_path(runid, scan_num)
            control_files = utils.get_files_in_dir(dir_path, f'{controls_name}*')

        # There may not be a Controls.CSV file to load in some cases, which is expected for
        # plotting scanned variables when var_to_scan is not a Control
        if control_files:
            if use_rho:
                self._load_from_np_csv(control_files[0])
            else:
                self._load_from_simple_csv(control_files[0])

    def _load_from_simple_csv(self, file_name):
        '''
        Loads a simple CSV where each line is a single (key, value) pair

        Parameters:
        * file_name (str): The name and path of the file to open
        '''

        with open(file_name, 'r') as file:
            for line in file:
                key, value = line.replace('\n', '').split(',')
                if hasattr(self, key):
                    getattr(self, key).values = float(value)

    def _load_from_np_csv(self, file_name):
        '''
        Loads a traditional CSV saved by Numpy where the first row contains all the keys, and values are in columns

        Parameters:
        * file_name (str): The name and path of the file to open
        '''

        data_array = np.genfromtxt(file_name, delimiter=',', dtype=float, names=True)
        control_names = data_array.dtype.names
        for name in control_names:
            if hasattr(self, name):
                getattr(self, name).values = data_array[name]


class Control:
    def __init__(self, name, vtype, values, label='', units_label=''):
        self.name = name
        self.vtype = vtype
        self.values = values
        self.label = label
        self.units_label = units_label

    def get_value_str(self):
        return int(self.values) if self.vtype is int else f'{self.values:{constants.INPUT_CONTROL_VALUE_FMT}}D0'

    def get_input_line(self):
        return f'{self.get_value_str()}  ! {self.name}\n'


'''
For testing purposes:
* There need to be existing folders corresponding to the runid and scan_num when saving controls
'''
if __name__ == '__main__':
    import modules.options
    options = modules.options.Options(runid='TEST', scan_num=373, input_points=51)

    '''Print sample MMM Header from user-specified Options'''
    controls = InputControls(options)
    print(f'Example MMM Header:\n{"-"*50}')
    print(controls.get_mmm_header())

    '''Print Controls values loaded from CSV'''
    controls = InputControls(options)
    controls.load_from_csv()
    print(f'Controls Values Loaded From CSV:\n{"-"*50}')
    controls.print_key_values_pairs()

    '''Save Controls to CSV'''
    controls.save()
