"""
Thermodynamic Calculator

Scripts to calculate a variety of thermodynamic quantities such as equilibrium
vapor pressure, LCL pressure and temperature, mixing ratio, equivalent potential
temperature, equivalent temperature, saturated equivalent potential temperature,
and wet bulb potential temperature.

The LCL script approximates the temperature and pressure level of the LCL given
the surface temperature, pressure and dew point. The approximation is made using
a method of bisections (using the fact that w_sfc - w_s(T_lcl) = 0).

Note: Here is a link to the NOAA radiosonde realtime database (for data):
http://www.esrl.noaa.gov/raobs/

Shawn Murdzek
sfm5282@psu.edu
"""


from math import exp, log, floor
import numpy as np


def e_s(T):
    """
    Calculates the equilibrium vapor pressure (Pa) at temperature T (K) using
    the Clausius-Clapeyron Equation.
    Inputs:
        T = Temperature (K)
    Outputs:
        evp = Equilibrium vapor pressure (Pa)
    Local Variables:
        lv = Enthalpy of vaporization (J/kg)
        Rv = Gas constant for water vapor (J/kg*K)
    """
    
    T = float(T)
    lv = 2.5 * (10**6)
    Rv = 461.5
    
    evp = 611*exp((lv/Rv)*((1/273.15) - (1/T)))
    return evp


def LCL(T, P, Td):
    """
    Calculates the temperature and pressure of the LCL (Lifted Condensation
    Level) using the fact that the mixing ratio and potential temperature are
    conserved below the LCL. The method of bisections is used to approximate the
    value of the LCL temperature and pressure.
    Inputs:
        T = Surface temperature (K)
        P = Surface pressure (Pa)
        Td = Surface dew point (K)
    Outputs:
        P_lcl = Pressure at LCL (Pa)
        T_lcl = Temperature at LCL (K)
    Local Variables:
        Rd = Gas constant for dry air (J/kg*K)
        cp = Specific heat for dry air at constant pressure (J/kg*K)
        epn = Ratio of molar mass of water vapor to molar mass of dry air
        e_sfc = Vapor pressure at surface (Pa)
        w = Mixing ratio (unitless, kg/kg)
        upper = upper bound of interval
        lower = lower bound of interval
        middle = middle of interval
        T_up = LCL temperature for upper bound (K)
        T_low = LCL temperature for lower bound (K)
        T_mid = LCL temperature for middle of interval (K)
        P_up = LCL pressure for upper bound (Pa)
        P_low = LCL pressure for lower bound (Pa)
        P_mid = LCL pressure for middle of interval (Pa)
    """

    # Define local variables
    Rd = 287.04
    cp = 1005.0
    epn = 0.622

    # Check for condition where T = Td
    if T == Td:
        P_lcl = P
        T_lcl = T
    else:
        
        # Calculate surface vapor pressure, mixing ratio:
        e_sfc = e_s(Td)
        w = (epn*e_sfc) / (P - e_sfc)

        # Find T_lcl such that w_sfc - w_s(T_lcl) = 0
        T_up = T
        P_up = ((T_up/T)**(cp/Rd)) * P
        upper = w - ((epn*e_s(T_up)) / (P_up - e_s(T_up)))
        T_low = 150.0
        P_low = ((T_low/T)**(cp/Rd)) * P
        lower = w - ((epn*e_s(T_low)) / (P_low - e_s(T_low)))
        while abs(abs(upper) - abs(lower)) > 0.000001:
            T_mid = 0.5*(T_up + T_low)
            P_mid = ((T_mid/T)**(cp/Rd)) * P
            middle = w - ((epn*e_s(T_mid)) / (P_mid - e_s(T_mid)))
            if (upper > 0 and middle < 0) or (upper < 0 and middle > 0):
                T_low = T_mid
            else:
                T_up = T_mid
            P_up = ((T_up/T)**(cp/Rd)) * P
            upper = w - ((epn*e_s(T_up)) / (P_up - e_s(T_up)))
            P_low = ((T_low/T)**(cp/Rd)) * P
            lower = w - ((epn*e_s(T_low)) / (P_low - e_s(T_low)))
        T_lcl = 0.5*(T_low + T_up)

        # Find P_lcl using Poisson's Relations
        P_lcl = ((T_lcl/T)**(cp/Rd)) * P
    
    return T_lcl, P_lcl


