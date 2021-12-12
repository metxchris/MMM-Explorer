# Standard Packages
import sys
sys.path.insert(0, '../')

# Local Packages
from main import utils
from main.enums import ShotType, DataType


class InputControls:
    '''
    Input Controls for the MMM input file

    Notes:
    * Controls defined here are will be placed into the header of the MMM input file
    * Controls with vtype=int are expected as Fortran Integer types in the input file
    * Controls with vtype=float are expected as Fortran Real types in the input file
    '''

    def __init__(self, options=None):
        self.npoints = Control('npoints', 'Number of radial points', values=51, vtype=int)
        # Switches for component models
        self.cmodel_weiland = Control('cmodel_weiland', 'Weiland', values=1, vtype=float)
        self.cmodel_dribm = Control('cmodel_dribm', 'DRIBM', values=1, vtype=float)
        self.cmodel_etg = Control('cmodel_etg', 'ETG', values=1, vtype=float)
        self.cmodel_etgm = Control('cmodel_etgm', 'ETGM', values=1, vtype=float)
        self.cmodel_mtm = Control('cmodel_mtm', 'MTM', values=1, vtype=float)
        # Weiland options
        self.weiland_exbs = Control('weiland_exbs', 'ExB shear coefficient', values=1, vtype=float)
        self.weiland_mpsf = Control('weiland_mpsf', 'Momentum pinch scaling factor', values=1, vtype=float)
        self.weiland_lbetd = Control('weiland_lbetd', 'Lower bound of electron thermal diffusivity', values=0, vtype=float)
        self.weiland_ubetd = Control('weiland_ubetd', 'Upper bound of electron thermal diffusivity', values=100, vtype=float)
        self.weiland_lbitd = Control('weiland_lbitd', 'Lower bound of ion thermal diffusivity', values=0, vtype=float)
        self.weiland_ubitd = Control('weiland_ubitd', 'Upper bound of ion thermal diffusivity', values=100, vtype=float)
        # DRIBM options
        self.dribm_exbs = Control('dribm_exbs', 'ExB shear coefficient', values=1, vtype=float)
        self.dribm_kyrhos = Control('dribm_kyrhos', 'kyrhos', values=0.1, vtype=float, label=r'$k_y \rho_s$')
        # MTM options
        self.mtm_ky_kx = Control('mtm_ky_kx', 'ky/kx for MTM', values=0.2, vtype=float, label=r'$k_y/k_x$')
        self.mtm_cf = Control('mtm_cf', 'calibration factor', values=1.0, vtype=float)
        # ETG options
        self.etg_jenko_threshold = Control('etg_jenko_threshold', 'Jenko threshold', values=2, vtype=int)
        self.etg_cees_scale = Control('etg_cees_scale', 'CEES scale', values=0.06, vtype=float)
        self.etg_ceem_scale = Control('etg_ceem_scale', 'CEEM scale', values=0.06, vtype=float)
        # ETGM options
        self.etgm_cl = Control('etgm_cl', 'Collisionless limit', values=1, vtype=int)
        self.etgm_exbs = Control('etgm_exbs', 'ExB shear coefficient', values=0.0, vtype=float)
        self.etgm_kyrhoe = Control('etgm_kyrhoe', 'kyrhoe', values=0.25, vtype=float, label=r'$k_y \rho_e$')
        self.etgm_kyrhos = Control('etgm_kyrhos', 'kyrhos', values=0.33, vtype=float, label=r'$k_y \rho_s$')
        # Verbose level
        self.lprint = Control('lprint', 'Verbose Level', values=0, vtype=int)

        # Private members are not input controls, but are used to help verify control values
        self._shot_type = ShotType.NONE

        # Update values from options, if available
        if options is not None:
            self.update_from_options(options)

    def update_from_options(self, options):
        '''Updates any controls dependent on options values, then verifies values'''
        self.npoints.values = options.input_points
        self._shot_type = options.shot_type
        self.verify_values()

    def set(self, **kwargs):
        '''Sets all control values, then verifies values'''
        for key, value in kwargs.items():
            getattr(self, key).values = value

        self.verify_values()

    def verify_values(self):
        '''Verifies that certain values are correct and fixes them if needed'''

        # Note: The DRIBM model is currently disabled for NSTX discharges
        if self._shot_type == ShotType.NSTX:
            self.cmodel_dribm.values = 0

        self.etgm_kyrhos.values = max(1e-6, self.etgm_kyrhos.values)
        self.etgm_kyrhoe.values = max(0, self.etgm_kyrhoe.values)

    def get_mmm_header(self):
        return MMM_HEADER.format(
            npoints=self.npoints.get_value_str(),
            cmodel_weiland=self.cmodel_weiland.get_value_str(),
            cmodel_dribm=self.cmodel_dribm.get_value_str(),
            cmodel_etg=self.cmodel_etg.get_value_str(),
            cmodel_etgm=self.cmodel_etgm.get_value_str(),
            cmodel_mtm=self.cmodel_mtm.get_value_str(),
            weiland_exbs=self.weiland_exbs.get_value_str(),
            weiland_mpsf=self.weiland_mpsf.get_value_str(),
            weiland_lbetd=self.weiland_lbetd.get_value_str(),
            weiland_ubetd=self.weiland_ubetd.get_value_str(),
            weiland_lbitd=self.weiland_lbitd.get_value_str(),
            weiland_ubitd=self.weiland_ubitd.get_value_str(),
            dribm_exbs=self.dribm_exbs.get_value_str(),
            dribm_kyrhos=self.dribm_kyrhos.get_value_str(),
            mtm_ky_kx=self.mtm_ky_kx.get_value_str(),
            mtm_cf=self.mtm_cf.get_value_str(),
            etg_jenko_threshold=self.etg_jenko_threshold.get_value_str(),
            etg_cees_scale=self.etg_cees_scale.get_value_str(),
            etg_ceem_scale=self.etg_ceem_scale.get_value_str(),
            etgm_cl=self.etgm_cl.get_value_str(),
            etgm_exbs=self.etgm_exbs.get_value_str(),
            etgm_kyrhoe=self.etgm_kyrhoe.get_value_str(),
            etgm_kyrhos=self.etgm_kyrhos.get_value_str(),
            lprint=self.lprint.get_value_str(),
        )

    def get_keys(self):
        return [o for o in dir(self) if not callable(getattr(self, o)) and not o.startswith("_")]

    def get_values(self):
        keys = self.get_keys()
        return [getattr(self, o).values for o in keys]

    def get_key_values_pairs(self):
        '''Returns (list): All key-values pairs of input controls'''

        keys = self.get_keys()
        return [str(o) + ', ' + str(getattr(self, o).values).replace('\n', '') for o in keys]

    def save_controls(self, options, scan_factor=None):
        '''Saves InputControls data to CSV'''

        if scan_factor is None:
            save_dir = utils.get_scan_num_path(options.runid, options.scan_num)
            file_name = f'{save_dir}\\{DataType.CONTROL.name.capitalize()}.csv'
        else:
            scan_factor_str = '{:.3f}'.format(scan_factor)
            save_dir = utils.get_var_to_scan_path(options.runid, options.scan_num, options.var_to_scan)
            file_name = f'{save_dir}\\{DataType.CONTROL.name.capitalize()} {options.var_to_scan} = {scan_factor_str}.csv'

        control_data = self.get_key_values_pairs()

        f = open(file_name, 'w')
        for data in control_data:
            f.write(f'{data}\n')

        print(f'Input controls saved to \n    {file_name}\n')


