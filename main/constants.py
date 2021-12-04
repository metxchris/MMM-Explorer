# Physical Constants
PI = 3.1415926535
ZCE = 1.602176565 * 10**(-19);                                # Electron charge                [Coulomb]
ZCEPS0 = 8.854187817 * 10**(-12);                             # Vacuum electrical permittivity [farads/m]
ZCMU0 = 4 * PI * 10**(-7);                                    # Vacuum magnetic permeability   [henrys/m]
ZCME = 9.10938215 * 10**(-31);                                # Electron mass                  [kg]
ZCMP = 1.672621777 * 10**(-27);                               # Proton mass                    [kg]
ZCKB = ZCE * 10**3;                                           # Energy conversion factor       [J/keV]
ZCF = ((4 * PI**(1/2) / 3) * (ZCE / (4 * PI * ZCEPS0)) ** 2   # Collision frequency factor     TODO: units?
    * (ZCE / ZCKB) * (ZCE / ZCME * ZCE / ZCKB)**(1/2))
