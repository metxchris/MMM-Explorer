# Standard Packages
import copy
import inspect
import sys
sys.path.insert(0, '../')

# 3rd Party Packages
import numpy as np
from scipy.interpolate import interp1d  # TODO: use Akima1DInterpolator?

# Local Packages
from main import variables, constants
from main.options import Options


def vpol(vars):
    '''Poloidal Velocity'''
    vpol = np.zeros((vars.xb.values.shape[0], vars.time.values.shape[0]))
    if vars.vpolavg.values is not None:
        vpol = vars.vpolavg.values
    elif vars.vpold.values is not None:
        vpol = vars.vpold.values
    elif vars.vpolh.values is not None:
        vpol = vars.vpolh.values

    vars.vpol.set_variable(vpol, 'M/SEC', ['XBO', 'TIME'])

def nh0(vars):
    '''Hydrogen Ion Density'''
    nd = vars.nd.values
    ne = vars.ne.values
    nf = vars.nf.values
    nz = vars.nz.values
    zimp = vars.zimp.values

    nh0 = ne - zimp * nz - nf - nd

    vars.nh0.set_variable(nh0, vars.ne.units, ['XBO', 'TIME'])

def nh(vars):
    '''Total Hydrogenic Ion Density'''
    nh0 = vars.nh0.values
    nd = vars.nd.values

    nh = nh0 + nd

    vars.nh.set_variable(nh, '', ['XBO', 'TIME'])

def ni(vars):
    '''Thermal Ion Density'''
    nd = vars.nd.values
    nh0 = vars.nh0.values
    nz = vars.nz.values

    ni = nd + nz + nh0

    vars.ni.set_variable(ni, vars.ne.units, ['XBO', 'TIME'])

def ahyd(vars):
    '''Mean atomic mass of hydrogenic ions (hydrogen + dueterium)'''
    nh0 = vars.nh0.values
    nd = vars.nd.values

    ahyd = (nh0 + 2 * nd) / (nh0 + nd)

    vars.ahyd.set_variable(ahyd, '', ['XBO', 'TIME'])

def aimass(vars):
    '''# Mean Atomic Mass of Thermal Ions'''
    ahyd = vars.ahyd.values
    aimp = vars.aimp.values
    nh = vars.nh.values
    nz = vars.nz.values

    aimass = (ahyd * nh + aimp * nz) / (nh + nz)

    vars.aimass.set_variable(aimass, '', ['XBO', 'TIME'])

# Rho (Approximation for rho)
def rho(vars):
    rmin = vars.rmin.values

    rho = rmin / rmin[-1, :]

    vars.rho.set_variable(rho, '', ['XBO', 'TIME'])

def tau(vars):
    '''Temperature Ratio'''
    te = vars.te.values
    ti = vars.ti.values

    tau = te / ti

    vars.tau.set_variable(tau, '', ['XBO', 'TIME'])

def vtor(vars):
    '''Toroidal Velocity'''
    rmaj = vars.rmaj.values
    omega = vars.omega.values

    vtor = rmaj * omega

    vars.vtor.set_variable(vtor, 'M/SEC', ['XBO', 'TIME'])

def vpar(vars):
    '''Parallel Velocity'''
    bpol = vars.bpol.values
    btor = vars.btor.values
    vpol = vars.vpol.values
    vtor = vars.vtor.values

    vpar = vtor + vpol * bpol / btor

    vars.vpar.set_variable(vpar, vars.vtor.units, ['XBO', 'TIME'])

def zeff(vars):
    '''Effective Charge'''
    ne = vars.ne.values
    nf = vars.nf.values
    nh = vars.nh.values
    nz = vars.nz.values
    zimp = vars.zimp.values

    zeff = (nh + nf + zimp**2 * nz) / ne

    vars.zeff.set_variable(zeff, '', ['XBO', 'TIME'])

def btor(vars):
    '''Toroidal Magnetic Field'''
    bz = vars.bz.values
    raxis = vars.rmaj.values[0, :]
    rmaj = vars.rmaj.values

    btor = raxis / rmaj * bz

    vars.btor.set_variable(btor, vars.bz.units, ['XBO', 'TIME'])

def bpol(vars):
    '''Poloidal Magnetic Field'''
    btor = vars.btor.values
    q = vars.q.values
    rmaj = vars.rmaj.values
    rmin = vars.rmin.values

    bpol = rmin / rmaj * btor / q

    vars.bpol.set_variable(bpol, vars.btor.units, ['XBO', 'TIME'])