def mixing(Td, P):
    """
    Calculates the mixing ratio given a dew point and a pressure using equation
    5.14 in Bohren's "Atmospheric Thermodynamics".
    Inputs:
        Td = Dew point (K)
        P = Pressure (Pa)
    Outputs:
        w = Mixing ratio (kg/kg, unitless)
    Local Variables:
        epn = Ratio of molar mass of water vapor to molar mass of dry air
    """

    Td = float(Td)
    P = float(P)
    epn = 0.622
    w = epn * (e_s(Td) / (P - e_s(Td)))
    return w


def theta_e(T, P, Td):
    """
    Returns the equivalent potential temperature given the parcel's initial
    temperature, pressure, and dew point using equation 6.121 in Bohren's
    "Atmospheric Thermodynamics".
    Inputs:
        T = Initial temperature of parcel (K)
        P = Initial pressure of parcel (Pa)
        Td = Initial dew point of parcel (K)
    Outputs:
        thet_e = Equivalent potential temperature (K)
    Local Variables:
        lv = Enthalpy of vaporization (J/kg)
        cp = Specific heat capacity at constant pressure (J/kg*K)
        Rd = Gas constant for dry air (J/kg*K)
        T_lcl = Temperature of parcel at LCL (deg C)
        P_lcl = Pressure of parcel at LCL (deg C)
        thet_d = Dry potential temperature (K)
        w_s = Saturation mixing ratio (mixing ratio at LCL) (kg/kg)
        e_lcl = Vapor pressure at LCL (Pa)
    """

    # Define local variables:
    lv = 2.5 * (10**6)
    cp = 1005.0
    Rd = 287.04

    # Find temperature and pressure of parcel at LCL:
    T_lcl, P_lcl = LCL(T, P, Td)

    # Calculate mixing ratio and thet_d at LCL:
    w_s = mixing(T_lcl, P_lcl)
    e_lcl = e_s(T_lcl)
    thet_d = T_lcl * ((100000.0 / (P_lcl - e_lcl)) ** (Rd /cp))

    # Calculate thet_e:
    thet_e = thet_d * exp((lv * w_s) / (cp * T_lcl))

    return thet_e


def T_e(T, P, Td):
    """
    Returns the equivalent temperature of a parcel given the parcel's initial
    temperature, pressure, and dew point. Equivalent temperature is calculated
    using equation 6.74 in Bohren's "Atmospheric Thermodynamics".
    Inputs:
        T = Initial temperature of parcel (K)
        P = Initial pressure of parcel (Pa)
        Td = Initial dew point of parcel (K)
    Outputs:
        Te = Equivalent temperature (K)
    Local Variables:
        lv = Enthalpy of vaporization (J/kg)
        cp = Specific heat capacity of dry air at constant pressure (J/kg*K)
        cw = Specific heat capacity of water (J/kg*K)
        w = Mixing ratio (kg/kg)
    """

    # Define local variables:
    lv = 2.5 * (10**6)
    cp = 1005.0
    cw = 4218.0

    # Calculate Te
    w = mixing(Td, P)
    Te = T + ((lv*w) / (cp + w*cw))
    return Te


def theta_es(T, P):
    """
    Calculates the saturated equivalent potential temperature given the parcel's
    initial temperature, pressure, and dew point.
    Inputs:
        T = Temperature of parcel (K)
        P = Initial pressure of parcel (Pa)
        Td = Initial dew point of parcel (K)
    Outputs:
        thet_es = Saturated equivalent potential temperature (K)
    """
    
    thet_es = theta_e(T, P, T)
    return thet_es