class Control:
    def __init__(self, name, desc, values, vtype, label='', units_label=''):
        self.name = name
        self.desc = desc
        self.values = values
        self.vtype = vtype
        self.label = label
        self.units_label = units_label

    def get_value_str(self):
        return int(self.values) if self.vtype is int else f'{self.values}D0'


# Header for MMM input file
MMM_HEADER = (
    '''&testmmm_input_control
    npoints = {npoints}    ! Number of radial points
    input_kind = 1
    /
    &testmmm_input_1stkind
    ! This is a sample input file of the first kind
    ! of an NSTX discharge

    !.. Switches for component models
    !   1D0 - ON, 0D0 - OFF
    cmodel  =
       {cmodel_weiland}    ! Weiland
       {cmodel_dribm}    ! DRIBM
       {cmodel_etg}    ! ETG
       {cmodel_mtm}    ! MTM
       {cmodel_etgm}    ! ETGM

    !.. Weiland real options
    cW20 =
       {weiland_exbs}     ! ExB shear coefficient
       {weiland_mpsf}     ! Momentum pinch scaling factor
       {weiland_lbetd}     ! Lower bound of electron thermal diffusivity
       {weiland_ubetd}     ! Upper bound of electron thermal diffusivity
       {weiland_lbitd}     ! Lower bound of ion thermal diffusivity
       {weiland_ubitd}     ! Upper bound of ion thermal diffusivity

    !.. DRIBM real options
    cDBM =
       {dribm_exbs}     ! ExB shear coefficient
       {dribm_kyrhos}   ! kyrhos

    !.. MTM real options
    cMTM =
       {mtm_ky_kx}   ! ky/kx for MTM
       {mtm_cf}   ! calibration factor

    !.. ETG integer options
    lETG =
       {etg_jenko_threshold}       ! Jenko threshold
               ! applied to both electrostatic and electromagnetic regimes

    !.. ETG real options
    cETG =
       {etg_cees_scale}    ! CEES scale
       {etg_ceem_scale}    ! CEEM scale

    !.. ETGM integer options
    lETGM =
       {etgm_cl}      ! Collisionless limit

    !.. ETGM real options
    cETGM =
       {etgm_exbs}     ! ExB shear coefficient
       {etgm_kyrhos}   ! kyrhos
       {etgm_kyrhoe}   ! kyrhoe

    lprint   = {lprint}      ! Verbose level\n\n''')

'''
For testing purposes:
* There need to be existing folders corresponding to the runid and scan_num when saving controls
'''
if __name__ == '__main__':
    from main.options import Options

    Options.instance.set(
        runid='129041A10',
        shot_type=ShotType.NSTX,
        input_points=51,
        scan_num=1)
    controls = InputControls(Options.instance)
    controls.set(
        etgm_kyrhos=0.65,
        etgm_kyrhoe=0.05,
    )

    print(controls.get_keys())
    print(controls.get_mmm_header())
    print(controls.get_key_values_pairs())
    # controls.save_controls(Options.instance)