# Inverse Aspect Ratio
def eps(vars):
    arat = vars.arat.values

    eps = 1 / arat

    vars.eps.set_variable(eps, '', ['XBO', 'TIME'])

# Plasma Pressure
def p(vars):
    zckb = constants.ZCKB
    ne = vars.ne.values
    ni = vars.ni.values
    te = vars.te.values
    ti = vars.ti.values

    p = (ne * te + ni * ti) * zckb

    vars.p.set_variable(p, 'PA', ['XBO', 'TIME'])

# Beta
def beta(vars):
    zcmu0 = constants.ZCMU0
    btor = vars.btor.values
    p = vars.p.values

    beta = 2 * zcmu0 * p / btor**2

    vars.beta.set_variable(beta, '', ['XBO', 'TIME'])

# Electron Beta
def betae(vars):
    zckb = constants.ZCKB
    zcmu0 = constants.ZCMU0
    btor = vars.btor.values
    ne = vars.ne.values
    te = vars.te.values

    betae = 2 * zcmu0 * ne * te * zckb / btor**2

    vars.betae.set_variable(betae, '', ['XBO', 'TIME'])

# TODO: Need to add equations for different TE ranges
def loge(vars):
    '''Electron Coulomb Logarithm'''
    ne = vars.ne.values
    te = vars.te.values
    zeff = vars.zeff.values

    # loge = 39.23 - np.log(zeff*ne**(1 / 2) / te)  # TRANSP definition
    loge = 37.8 - np.log(ne**(1 / 2) / te)  # NRL Plasma Formulary Definition
    
    vars.loge.set_variable(loge, '', ['XBO', 'TIME'])

# Collision Frequency (NU_{ei})
def nuei(vars):
    zcf = constants.ZCF
    ne = vars.ne.values
    te = vars.te.values
    zeff = vars.zeff.values
    loge = vars.loge.values

    nuei = zcf * 2**(1/2) * ne * loge * zeff / te**(3/2)

    vars.nuei.set_variable(nuei, 's^-1', ['XBO', 'TIME'])

# OLD NOTE: Not sure what to call this, but it leads to the approx the correct NUSTI
def nuei2(vars):
    zcf = constants.ZCF
    ni = vars.ni.values
    ti = vars.ti.values
    zeff = vars.zeff.values
    loge = vars.loge.values

    nuei2 = zcf * 2**(1/2) * ni * loge * zeff / ti**(3/2)

    vars.nuei2.set_variable(nuei2, 's^-1', ['XBO', 'TIME'])

# Thermal Velocity of Electrons
def vthe(vars):
    zckb = constants.ZCKB
    zcme = constants.ZCME
    te = vars.te.values

    vthe = (2 * zckb * te / zcme)**(1/2)

    vars.vthe.set_variable(vthe, 'm/s', ['XBO', 'TIME'])

# Thermal Velocity of Ions
def vthi(vars):
    zckb = constants.ZCKB
    zcmp = constants.ZCMP
    aimass = vars.aimass.values
    ti = vars.ti.values

    vthi = (zckb * ti / (zcmp * aimass))**(1/2)

    vars.vthi.set_variable(vthi, 'm/s', ['XBO', 'TIME'])

# Electron Collisionality (NU^{*}_{e}) TODO: units?
# OLD NOTE: This is in approximate
# agreement with NUSTE in transp.  One source of the disagreement is
# likely because the modmmm7_1.f90 Coulomb logarithm (loge) does not
# match perfectly with the TRANSP version (CLOGE).
def nuste(vars):
    eps = vars.eps.values
    nuei = vars.nuei.values
    q = vars.q.values
    rmaj = vars.rmaj.values
    vthe = vars.vthe.values

    nuste = nuei * eps**(-3/2) * q * rmaj / vthe

    vars.nuste.set_variable(nuste, '', ['XBO', 'TIME'])