def theta_wb(T, P, Td):
    """
    Returns the wet bulb potential temperature of a parcel given the parcel's
    initial temperature, pressure, and dew point. Like with the LCL calculator,
    this script uses bisections to find thet_wb. The equation used in this
    script is equation 6.142 in Bohren's "Atmospheric Thermodynamics".
    Inputs:
        T = Initial temperature of parcel (K)
        P = Initial pressure of parcel (Pa)
        Td = Initial dew point of parcel (K)
    Outputs:
        thet_wb = Wet bulb potential temperature (K)
    Local Variables:
        lv = Enthalpy of vaporization (J/kg)
        cp = Specific heat capacity (J/kg*K)
        Rd = Gas constant for dry air (J/kg*K)
        T_lcl = Temperature at LCL (K)
        P_lcl = Pressure at LCL (Pa)
        w = Mixing ratio of parcel (kg/kg)
        thet_d = Dry potential temperature (K)
        e_lcl = Vapor pressure at LCL (Pa)
    """

    # Define local variables:
    lv = 2.5 * (10**6)
    cp = 1005.0
    Rd = 287.04

    # Find T_lcl, mixing ratio (at LCL):
    T_lcl, P_lcl = LCL(T, P, Td)
    w = mixing(T_lcl, P_lcl)

    # Find thet_d:
    e_lcl = e_s(T_lcl)
    thet_d = T_lcl * ((100000.0 / (P_lcl - e_lcl)) ** (Rd /cp))

    # Find thet_wb using method of bisections:
    thet_wb_up = 100.0
    w_s_up = mixing(thet_wb_up, 100000.0)
    upper = (thet_d * exp((lv/cp) * ((w/T_lcl) - (w_s_up/thet_wb_up))) -
             thet_wb_up)
    thet_wb_low = thet_d
    w_s_low = mixing(thet_wb_low, 100000.0)
    lower = (thet_d * exp((lv/cp) * ((w/T_lcl) - (w_s_low/thet_wb_low))) -
             thet_wb_low)

    while abs(abs(upper) - abs(lower)) > 0.000001:
        thet_wb_mid = 0.5*(thet_wb_up + thet_wb_low)
        w_s_mid = mixing(thet_wb_mid, 100000.0)
        middle = (thet_d * exp((lv/cp) * ((w/T_lcl) - (w_s_mid/thet_wb_mid))) -
                  thet_wb_mid)
        if (upper > 0 and middle < 0) or (upper < 0 and middle > 0):
            thet_wb_low = thet_wb_mid
        else:
            thet_wb_up = thet_wb_mid
        w_s_up = mixing(thet_wb_up, 100000.0)
        upper = (thet_d * exp((lv/cp) * ((w/T_lcl) - (w_s_up/thet_wb_up))) -
                 thet_wb_up)
        w_s_low = mixing(thet_wb_low, 100000.0)
        lower = (thet_d * exp((lv/cp) * ((w/T_lcl) - (w_s_low/thet_wb_low))) -
                 thet_wb_low)
    thet_wb = 0.5*(thet_wb_low + thet_wb_up)

    return thet_wb


def Td_from_RH(T, RH):
    """
    Returns the dew point given the temperature and relative humidity.
    Inputs:
        T = Temperature (K)
        RH = Relative humidity (as a decimal)
    Outputs:
        Td = Dew point (K)
    Local Variables:
        Rv = Gas constant for water vapor (J/kg*K)
        lv = Enthalpy of vaporization (J/kg)
        e = Vapor pressure (Pa)
    """

    # Define Local Variables:
    Rv = 461.5
    lv = 2.5 * (10**6)

    # Calculate vapor pressure
    e = RH * e_s(T)

    # Calculate Td:
    Td = (1/273.15 - (Rv/lv)*log(e/611.0)) ** (-1.0)
    return Td


def theta(T, P):
    """
    Returns the potential temperature given an initial temperature and pressure
    using Possion's Relations.
    Inputs:
        T = Temperature (K)
        P = Pressure (Pa)
    Outputs:
        thet = Potential temperature (K)
    Local Variables:
        Rd = Gas constant for dry air (J/kg*K)
        cp = Specific heat capacity for dry air at constant pressure (J/kg*K)
    """

    # Define local variables:
    Rd = 287.04
    cp = 1005.0

    # Calculate thet with Possion's Relations
    thet = T * ((100000.0 / P) ** (Rd/cp))
    return thet


def DALR(theta, p1 = 100000.0, p2 = 10000.0, step = 1000):
    """
    Returns a two column array containing pressures in the first column and
    corresponding temperatures in the second column of a dry adiabat (constant
    potential temperature). Temperatures are calculated using Poisson's
    Relations.
    Inputs:
        theta = Potential temperature of dry adiabat (K)
    Keywords:
        p1 = Lower pressure bound for adiabat (Pa)
        p2 = Upper pressure bound for adiabat (Pa)
        step = Difference between each pressure level where temperature is
            calculated (Pa)
    Outputs:
        d_adiabat = Two column array of a dry adiabat containing pressures (Pa)
            in the first column and temperatures (K) in the second column
    Local Variables:
        gamma = Ratio of cp/cv, where cp = heat capacity of dry air at constant
            pressure and cv = heat capacity of dry air at constant volume
    """

    # Pre-allocate array, define local variable:
    d_adiabat = np.zeros([floor((p1-p2)/step) + 1, 2], 'd')
    gamma = 1.4
    
    # Fill array using Poisson's Relations:
    for i in xrange(np.shape(d_adiabat)[0]):
        d_adiabat[i, 0] = p1 - step*i
        d_adiabat[i, 1] = (((100000.0 / d_adiabat[i, 0]) ** ((1 - gamma) /
                                                             gamma)) * theta)
    
    return d_adiabat


