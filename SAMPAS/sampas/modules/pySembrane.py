"""
pySembrane - Python Membrane Separation module
분리막 공정 해석을 위한 모듈 (stub implementation)
"""

import numpy as np


# ─────────────────────────────────────────────
#  기본 막 성능 지표 (Basic Membrane Performance)
# ─────────────────────────────────────────────

def permeability_to_permeance(P_i, thickness_m):
    """
    투과도(Permeability) → 투과율(Permeance) 변환
    Parameters
    ----------
    P_i         : float - 투과도 [Barrer]  (1 Barrer = 1e-10 cm³(STP)·cm / cm²·s·cmHg)
    thickness_m : float - 막 두께 [m]
    Returns
    -------
    GPU : float - 투과율 [GPU]  (1 GPU = 1e-6 cm³(STP) / cm²·s·cmHg)
    """
    thickness_cm = thickness_m * 100
    GPU = P_i / thickness_cm   # 1 Barrer / cm = 1 GPU
    return round(GPU, 4)


def ideal_selectivity(P_A, P_B):
    """
    이상 선택도 (Ideal Selectivity / Permselectivity)
    Parameters
    ----------
    P_A : float - 성분 A 투과도 [Barrer]
    P_B : float - 성분 B 투과도 [Barrer]
    Returns
    -------
    alpha_AB : float - A/B 선택도
    """
    return round(P_A / P_B, 4)


def robeson_upper_bound(alpha_AB, k=1.0, n=1.0):
    """
    Robeson Upper Bound (CO2/N2 등 기체쌍 성능 한계 곡선)
    Parameters
    ----------
    alpha_AB : float or array - 선택도
    k, n     : float          - 가스 쌍별 경험 계수
    Returns
    -------
    P_max : 상한 곡선 투과도 [Barrer]
    """
    alpha = np.asarray(alpha_AB, dtype=float)
    return k * (alpha ** (-n))


# ─────────────────────────────────────────────
#  기체 투과 모델 (Gas Permeation Models)
# ─────────────────────────────────────────────

def cross_flow_permeation(feed_flow, feed_comp, permeances, pressures,
                          n_stages=10):
    """
    Cross-flow 기체 분리막 모듈 시뮬레이션 (1성분계 근사)
    Parameters
    ----------
    feed_flow    : float - 공급 유량 [mol/s]
    feed_comp    : dict  - {'CO2': 0.15, 'N2': 0.85}
    permeances   : dict  - {'CO2': 500, 'N2': 10}  [GPU]
    pressures    : tuple - (P_feed_bar, P_permeate_bar)
    n_stages     : int   - 계산 단계 수
    Returns
    -------
    results : dict
    """
    P_f, P_p = pressures
    comps = list(feed_comp.keys())
    y     = np.array([feed_comp[c] for c in comps])
    Q     = np.array([permeances.get(c, 1.0) for c in comps])  # GPU

    # --- 단순 1-stage 근사 ---
    J = Q * (y * P_f - y * P_p)   # 각 성분 flux [GPU·bar → cm³/cm²/s/cmHg 단위 주의]
    J = np.maximum(J, 0)
    J_total = J.sum()

    permeate_comp = (J / J_total) if J_total > 0 else y
    stage_cut     = J_total / (Q.mean() * P_f + 1e-9) * 0.1   # 근사

    result = {}
    for i, c in enumerate(comps):
        result[f"permeate_{c}"] = round(float(permeate_comp[i]), 4)
    result["stage_cut_approx"] = round(float(np.clip(stage_cut, 0, 1)), 4)
    return result


def hollow_fiber_module(feed_pressure, permeate_pressure,
                        fiber_length, inner_radius, outer_radius,
                        n_fibers, permeance):
    """
    중공사막(Hollow Fiber) 모듈 성능 계산
    Parameters
    ----------
    feed_pressure, permeate_pressure : float [bar]
    fiber_length     : float [m]
    inner_radius     : float [m]
    outer_radius     : float [m]
    n_fibers         : int
    permeance        : float [GPU]
    Returns
    -------
    dict - 유효 막 면적, 예상 투과 유량
    """
    A_fiber = 2 * np.pi * outer_radius * fiber_length   # 외표면 기준
    A_total = A_fiber * n_fibers                         # [m²]

    # GPU → mol/(m²·s·Pa)  변환: 1 GPU ≈ 3.35e-10 mol/(m²·s·Pa)
    P_SI = permeance * 3.35e-10
    dP   = (feed_pressure - permeate_pressure) * 1e5    # bar → Pa
    flux = P_SI * dP                                     # [mol/(m²·s)]
    total_flux = flux * A_total                          # [mol/s]

    return {
        "membrane_area_m2":     round(A_total, 4),
        "flux_mol_m2_s":        round(float(flux), 8),
        "total_permeate_mol_s": round(float(total_flux), 6),
    }


# ─────────────────────────────────────────────
#  분리막 물성 분석
# ─────────────────────────────────────────────

def solution_diffusion_permeability(D, S):
    """
    Solution-Diffusion 모델: P = D × S
    Parameters
    ----------
    D : float - 확산 계수 [cm²/s]
    S : float - 용해도 계수 [cm³(STP)/(cm³·cmHg)]
    Returns
    -------
    P : float - 투과도 [Barrer]
    """
    P_cgs = D * S                            # cm²/s × cm³(STP)/(cm³·cmHg)
    P_barrer = P_cgs / 1e-10                 # Barrer
    return round(P_barrer, 4)


def membrane_flux_temperature(J_ref, T_ref, T, Ea_kJ_mol=30.0):
    """
    Arrhenius 온도 의존성에 따른 막 투과 플럭스 보정
    Parameters
    ----------
    J_ref     : float - 기준 온도에서 플럭스
    T_ref, T  : float - 기준/계산 온도 [K]
    Ea_kJ_mol : float - 활성화 에너지 [kJ/mol]
    Returns
    -------
    J : float - 보정된 플럭스
    """
    R  = 8.314e-3   # kJ/(mol·K)
    Ea = Ea_kJ_mol
    J  = J_ref * np.exp(-Ea / R * (1.0 / T - 1.0 / T_ref))
    return round(float(J), 6)


def concentration_polarization_factor(k_mass, P_mem):
    """
    농도 분극 계수 (Concentration Polarization Factor)
    Parameters
    ----------
    k_mass : float - 물질 전달 계수 [m/s]
    P_mem  : float - 막 투과도 (같은 단위)
    Returns
    -------
    CP : float - 농도 분극 계수 (>1 : 분극 발생)
    """
    CP = np.exp(P_mem / k_mass)
    return round(float(CP), 4)