# Ion Collisionality (NUSTI = NU^{*}_{i}) TODO: Units
# OLD NOTE: This is approx correct, but
# agreement is also somewhat time-dependent.  The issue is possibly due
# to the artifical AIMASS that we are using.  We likely also need to
# use the coulomb logarithm for ions as well.
def nusti(vars):
    zcme = constants.ZCME
    zcmp = constants.ZCMP
    eps = vars.eps.values
    q = vars.q.values
    nuei2 = vars.nuei2.values
    rmaj = vars.rmaj.values
    vthi = vars.vthi.values

    nusti = nuei2 * eps**(-3/2) * q * rmaj / (2 * vthi) * (zcme / zcmp)**(1/2)

    vars.nusti.set_variable(nusti, '', ['XBO', 'TIME'])

def gyrfi(vars):
    '''Ion Gyrofrequency'''
    zce = constants.ZCE
    zcmp = constants.ZCMP
    aimass = vars.aimass.values
    btor = vars.btor.values

    gyrfi = zce * btor / (zcmp * aimass)

    vars.gyrfi.set_variable(gyrfi, 's^-1', ['XBO', 'TIME'])

def gmax(vars):
    '''Upper bound for ne, nh, te, and ti gradients in DRBM model (modmmm.f90)'''
    eps = vars.eps.values
    q = vars.q.values
    rmaj = vars.rmaj.values
    gyrfi = vars.gyrfi.values
    vthi = vars.vthi.values

    gmax = rmaj / (vthi / gyrfi * q / eps)

    vars.gmax.set_variable(gmax, '', ['XBO', 'TIME'])

# Magnetic Shear
def shear(vars):
    gq = vars.gq.values
    rmaj = vars.rmaj.values
    rmin = vars.rmin.values

    shear = gq * rmin / rmaj

    vars.shear.set_variable(shear, '', ['XBO', 'TIME'])

# Effective Magnetic Shear
def shat(vars):
    elong = vars.elong.values
    shear = vars.shear.values

    shat = (2 * shear - 1 + (elong * (shear - 1))**2)**(1/2)
    shat[shat < 0] = 0

    vars.shat.set_variable(shat, '', ['XBO', 'TIME'])

# Alpha MHD (Weiland Definition)
def alphamhd(vars):
    betae = vars.betae.values
    gne = vars.gne.values
    gni = vars.gni.values
    gte = vars.gte.values
    gti = vars.gti.values
    q = vars.q.values
    te = vars.te.values
    ti = vars.ti.values

    alphamhd = q**2 * betae * (gne + gte + ti / te * (gni + gti))

    vars.alphamhd.set_variable(alphamhd, '', ['XBO', 'TIME'])

def gave(vars):
    shear = vars.shear.values
    alphamhd = vars.alphamhd.values

    gave = 2/3 + 5/9 * shear - 5/12 * alphamhd

    vars.gave.set_variable(gave, '', ['XBO', 'TIME'])

def etae(vars):
    gte = vars.gte.values
    gne = vars.gne.values

    etae = gte / gne

    vars.etae.set_variable(etae, '', ['XBO', 'TIME'])

def etai(vars):
    gti = vars.gti.values
    gni = vars.gni.values

    etai = gti / gni

    vars.etai.set_variable(etai, '', ['XBO', 'TIME'])

def etaih(vars):
    gti = vars.gti.values
    gnh = vars.gnh.values

    etaih = gti / gnh

    vars.etaih.set_variable(etaih, '', ['XBO', 'TIME'])

def etaie(vars):
    gti = vars.gti.values
    gne = vars.gne.values

    etaie = gti / gne

    vars.etaie.set_variable(etaie, '', ['XBO', 'TIME'])

def etaid(vars):
    gti = vars.gti.values
    gnd = vars.gnd.values

    etaid = gti / gnd

    vars.etaid.set_variable(etaid, '', ['XBO', 'TIME'])

# Test variables are just used for testing calculations, and are not sent to the MMM driver
def test(vars):
    nh = vars.nh.values
    nd = vars.nd.values

    ni = nh + nd

    vars.test.set_variable(ni)

# Test variables are just used for testing calculations, and are not sent to the MMM driver
def test2(vars):
    gti = vars.gti.values
    gni = vars.gtest.values

    test2 = gti / gni

    vars.test2.set_variable(test2)