def mix_ratio(w, p1 = 100000.0, p2 = 50000.0, step = 1000):
    """
    Returns a two column array that contains the pressure in the first column
    and temperature in the second column of a saturation mixing ratio line. The
    mixing ratio is kept constant on a mixing ratio line, so knowing the
    pressure and mixing ratio, this script calculates the temperature (assuming
    T = Td).
    Inputs:
        w = Mixing ratio (kg/kg, unitless)
    Keywords:
        p1 = Lower pressure bound for mixing ratio line (Pa)
        p2 = Upper pressure bound for mixing ratio line (Pa)
        step = Difference between each pressure level where temperature is
            calculated (Pa)
    Outputs:
        mix_line = Two column array containing pressures (Pa) in the first
            column and temperatures (K) in the second column.
    Local Variables:
        Rv = Gas constant for water vapor (J/kg*K)
        lv = Enthalpy of vaporization (J/kg)
    """

    # Define Local Variables, pre-allocate array:
    Rv = 461.5
    lv = 2.5 * (10**6)
    mix_line = np.zeros([floor((p1-p2)/step) + 1, 2], 'd')

    # Calculate T at each pressure level for each w using bisections:
    # Note that T_up is set to the value where p - e_s(T) = 5000
    for i in xrange(np.shape(mix_line)[0]):
        mix_line[i, 0] = p1 - step*i    
        T_up = (1/273.15 - (Rv/lv)*log(((mix_line[i, 0])-5000.0)
                                             /611.0)) ** (-1.0)
        upper = mixing(T_up, mix_line[i, 0]) - w
        T_low = 150.0
        lower = mixing(T_low, mix_line[i, 0]) - w
        while abs(T_up - T_low) > 0.01:
            T_mid = 0.5 * (T_low + T_up)
            mid = mixing(T_mid, mix_line[i, 0]) - w
            if (upper > 0 and mid < 0) or (upper < 0 and mid > 0):
                T_low = T_mid
                lower = mixing(T_low, mix_line[i, 0]) - w
            else:
                T_up = T_mid
                upper = mixing(T_up, mix_line[i, 0]) - w
        mix_line[i, 1] = 0.5*(T_up + T_low)
            
    return mix_line


def MALR(thet_e_0, p1 = 100000.0, p2 = 20000.0, step = 1000):
    """
    Returns a two column array that gives the pressure (1st column) and
    temperature (2nd column) of a moist adiabat from p1 to p2. This script makes
    use of the fact that theta_e is conserved when traveling along a moist
    adiabat, and uses the method of bisections to find T given a certain P and
    theta_e.
    Inputs:
        thet_e_0 = Equivalent potential temperature of moist adiabat (K)
    Keywords:
        p1 = Lower pressure bound (Pa)
        p2 = Upper pressure bound (Pa)
        step = Step size between pressure levels where temperature is calculated
            (mb)
    Outputs:
        m_adiabat = Two column array of points along this moist adiabat, goes
            (T, P), where T is in K and P is in Pa
    Local Variables:
        Rv = Gas constant for water vapor (J/kg*K)
        lv = Enthalpy of vaporization (J/kg)
    """

    # Define local variables, allocate array:
    Rv = 461.5
    lv = 2.5 * (10**6)
    m_adiabat = np.zeros([floor(abs((p1-p2)/step)) + 1, 2], 'd')
    
    # Finding T at each pressure level such that theta_e is constant
    # Note that T_up is set to the value where p - e_s(T) = 5000
    count = 0
    for p in xrange(int(p1), int(p2 - 1), int((-1)*step)):
        T_low = 100.0
        T_up = (1/273.15 - (Rv/lv)*log((p-5000.0)/611.0)) ** (-1.0)
        lower = theta_e(T_low, p, T_low) - thet_e_0
        upper = theta_e(T_up, p, T_up) - thet_e_0
        while abs(T_up - T_low) > 0.01:
            T_mid = 0.5*(T_low + T_up)
            mid = theta_e(T_mid, p, T_mid) - thet_e_0
            if (upper > 0 and mid < 0) or (upper < 0 and mid > 0):
                T_low = T_mid
                lower = theta_e(T_low, p, T_low) - thet_e_0
            else:
                T_up = T_mid
                upper = theta_e(T_up, p, T_up) - thet_e_0
        T = 0.5*(T_up + T_low)
        m_adiabat[count, 0] = p
        m_adiabat[count, 1] = T
        count = count + 1

    return m_adiabat


