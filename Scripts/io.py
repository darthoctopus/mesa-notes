#!/usr/bin/env python3

## Author: Joel Ong <joel.ong@yale.edu>
## Yale University Dept. of Astronomy

'''
Convenience functions for reading MESA and YREC output
'''

import pandas as pd
import numpy as np
from os.path import isdir, isfile
from astropy import units as u, constants as c
from scipy.interpolate import UnivariateSpline, interp1d

# list of column names, determined by reading the relevant documentation.

# FGONG: see documentation at https://www.astro.up.pt/corot/ntools/docs/CoRoT_ESTA_Files.pdf
# Some of this also determined by reading MESA source code

MESA_NAMES = {
    'X': 'x_mass_fraction_H',
    'Y': 'y_mass_fraction_He',
    'Z': 'z_mass_fraction_metals'
}

FGONG_GLOB_NAMES = [
        'M', 'R', 'L', 'Z', 'X_0', 'α', 'φ', 'ξ', 'β',
        'λ', 'R^2/P ∂2P/∂r2_c', 'R^2/ρ ∂2ρ/∂r2_c', 't',
        # Newer version of FGONG than in the documentation have more names
        # This is constructed for compatibility with MESA
        'Teff', 'G_N' # Yes, that's right, we're storing the gravitational constant
        ]
FGONG_NAMES = [
        'r', 'ln(m/M)', 'T', 'P', 'ρ', 'X', 'L', 'κ', 'εnuc',
        'Γ1', '∇ad', 'δ', 'cp', 'Nemu', 'A_ast', 'rX', 'Z', 'R-r',
        # A_ast is the dimensionless B-V frequency N^2 * r / g
        # εg (below) is gravitational luminosity density
        'εg', 'Lg', '3He', '12C', '13C', '14N', '16O',
        # partial derivatives of Γ1 wrt ρ, P, Y triple
        '∂logΓ1/∂logρ', '∂logΓ1/∂logP', '∂logΓ1/∂logY',
        # more elemental abundances
        '2H', 'Y', '7Li', '7Be', '15N', '17O', '18O', '20Ne',
        # Newer version of FGONG than in the documentation have more columns
        # Interestingly although these don't appear in the MESA source code, 
        # they seem to have been written out in some files I made with v8845.
        # I have no idea what they are.
        # '∇', '∇rad', '39na', '40na'
        ]

# GYRE (by Rich Townsend): see Git repo.
# Also some help gotten from MESA

GYRE_GLOB_NAMES = [
        "nrows", "M", "R", "L", "version"
    ]
GYRE_NAMES = [
        "k", "r", "m", "L", "P", "T", "ρ", "∇", "N2", "Γ1", "∇ad", "δ",
        "κ", "κκ_T", "κκ_ρ", "εnuc", "εε_T", "εε_ρ", "Ω"
        # Double letters here indicate boldface
    ]

# YREC: the format is self-documenting
# but not in a machine-readable manner

YREC_NAMES = [
        "shell", 'r/R', 'm/M', 'T', 'ρ', 'P', 'μ', 'L', 'ε', 'κ', '∇', '∇ad', 'Γ1',
        'Cp', 'Cv', 'X', 'Z', 'cs', 'S_1^2', 'N2', 'νcrit_+^2', 'νcrit_-^2'
    ]
YREC_TRACK_NAMES = [
        "model_number", "shells", "star_age", "X_center", "Y_center", "Z_center",
        "log(L/Lsun)", "log(R/Rsun)", "log(g)", "log(Teff)", "m_core/M",
        "m_envp/M", "%_Gr_Energy", "X_env", "Z_env", "He_core_mass",
        "M_T_max", "eta" 
    ]

# OSC: Also used by ADIPLS
# = quantities appearing directly in the dimensionless parameterisation
# of the oscillation equations (i.e. "theorist" quantities)

OSC_GLOB_NAMES = [
        'M', 'R'
]

OSC_NAMES = [
	'x', 'q/x^3', 'Vg', 'Γ1', 'A_ast', 'U'
]

def read_track(x, **kwargs):
    '''
    Read track file produced by MESA. If a directory is supplied,
    combine that with the profiles.index file in the directory.

    Input: folder containing file named history.data (and optionally
    profiles.index, integrals.csv)
    '''
    if not isdir(x):
        return pd.read_csv(x, **{'delim_whitespace': True, 'skiprows': 5, **kwargs})
    else:
        df1 = read_track(f'{x}/history.data')
        df2 = read_index(f'{x}/')

        df = pd.merge(df1, df2, on='model_number')
        if isfile(f"{x}/integrals.csv"):
            dfi = pd.read_csv(f"{x}/integrals.csv")
            df = pd.merge(df, dfi, on='model_number')
        return df