def calculate_gradient(gvar_name, var_name, drmin, vars):
    rmaj = vars.rmaj.values
    x = vars.x.values[:, 0]
    xb = vars.xb.values[:, 0]  # includes origin

    # get variables related to the gradient from variable names
    gvar = getattr(vars, gvar_name)
    var = getattr(vars, var_name)

    # partial derivative along x-axis
    dxvar = np.diff(var.values, axis=0) / drmin

    # intepolate from x to xb
    set_interp = interp1d(x, dxvar, kind='cubic', fill_value="extrapolate", axis=0)
    dxvar = set_interp(xb)

    # take gradient
    gradient_values = rmaj * dxvar / var.values
    gvar.set_variable(gradient_values, '', ['XBO', 'TIME'])

    if Options.instance.apply_smoothing:
        gvar.apply_smoothing(Options.instance.input_points)

    gvar.clamp_gradient(100)
    gvar.set_minvalue()

    if Options.instance.reject_outliers:
        gvar.reject_outliers()

    gvar.remove_nan()

# Calculate the variable specified by it's corresponding function
def calculate_variable(var_function, vars):
    var_function(vars)

    # Get the variable name specified by var_function
    var_name = var_function.__name__

    if Options.instance.apply_smoothing:
        getattr(vars, var_name).apply_smoothing(Options.instance.input_points)

    getattr(vars, var_name).set_minvalue()

    if Options.instance.reject_outliers:
        getattr(vars, var_name).reject_outliers()

    getattr(vars, var_name).remove_nan()

# Calculates new variables needed for MMM and data display from CDF variables
# Values are stored to vars within each function call
def calculate_inputs(cdf_vars):
    vars = copy.deepcopy(cdf_vars)

    # Some calculations depend on values from previous calculations
    calculate_variable(vpol, vars)
    calculate_variable(nh0, vars)
    calculate_variable(nh, vars)
    calculate_variable(ni, vars)
    calculate_variable(ahyd, vars)
    calculate_variable(aimass, vars)
    calculate_variable(rho, vars)
    calculate_variable(tau, vars)
    calculate_variable(btor, vars)
    calculate_variable(bpol, vars)
    calculate_variable(vtor, vars)
    calculate_variable(vpar, vars)
    calculate_variable(zeff, vars)
    calculate_variable(eps, vars)
    calculate_variable(p, vars)
    calculate_variable(beta, vars)
    calculate_variable(betae, vars)
    calculate_variable(loge, vars)
    calculate_variable(nuei, vars)
    calculate_variable(nuei2, vars)
    calculate_variable(vthe, vars)
    calculate_variable(vthi, vars)
    calculate_variable(nuste, vars)
    calculate_variable(nusti, vars)
    calculate_variable(gyrfi, vars)
    calculate_variable(gmax, vars)

    # Differential rmin needed for gradient calculations
    drmin = np.diff(vars.rmin.values, axis=0)

    # Calculate gradients.  The sign on drmin sets the sign of the gradient equation
    calculate_gradient('gne',   'ne',   -drmin, vars)
    calculate_gradient('gnh',   'nh',   -drmin, vars)
    calculate_gradient('gni',   'ni',   -drmin, vars)
    calculate_gradient('gnz',   'nz',   -drmin, vars)
    calculate_gradient('gnd',   'nd',   -drmin, vars)
    calculate_gradient('gq',    'q',     drmin, vars)
    calculate_gradient('gte',   'te',   -drmin, vars)
    calculate_gradient('gti',   'ti',   -drmin, vars)
    calculate_gradient('gvpar', 'vpar', -drmin, vars)
    calculate_gradient('gvpol', 'vpol', -drmin, vars)
    calculate_gradient('gvtor', 'vtor', -drmin, vars)

    # Calculations dependent on gradient variables
    calculate_variable(shear, vars)
    calculate_variable(shat, vars)
    calculate_variable(alphamhd, vars)
    calculate_variable(gave, vars)
    calculate_variable(etae, vars)
    calculate_variable(etai, vars)
    calculate_variable(etaie, vars)
    calculate_variable(etaih, vars)
    calculate_variable(etaid, vars)

    # Test variables are just used for testing calculations, and are not sent to the MMM driver
    calculate_variable(test, vars)
    calculate_gradient('gtest', 'test', -drmin, vars)
    calculate_variable(test2, vars)

    return vars


def get_calculated_vars():
    '''Returns function names of calculated variables in this module, other than gradient calculations'''
    return [o[0] for o in inspect.getmembers(sys.modules[__name__]) if inspect.isfunction(o[1]) and 'calculate' not in o[0]]


if __name__ == '__main__':
    ...