def virt_T(T, w):
    """
    Calculates the virtual temperature using the equation, T_v = T(1+0.61w),
    which is similar to equation 6.48 in Bohren's "Atmospheric Thermodynamics".
    Inputs:
        T = Temperature (K)
        w = Mixing ratio (kg/kg, unitless)
    Outputs:
        T_v = Virtual temperature (K)
    """

    T_v = T * (1 + 0.61*w)
    return T_v


def lin_interp(X, x1, y1, x2, y2):
    """
    Function that creates a line between (x1, y1) and (x2, y2) and then
    interpolates the y-value for x-value X.
    Inputs:
        X = x-value where the y-value is being interpolated
        x1 = x-value of first point
        y1 = y-value of firts point
        x2 = x-value of second point
        y2 = y-value of second point
    Outputs:
        Y = y-value for x-value X
    Local Variables:
        m = Slope of line
    """

    m = (y2 - y1) / (x2 - x1)
    Y = m * (X - x1) + y1
    return Y


def parcel_prof(P, prs, temp, dew, step = 'same', p1 = 100000.0, p2 = 10000.0):
    """
    Creates three 1D arrays of the pressure, temperature, and dew point of a
    parcel originating at pressure level P.
    Inputs:
        P = Pressure level where parcel originates (Pa)
        prs = 1D array of environmental pressures (Pa)
        temp = 1D arra of environmental temperatures (K)
        dew = 1D array of environmental dew points (K)
    Keywords:
        step = Distance (in Pa) between pressure levels for the parcel profile.
            If set to 'same', parcel will have same pressure levels as prs
        p1 = Lower pressure bound (Pa)
        p2 = Upper pressure bound (Pa)
    Outputs:
        p_prs = 1D array of parcel pressures (Pa)
        p_temp = 1D array of parcel temperatures (K)
        p_dew = 1D array of parcel dew points (K)
    Local Variables:
        T = Initial temperature of parcel (K)
        D = Initial dew point of parcel (K)
        lcl_T = Temperature at LCL (K)
        lcl_P = Pressure at LCL (Pa)
        thet = Potential temperature of parcel below LCL (K)
        thet_e = Equivalent potential temperature of parcel (K)
        w = Mixing ratio below LCL (kg/kg, unitless)
        min_p = Value in prs array immediately below pressure level where parcel
            originates (Pa)
        max_p = Value in prs array immediately above pressure level where parcel
            originates (Pa)
        min_p_index = Index of min_p
        max_p_index = Index of max_p
        ind_below_lcl = Parcel indices below LCL
        lcl_ind = Largest index below LCL
    """

    # Find parcel's initial pressure, temperature, and dew point:
    if P in prs:
        T = temp[np.where(prs==P)[0][0]]
        D = dew[np.where(prs==P)[0][0]]
    else:
        # Estimating T and D using the lin_interp function
        min_p = np.amin(np.extract(prs > P, prs))
        max_p = np.amax(np.extract(prs < P, prs))
        min_p_index = np.where(prs==min_p)[0][0]
        max_p_index = np.where(prs==max_p)[0][0]
        T = lin_interp(np.log10(P), np.log10(min_p),
                        temp[min_p_index], np.log10(max_p),
                        temp[max_p_index])
        D = lin_interp(np.log10(P), np.log10(min_p),
                        dew[min_p_index], np.log10(max_p),
                        dew[max_p_index])
        
    # Find LCL, theta and w below LCL, theta_e:
    [lcl_T, lcl_P] = LCL(T, P, D)
    thet = theta(T, P)
    thet_e = theta_e(T, P, D)
    w = mixing(D, P)

    # Pre-allocate p_prs, p_temp, p_dew:
    if step == 'same':
        p_prs = prs
    elif (P >= np.amin(prs)) and (P <= np.amax(prs)):
        p_prs = np.arange(p1, p2 - 1, (-1)*step)
    p_temp = np.zeros([len(p_prs)], 'd')
    p_dew = np.zeros([len(p_prs)], 'd')

    # Fill p_temp and p_dew using MALR, DALR, and mix_ratio:
    ind_below_lcl = np.where(p_prs >= lcl_P)
    lcl_ind = np.max(ind_below_lcl)
    if step == 'same':
        if p2 < lcl_P:
            for i in xrange(lcl_ind + 1):
                p_temp[i] = DALR(thet, p1 = p_prs[i], p2 = p_prs[i] -
                                 10.0)[0, 1]
                p_dew[i] = mix_ratio(w, p1 = p_prs[i], p2 = p_prs[i] -
                                     10.0)[0, 1]
            for i in range(1, len(p_prs) - lcl_ind):
                p_temp[i + lcl_ind] = MALR(thet_e, p1 = p_prs[i + lcl_ind], p2 =
                                           p_prs[i + lcl_ind] - 10.0)[0, 1]
                p_dew[i + lcl_ind] = MALR(thet_e, p1 = p_prs[i + lcl_ind], p2 =
                                          p_prs[i + lcl_ind] - 10.0)[0, 1]
        else:
            for i in xrange(len(p_prs)):
                p_temp[i] = DALR(thet, p1 = p_prs[i], p2 = p_prs[i] -
                                 10.0)[0, 1]
                p_dew[i] = mix_ratio(w, p1 = p_prs[i], p2 = p_prs[i] -
                                     10.0)[0, 1]
    else:
        if p2 < lcl_P:
            p_temp[0:lcl_ind + 1] = DALR(thet, p1 = p1, p2 = lcl_P, step =
                                         step)[:, 1]
            p_dew[0:lcl_ind + 1] = mix_ratio(w, p1 = p1, p2 = lcl_P, step =
                                             step)[:, 1]
            p_temp[lcl_ind + 1:] = MALR(thet_e, p1 = p_prs[lcl_ind] - step,
                                        p2 = p2, step = step)[:, 1]
            p_dew[lcl_ind + 1:] = MALR(thet_e, p1 = p_prs[lcl_ind] - step,
                                       p2 = p2, step = step)[:, 1]
        else:
            p_temp = DALR(thet, p1 = p1, p2 = p2)
            p_dew = mix_ratio(w, p1 = p1, p2 = p2)
    
    return p_prs, p_temp, p_dew