def read_profile(x, **kwargs):
    '''
    Read profile file produced by MESA.

    Input: filename (e.g. "profile\\d+.data")
    '''
    return dict(pd.read_csv(x, **{'delim_whitespace': True, 'skiprows': 1, 'nrows': 1, **kwargs}).iloc[0]), read_track(x)

def read_index(track):
    '''
    Read index file produced by MESA

    Input: folder containing file named profiles.index
    '''
    return pd.read_csv(track+'/profiles.index', delim_whitespace=True,
                         skiprows=1, names=['model_number', 'priority', 'profile'])

def read_gyre(f, **kwargs):
    '''
    Read GYRE model file produced by MESA

    Input: filename (e.g. "profile\\d+.data.GYRE")
    '''
    # GYRE accepts CGS units for its MESA input format; see documentation
    # Mesh points go from centre outwards (opposite from usual MESA profile files)
    info = pd.read_csv(f, delim_whitespace=True, nrows=1, names=GYRE_GLOB_NAMES, **kwargs).iloc[0].to_dict()
    profiles = pd.read_csv(f, delim_whitespace=True, skiprows=1, names=GYRE_NAMES, **kwargs)
    return info, profiles

def write_gyre(info, p):
    '''
    Write GYRE files of the same format as those read in by our read_gyre function.
    Returns a string that can be used to write to a file
    '''
    def ff(i):
        return '     %.16E' % i
    s = '%6d     %.16E     %.16E     %.16E%7d\n' % tuple([info[v] for v in GYRE_GLOB_NAMES])
    for i in range(len(p)):
        l = '%6d' % p.loc[i]['k']
        for k in GYRE_NAMES[1:]:
            l += ff(p.loc[i][k])
        s += l
        s += '\n'
    return s

def read_freqs(f, **kwargs):
    '''
    Read frequencies returned from GYRE: returns dict.
    '''
    df = pd.read_csv(f, skiprows=5, delim_whitespace=True, **kwargs)
    out = {}
    out['ν'] = df['Re(freq)'].values
    out['l'] = df['l'].values
    out['n_p'] = df['n_p'].values
    out['n_g'] = df['n_g'].values
    out['E'] = df['E_norm'].values
    return out

def read_fgong(file):
    with open(file, 'r') as f:
        desc = ''.join([f.readline() for _ in range(4)])\

    # These variable names are from the documentation
    NN, ICONST, IVAR, IVERS = np.loadtxt(file, skiprows=4, max_rows=1, dtype=int)
    # data = np.genfromtxt(file, skip_header=5, delimiter=16).flatten()
    data = np.loadtxt(file, skiprows=5).flatten()

    # Global names
    globs = {name: val for name, val in zip(FGONG_GLOB_NAMES, data[:ICONST])}
    globs['version'] = IVERS

    columns = data[ICONST:].reshape(NN, IVAR).T
    # Format columns into a DataFrame
    profiles = pd.DataFrame({
        name: val for name, val in zip(FGONG_NAMES, columns)
        })

    return globs, profiles

def gyre_to_fgong(info, profiles, mesa_profiles=None):

    glob = {k: 0. for k in FGONG_GLOB_NAMES}

    # Most of the quantities in the FGONG variable list are either obviously irrelevant to pulsations
    # and/or inaccessible from a GYRE file (and therefore seemingly irrelevant to pulsations)
    glob['M'] = info['M']
    glob['R'] = info['R']
    glob['L'] = info['L']
    glob['G_N'] = c.G.cgs.value # I assume?

    # Boundary conditions need some work
    R = glob['R']
    P = profiles['P'].values
    ρ = profiles['ρ'].values
    k = np.argmin((profiles['r'].values - R)**2)

    # I translate MESA's eval_center_d2 function
    def eval_center_d2(r, v, k_b):
        # fit a parabola with dv/dq = 0 at the center
        r1 = r[k_b]
        r2 = r[k_b - 1]

        v1 = v[k_b]
        v2 = v[k_b - 1]

        return 2 * (v2 - v1) / (r2*r2 - r1*r1)

    glob['R^2/P ∂2P/∂r2_c'] = R**2 / P[0] * eval_center_d2(profiles['r'].values, P, 1)
    glob['R^2/ρ ∂2ρ/∂r2_c'] = R**2 / ρ[0] * eval_center_d2(profiles['r'].values, ρ, 1)


    ######
    # populate columns
    ######

    n = len(profiles['k'])

    cols = {k: np.zeros(n) for k in FGONG_NAMES}
    for k in FGONG_NAMES:
        if k in GYRE_NAMES:
            cols[k] = np.copy(profiles[k])

    # Some special attention is required for some columns

    # log q
    lnq = np.log(profiles['m']/glob['M'])
    cols['ln(m/M)'] = lnq

    # Brunt-Vaisala frequency: GYRE stores N2 while FGONG uses A_ast
    # (dedimensionalisation wrt LOCAL quantities)
    r = cols['r']
    m = profiles['m']
    g = np.nan_to_num(c.G.cgs.value * m / r / r)
    cols['A_ast'] = np.nan_to_num(profiles['N2'] * r / g)

    # R - r
    cols['R-r'] = glob['R'] - np.array(profiles['r'])

    # Interestingly MESA sets ε, ε_g, L_g to 0.
    # We also don't have any compositional information in the GYRE file…
    # MESA also pointedly ignores the Γ1 EOS derivatives.
    # It turns out that most of the data ends up being 0 (i.e. no value)??

    # Some other columns become available if MESA profile files are also available

    if mesa_profiles is not None:
        N_MESA = len(mesa_profiles)
        def _(key):
            return interp1d(
                mesa_profiles['mass'].values[::-1] * c.M_sun.cgs.value,
                mesa_profiles[key].values[::-1],
                bounds_error = False,
                fill_value=(mesa_profiles[key].values[-1], mesa_profiles[key].values[0])
                )(profiles['m'])

        for name in MESA_NAMES:
            if MESA_NAMES[name] in mesa_profiles.columns:
                cols[name] = _(MESA_NAMES[name])

    return glob, pd.DataFrame(cols).iloc[::-1] # FGONG goes outside in vs GYRE's inside-out

