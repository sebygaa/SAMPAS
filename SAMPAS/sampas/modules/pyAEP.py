"""
pyAEP - Python Adsorption Equilibrium & Process module
흡착 공정 해석을 위한 모듈 (stub implementation)
"""

import numpy as np


# ─────────────────────────────────────────────
#  등온 흡착 모델 (Adsorption Isotherm Models)
# ─────────────────────────────────────────────

def langmuir_isotherm(P, q_max, K_L):
    """
    Langmuir 등온 흡착 모델
    Parameters
    ----------
    P     : float or array  - 압력 [bar]
    q_max : float           - 최대 흡착량 [mol/kg]
    K_L   : float           - Langmuir 상수 [1/bar]
    Returns
    -------
    q : 흡착량 [mol/kg]
    """
    P = np.asarray(P, dtype=float)
    return (q_max * K_L * P) / (1 + K_L * P)


def freundlich_isotherm(P, K_F, n):
    """
    Freundlich 등온 흡착 모델
    Parameters
    ----------
    P   : float or array - 압력 [bar]
    K_F : float          - Freundlich 계수
    n   : float          - Freundlich 지수
    Returns
    -------
    q : 흡착량 [mol/kg]
    """
    P = np.asarray(P, dtype=float)
    return K_F * (P ** (1.0 / n))


def dual_site_langmuir(P, q1, K1, q2, K2):
    """
    Dual-Site Langmuir (DSL) 모델
    Parameters
    ----------
    P, q1, K1, q2, K2 : 각 사이트의 최대 흡착량 및 Langmuir 상수
    Returns
    -------
    q : 흡착량 [mol/kg]
    """
    P = np.asarray(P, dtype=float)
    return (q1 * K1 * P) / (1 + K1 * P) + (q2 * K2 * P) / (1 + K2 * P)


# ─────────────────────────────────────────────
#  PSA 공정 시뮬레이션 (Pressure Swing Adsorption)
# ─────────────────────────────────────────────

def psa_simple_cycle(feed_composition, pressures, cycle_time,
                     isotherm_func, isotherm_params):
    """
    단순화된 2-bed PSA 사이클 시뮬레이션 (stub)
    Parameters
    ----------
    feed_composition : dict  - {'CO2': 0.15, 'N2': 0.85} 형태
    pressures        : tuple - (P_high, P_low) [bar]
    cycle_time       : float - 사이클 시간 [s]
    isotherm_func    : callable
    isotherm_params  : dict
    Returns
    -------
    results : dict - 회수율, 순도, 생산성 등
    """
    P_high, P_low = pressures
    q_high = isotherm_func(P_high, **isotherm_params)
    q_low  = isotherm_func(P_low,  **isotherm_params)
    working_capacity = q_high - q_low

    # --- 간략 계산 (실제 공정은 PDE 기반 시뮬레이션 필요) ---
    purity     = 0.95 + 0.02 * (P_high / (P_high + P_low))   # placeholder
    recovery   = 0.80 + 0.05 * (working_capacity / (q_high + 1e-9))
    productivity = working_capacity / cycle_time

    return {
        "working_capacity_mol_kg": round(float(working_capacity), 4),
        "purity_%":                round(float(purity * 100), 2),
        "recovery_%":              round(float(recovery * 100), 2),
        "productivity_mol_kg_s":   round(float(productivity), 6),
    }


def tsa_energy_requirement(T_ads, T_des, q_working, delta_H_ads, Cp_solid, mass_adsorbent):
    """
    TSA(Temperature Swing Adsorption) 에너지 요구량 계산
    Parameters
    ----------
    T_ads, T_des   : float - 흡착/탈착 온도 [K]
    q_working      : float - 실효 흡착량 [mol/kg]
    delta_H_ads    : float - 흡착 엔탈피 [kJ/mol]
    Cp_solid       : float - 흡착제 열용량 [kJ/(kg·K)]
    mass_adsorbent : float - 흡착제 질량 [kg]
    Returns
    -------
    dict with energy breakdown [kJ]
    """
    dT = abs(T_des - T_ads)
    Q_sensible  = mass_adsorbent * Cp_solid * dT
    Q_desorption = mass_adsorbent * q_working * abs(delta_H_ads)
    Q_total = Q_sensible + Q_desorption

    return {
        "Q_sensible_kJ":   round(Q_sensible, 2),
        "Q_desorption_kJ": round(Q_desorption, 2),
        "Q_total_kJ":      round(Q_total, 2),
    }


# ─────────────────────────────────────────────
#  흡착제 특성 분석
# ─────────────────────────────────────────────

def BET_surface_area(P_P0_array, n_ads_array):
    """
    BET 비표면적 계산
    Parameters
    ----------
    P_P0_array  : array - 상대압력 (P/P0)
    n_ads_array : array - 흡착량 [cm³(STP)/g]
    Returns
    -------
    dict - BET surface area [m²/g], C constant, monolayer capacity
    """
    P_P0 = np.asarray(P_P0_array)
    n    = np.asarray(n_ads_array)

    mask = (P_P0 > 0.05) & (P_P0 < 0.35)
    x = P_P0[mask]
    y = x / (n[mask] * (1 - x))

    coeffs   = np.polyfit(x, y, 1)
    slope, intercept = coeffs
    n_m = 1.0 / (slope + intercept)
    C   = 1 + slope / intercept
    N_A = 6.022e23
    sigma = 0.162e-18   # N2 분자 단면적 [m²]
    S_BET = n_m / 22400 * N_A * sigma * 1e4   # [m²/g]  (STP, 1g)

    return {
        "BET_surface_area_m2g": round(float(S_BET), 1),
        "C_constant":           round(float(C), 1),
        "nm_cm3g":              round(float(n_m), 4),
    }