def env_prof(prs, temp, dew, step = 1000.0, p1 = 100000.0, p2 = 10000.0):
    """
    Approximates the temperature and dew point of an environmental sounding
    between p1 and p2 using the lin_interp function. We are assuming that the
    temperature and dew point of the parcel change in a linear fashion between
    each pair of points in the sounding. If p1 and/or p2 lie outside the range
    of the original sounding, those pressure levels will be extrapolated by
    treating the profile as a dry adiabat.
    Inputs:
        prs = 1D array of environmental pressures, going from surface to space
            (Pa)
        temp = 1D array of environmental temperatures (K)
        dew = 1D array of environmental dew points (K)
    Keywords:
        step = Step size between successive points
        p1 = Lower pressure bound (Pa)
        p2 = Upper pressure bound (Pa)
    Outputs:
        env_prs = 1D array of environmental pressures (Pa)
        env_temp = 1D array of interpolated environmental temperatures (K)
        env_dew = 1D array of interpolated environmental dew points (K)
    Local Variables:
        gamma = Ratio of specific heat capacity of dry air at constant pressure
            to specific heat capacity of dry air at constant volume (unitless)
        max_p_in = Pressure level index in prs array immediately below
            env_prs[i]
        min_p_in = Pressure level index in prs array immediately above
            env_prs[i]
        thet_low = Potential temperature for first pressure level in prs (K)
        thet_high = Potential temperature for last pressure level in prs (K)
        mix_low = Mixing ratio for first pressure level in prs (Pa)
        mix_high = Mixing ration for last pressure level in prs (Pa)
        low_in = Last index in env_prs below prs[0]
        high_in = First index in env_prs above prs[-1]
    """

    # Pre-allocate arrays, define local variables:
    env_prs = np.arange(p1, p2 - 1, (-1)*step, 'd')
    env_temp = np.zeros([len(env_prs)], 'd')
    env_dew = np.zeros([len(env_prs)], 'd')
    gamma = 1.4
    
    # Fill env_temp and env_dew arrays with lin_interp:
    for i in xrange(len(env_prs)):
        if env_prs[i] in prs:
            env_temp[i] = temp[np.where(prs == env_prs[i])]
            env_dew[i] = dew[np.where(prs == env_prs[i])]
        elif env_prs[i] < np.amax(prs) and env_prs[i] > np.amin(prs):
            max_p_in = np.amax(np.where(prs > env_prs[i]))
            min_p_in = np.amin(np.where(prs < env_prs[i]))
            env_temp[i] = lin_interp(log(env_prs[i], 10), log(prs[max_p_in], 10)
                                     , temp[max_p_in], log(prs[min_p_in], 10),
                                     temp[min_p_in])
            env_dew[i] = lin_interp(log(env_prs[i], 10), log(prs[max_p_in], 10),
                                    dew[max_p_in], log(prs[min_p_in], 10),
                                    dew[min_p_in])

    # Fill remaining values by approximating with dry adiabat:
    if env_prs[0] > prs[0]:
        thet_low = theta(temp[0], prs[0])
        mix_low = mixing(dew[0], prs[0])
        low_in = np.argmax(np.where(env_prs > prs[0]))
        env_temp[0:low_in+1] = DALR(thet_low, p1 = env_prs[0], p2 =
                                    env_prs[low_in], step = step)[:, 1]
        env_dew[0:low_in+1] = mix_ratio(mix_low, p1 = env_prs[0], p2 =
                                        env_prs[low_in], step = step)[:, 1]
    if env_prs[-1] < prs[-1]:
        thet_high = theta(temp[-1], prs[-1])
        mix_high = mixing(dew[-1], prs[-1])
        high_in = np.argmin(np.where(env_prs < prs[-1]))
        env_temp[high_in:] = DALR(thet_high, p1 = env_prs[high_in], p2 =
                                  env_prs[-1], step = step)[:, 1]
        env_dew[high_in:] = mix_ratio(mix_high, p1 = env_prs[high_in], p2 =
                                      env_prs[-1], step = step)[:, 1]

    return env_prs, env_temp, env_dew
                             
             