def write_fgong(glob, profiles):
    '''
    Returns a string that can be written to a file.
    '''
    def format_single(x):
        return f"{'-' if x < 0 else ' '}{float(abs(np.nan_to_num(np.float32(x)))):.9E}"

    fmt = np.vectorize(format_single)

    # First row: four ints
    NN = len(profiles)
    ICONST = len(FGONG_GLOB_NAMES)
    IVAR = 40 # (exactly)
    IVERS = 1300 # same as MESA writes
    s = f'{NN: >10d}{ICONST: >10d}{IVAR: >10d}{IVERS: >10d}'

    # Header
    header = f"Produced by mesa_tricks\n\n\n\n{s}\n"

    meta = np.array([glob[k] for k in FGONG_GLOB_NAMES])
    cols = np.zeros((IVAR, NN))
    for i, k in enumerate(FGONG_NAMES):
        cols[i, ...] = profiles[k]

    data = fmt(np.concatenate((meta, cols.T.reshape(-1))).reshape(-1, 5))
    datastring = '\n'.join([''.join(line) for line in data])

    return header + datastring

def read_yrec_structure(f):
    '''
    Read structure file produced by YREC
    '''
    q = np.array(pd.read_csv(f, nrows=15, names=['', '', '', '', '', '', ''], delim_whitespace=True))
    info = {'M': float(q[1,2]), 'R': float(q[2,2]), 'L': float(q[4, 2]), 'Teff': float(q[3,2]),
            'stellar_age': float(q[5,2]), 'α': float(q[6, 3]), 'X': float(q[7, 2]), 'Z': float(q[8, 2])}
    profiles =  pd.read_csv(f, delim_whitespace=True, skiprows=17, names=YREC_NAMES)
    profiles['m'] = profiles['m/M'] * info['M']
    profiles['r'] = profiles['r/R'] * info['R']
    return info, profiles

def read_yrec_track(f):
    '''
    Read track summary file produced by YREC
    '''
    return pd.read_csv(f, delim_whitespace=True, skiprows=9, names=YREC_TRACK_NAMES)

def read_yrec_history(f):
    '''
    Read track history file produced by YREC
    '''
    h = pd.read_csv(f, delim_whitespace=True, skiprows=0, names=[
        'model_number', 'stellar_mass', 'R/Rsun', 'Teff', 'logL/Lsun', 'stellar_age', 'Y', 'Zsurf', 'Xc', 'Δν_scale', 'α'
    ], dtype={'model_number': str})
    if h['model_number'].iloc[0][0] != '0':
        h = pd.read_csv(f, delim_whitespace=True, skiprows=0, names=[
        'model_number', '', 'stellar_mass', 'R/Rsun', 'Teff', 'logL/Lsun', 'stellar_age', 'Y', 'Zsurf', 'Xc', 'Δν_scale', 'α'
    ], dtype={'model_number': str})
    return h

def read_osc(file):

	header = np.loadtxt(file, max_rows=1)
	body = np.loadtxt(file, skiprows=1)

	assert int(header[0]) == body.shape[0], "filesize mismatch with file header"

	info = {k: v for k, v in zip(OSC_GLOB_NAMES, header[1:])}
	profile = {k: v for k, v in zip(OSC_NAMES, body.T)}

	return info, profile