def EL(prs, temp, dew, P = 'sfc', accuracy = 50.0):
    """
    Finds the equilibrium level of a sounding, the level where the parcel
    originating from pressure level P becomes negatively buoyant. This script
    uses the virtual temperature to assess where the parcel becomes positively
    buoyant, starting at the top of the sounding.
    Inputs:
        prs = 1D array of pressure levels (Pa)
        temp = 1D array of temperatures (K)
        dew = 1D array of dew points (K)
    Keywords:
        P = Pressure level where parcel originates (Pa). If set to 'sfc', parcel
            originates at the surface
        accuracy = The pressure level with be equal to the actual EL plus/minus
            the accuracy value (in Pa). Maximum value is 50.0
    Outputs:
        el = Equilibrium level (Pa)
    Local Variables:
        env_T_v = Environmental virtual temperatures (K)
        par_T_v = Parcel virtual temperatures (K)
        step = Step for env_prof and parcel_prof
        prs_prof = Pressure levels from env_prof and parcel_prof with step
            specified by accuracy keyword
        e_temp = Environmental temperature from env_prof
        e_dew = Environmental dew points from env_prof
        p_temp = Parcel temperature from parcel_prof
        p_dew = Parcel dew point from parcel_prof
    """

    # Set P if P = 'sfc', call env_prof and parcel_prof
    if P == 'sfc':
        P = np.amax(prs)
    step = accuracy * 2.0
    [prs_prof, e_temp, e_dew] = env_prof(prs, temp, dew, step = step, p1 =
                                        np.amax(prs), p2 = np.amin(prs))
    [prs_prof, p_temp, p_dew] = parcel_prof(P, prs, temp, dew, step = step, p1 =
                                           np.amax(prs), p2 = np.amin(prs))

    # Starting from top of sounding, find where parcel virtual temperature is
    # greater than environmental virtual temperature
    for i in xrange(len(prs_prof)):
        env_T_v = virt_T(e_temp[-1-i], mixing(e_dew[-1-i], prs_prof[-1-i]))
        par_T_v = virt_T(p_temp[-1-i], mixing(p_dew[-1-i], prs_prof[-1-i]))
        if env_T_v == par_T_v:
            el = prs_prof[-1-i]
            break
        elif env_T_v < par_T_v:
            prs_below = prs_prof[-1-i]
            prs_above = prs_prof[(-1)*i]
            el = 0.5 * (prs_below + prs_above)
            break

    return el


def LFC(prs, temp, dew, P = 'sfc', accuracy = 50.0):
    """
    Finds the level of free convection of a sounding, the level where the parcel
    originating from pressure level P becomes negatively buoyant. This script
    uses the virtual temperature to assess where the parcel becomes negatively
    buoyant, starting at the equilibrium level.
    Inputs:
        prs = 1D array of pressure levels (Pa)
        temp = 1D array of temperatures (K)
        dew = 1D array of dew points (K)
    Keywords:
        P = Pressure level where parcel originates (Pa). If set to 'sfc', parcel
            originates at the surface
        accuracy = The pressure level with be equal to the actual LFC plus/minus
            the accuracy value (in Pa). Maximum value is 50.0
    Outputs:
        lfc = Level of free convection (Pa)
    Local Variables:
        el = Equilibrium level for same sounding (Pa)
        env_T_v = Environmental virtual temperatures (K)
        par_T_v = Parcel virtual temperatures (K)
        step = Step for env_prof and parcel_prof
        prs_prof = Pressure levels from env_prof and parcel_prof with step
            specified by accuracy keyword
        e_temp = Environmental temperature from env_prof
        e_dew = Environmental dew points from env_prof
        p_temp = Parcel temperature from parcel_prof
        p_dew = Parcel dew point from parcel_prof
    """

    # Find el, set P if P = 'sfc', call env_prof and parcel_prof
    el = EL(prs, temp, dew, P = P, accuracy = accuracy)
    if P == 'sfc':
        P = np.amax(prs)
    step = accuracy * 2.0
    [prs_prof, e_temp, e_dew] = env_prof(prs, temp, dew, step = step, p1 =
                                        np.amax(prs), p2 = el)
    [prs_prof, p_temp, p_dew] = parcel_prof(P, prs, temp, dew, step = step, p1 =
                                           np.amax(prs), p2 = el)

    # Starting from top of sounding, find where parcel virtual temperature is
    # greater than environmental virtual temperature
    for i in xrange(len(prs_prof)):
        env_T_v = virt_T(e_temp[-1-i], mixing(e_dew[-1-i], prs_prof[-1-i]))
        par_T_v = virt_T(p_temp[-1-i], mixing(p_dew[-1-i], prs_prof[-1-i]))
        if env_T_v == par_T_v:
            lfc = prs_prof[-1-i]
            break
        elif env_T_v > par_T_v:
            prs_below = prs_prof[-1-i]
            prs_above = prs_prof[(-1)*i]
            lfc = 0.5 * (prs_below + prs_above)
            break

    return lfc
#-------------------------------------------------------------------------------
"""
T = 3.0 + 273.15
P = 60000.0
Td = -5.0 + 273.15

print
[T_lcl, P_lcl] = LCL(T, P, Td)
print "T_lcl (deg C) =", round((T_lcl - 273.15), 2)
print "P_lcl (mb) =", round((P_lcl / 100.0), 2)
print "w (g/kg) =", round((mixing(Td, P) * 1000.0), 2)
print "Td (deg C) =", round((Td - 273.15), 2) 
print "Te (deg C) =", round((T_e(T, P, Td) - 273.15), 2)
print "Theta e (deg C) =", round((theta_e(T, P, Td) - 273.15), 2)
print "Theta es (deg C) =", round((theta_es(T, P) - 273.15), 2)
print "Theta wb (deg C) =", round((theta_wb(T, P, Td) - 273.15), 2)
print "Theta (deg C) =", round((theta(T, P) - 273.15), 2)
"""

#-------------------------------------------------------------------------------
"""
Notes for development:

For functions involving lin_interp, check before hand to make sure prs array
starts at the surface and goes towards space. If this is not so, the prs, temp,
and dew arrays will need to be concatenated into a 3 X n array and then sorted
along the prs axis. If this is not done, certain functions (like the env_prof
and parcel_prof) will not work.

Re-write LFC and EL scripts in fortran so they run faster, then use f2py.

"""
