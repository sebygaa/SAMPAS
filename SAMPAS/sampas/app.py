"""
SAMPAS - Simulation-Aided Material & Processes Analysis System
메인 GUI 애플리케이션
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import sys
import os

# 모듈 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sampas.modules import pyAEP, pySembrane

# ═══════════════════════════════════════════
#  색상 & 스타일 테마
# ═══════════════════════════════════════════
THEME = {
    "bg":         "#0D1117",
    "panel":      "#161B22",
    "border":     "#30363D",
    "accent":     "#58A6FF",
    "accent2":    "#3FB950",
    "accent3":    "#F78166",
    "text":       "#C9D1D9",
    "text_dim":   "#8B949E",
    "input_bg":   "#21262D",
    "btn":        "#238636",
    "btn_hover":  "#2EA043",
    "header_bg":  "#1C2128",
}

APP_VERSION = "0.1.0-alpha"
APP_TITLE   = f"SAMPAS v{APP_VERSION}"


# ═══════════════════════════════════════════
#  유틸: 결과 포맷터
# ═══════════════════════════════════════════

def format_result(result_dict: dict) -> str:
    lines = ["─" * 42]
    for k, v in result_dict.items():
        lines.append(f"  {k:<30} {v}")
    lines.append("─" * 42)
    return "\n".join(lines)


# ═══════════════════════════════════════════
#  흡착 공정 탭 (pyAEP)
# ═══════════════════════════════════════════

class AdsorptionTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        # ── 왼쪽: 기능 선택 패널
        left = tk.Frame(self, bg=THEME["panel"], width=220)
        left.pack(side="left", fill="y", padx=(8, 4), pady=8)
        left.pack_propagate(False)

        tk.Label(left, text="pyAEP Functions", bg=THEME["panel"],
                 fg=THEME["accent"], font=("Consolas", 11, "bold")).pack(pady=(12, 6))

        self._func_var = tk.StringVar(value="langmuir")
        funcs = [
            ("Langmuir Isotherm",       "langmuir"),
            ("Freundlich Isotherm",     "freundlich"),
            ("Dual-Site Langmuir",      "dsl"),
            ("PSA Simple Cycle",        "psa"),
            ("TSA Energy Requirement",  "tsa"),
            ("BET Surface Area",        "bet"),
        ]
        for label, val in funcs:
            rb = tk.Radiobutton(
                left, text=label, variable=self._func_var, value=val,
                bg=THEME["panel"], fg=THEME["text"],
                selectcolor=THEME["input_bg"],
                activebackground=THEME["panel"],
                font=("Consolas", 9),
                command=self._on_func_change,
            )
            rb.pack(anchor="w", padx=10, pady=1)

        # ── 오른쪽: 입력 + 출력
        right = tk.Frame(self, bg=THEME["bg"])
        right.pack(side="left", fill="both", expand=True, padx=(4, 8), pady=8)

        # 입력 영역
        input_frame = tk.LabelFrame(
            right, text=" Input Parameters ", bg=THEME["bg"],
            fg=THEME["accent"], font=("Consolas", 9), bd=1,
            relief="solid", highlightbackground=THEME["border"]
        )
        input_frame.pack(fill="x", pady=(0, 6))

        self._input_frame = input_frame
        self._entries = {}
        self._build_inputs()

        # 실행 버튼
        run_btn = tk.Button(
            right, text="▶  Run Calculation",
            bg=THEME["btn"], fg="white",
            activebackground=THEME["btn_hover"],
            font=("Consolas", 10, "bold"),
            relief="flat", cursor="hand2",
            command=self._run,
        )
        run_btn.pack(fill="x", pady=(0, 6))

        # 결과 출력
        result_frame = tk.LabelFrame(
            right, text=" Results ", bg=THEME["bg"],
            fg=THEME["accent2"], font=("Consolas", 9), bd=1, relief="solid"
        )
        result_frame.pack(fill="both", expand=True)

        self._result_box = scrolledtext.ScrolledText(
            result_frame, bg=THEME["input_bg"], fg=THEME["text"],
            font=("Consolas", 10), relief="flat", state="disabled", height=10
        )
        self._result_box.pack(fill="both", expand=True, padx=4, pady=4)

    # ── 선택된 함수에 맞게 입력 필드 재구성
    FUNC_PARAMS = {
        "langmuir":   [("Pressure P [bar]", "1.0"),
                       ("q_max [mol/kg]", "5.0"), ("K_L [1/bar]", "0.5")],
        "freundlich": [("Pressure P [bar]", "1.0"),
                       ("K_F", "2.0"), ("n", "2.0")],
        "dsl":        [("Pressure P [bar]", "1.0"),
                       ("q1 [mol/kg]", "3.0"), ("K1 [1/bar]", "0.8"),
                       ("q2 [mol/kg]", "2.0"), ("K2 [1/bar]", "0.1")],
        "psa":        [("Feed CO2 fraction", "0.15"),
                       ("P_high [bar]", "5.0"), ("P_low [bar]", "0.1"),
                       ("Cycle time [s]", "300"),
                       ("q_max [mol/kg]", "5.0"), ("K_L [1/bar]", "0.5")],
        "tsa":        [("T_ads [K]", "298"), ("T_des [K]", "393"),
                       ("q_working [mol/kg]", "2.0"),
                       ("ΔH_ads [kJ/mol]", "40.0"),
                       ("Cp_solid [kJ/kg/K]", "1.0"),
                       ("Mass adsorbent [kg]", "1.0")],
        "bet":        [("P/P0 values (csv)", "0.05,0.10,0.15,0.20,0.25,0.30"),
                       ("n_ads cm³/g (csv)", "50,90,125,160,200,250")],
    }

    def _build_inputs(self):
        for w in self._input_frame.winfo_children():
            w.destroy()
        self._entries.clear()
        func = self._func_var.get()
        params = self.FUNC_PARAMS.get(func, [])
        for i, (label, default) in enumerate(params):
            row = tk.Frame(self._input_frame, bg=THEME["bg"])
            row.pack(fill="x", padx=8, pady=2)
            tk.Label(row, text=label, bg=THEME["bg"], fg=THEME["text_dim"],
                     font=("Consolas", 9), width=26, anchor="w").pack(side="left")
            e = tk.Entry(row, bg=THEME["input_bg"], fg=THEME["text"],
                         insertbackground=THEME["text"],
                         font=("Consolas", 10), relief="flat", bd=4)
            e.insert(0, default)
            e.pack(side="left", fill="x", expand=True)
            self._entries[label] = e

    def _on_func_change(self):
        self._build_inputs()

    def _run(self):
        func = self._func_var.get()
        vals = {k: v.get() for k, v in self._entries.items()}
        try:
            result = self._calculate(func, vals)
        except Exception as ex:
            messagebox.showerror("Calculation Error", str(ex))
            return
        self._show_result(result)

    def _calculate(self, func, vals):
        import numpy as np

        def fv(key):
            return float(vals[key])

        def csv(key):
            return [float(x) for x in vals[key].split(",")]

        if func == "langmuir":
            q = pyAEP.langmuir_isotherm(fv("Pressure P [bar]"),
                                        fv("q_max [mol/kg]"), fv("K_L [1/bar]"))
            return {"q [mol/kg]": round(float(q), 4)}

        elif func == "freundlich":
            q = pyAEP.freundlich_isotherm(fv("Pressure P [bar]"),
                                          fv("K_F"), fv("n"))
            return {"q [mol/kg]": round(float(q), 4)}

        elif func == "dsl":
            q = pyAEP.dual_site_langmuir(
                fv("Pressure P [bar]"),
                fv("q1 [mol/kg]"), fv("K1 [1/bar]"),
                fv("q2 [mol/kg]"), fv("K2 [1/bar]"),
            )
            return {"q_total [mol/kg]": round(float(q), 4)}

        elif func == "psa":
            iso_params = {"q_max": fv("q_max [mol/kg]"), "K_L": fv("K_L [1/bar]")}
            feed_comp  = {"CO2": fv("Feed CO2 fraction"),
                          "N2":  1.0 - fv("Feed CO2 fraction")}
            return pyAEP.psa_simple_cycle(
                feed_comp,
                (fv("P_high [bar]"), fv("P_low [bar]")),
                fv("Cycle time [s]"),
                pyAEP.langmuir_isotherm,
                iso_params,
            )

        elif func == "tsa":
            return pyAEP.tsa_energy_requirement(
                fv("T_ads [K]"), fv("T_des [K]"),
                fv("q_working [mol/kg]"), fv("ΔH_ads [kJ/mol]"),
                fv("Cp_solid [kJ/kg/K]"), fv("Mass adsorbent [kg]"),
            )

        elif func == "bet":
            return pyAEP.BET_surface_area(
                csv("P/P0 values (csv)"), csv("n_ads cm³/g (csv)")
            )

    def _show_result(self, result):
        text = format_result(result)
        self._result_box.config(state="normal")
        self._result_box.delete("1.0", "end")
        self._result_box.insert("end", text)
        self._result_box.config(state="disabled")


# ═══════════════════════════════════════════
#  분리막 공정 탭 (pySembrane)
# ═══════════════════════════════════════════

class MembraneTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        left = tk.Frame(self, bg=THEME["panel"], width=220)
        left.pack(side="left", fill="y", padx=(8, 4), pady=8)
        left.pack_propagate(False)

        tk.Label(left, text="pySembrane Functions", bg=THEME["panel"],
                 fg=THEME["accent"], font=("Consolas", 11, "bold")).pack(pady=(12, 6))

        self._func_var = tk.StringVar(value="permeance")
        funcs = [
            ("Permeability → Permeance", "permeance"),
            ("Ideal Selectivity",        "selectivity"),
            ("Cross-flow Permeation",    "crossflow"),
            ("Hollow Fiber Module",      "hollow"),
            ("Solution-Diffusion P",     "sol_diff"),
            ("T-dependent Flux",         "temp_flux"),
            ("Conc. Polarization",       "cp_factor"),
        ]
        for label, val in funcs:
            rb = tk.Radiobutton(
                left, text=label, variable=self._func_var, value=val,
                bg=THEME["panel"], fg=THEME["text"],
                selectcolor=THEME["input_bg"],
                activebackground=THEME["panel"],
                font=("Consolas", 9),
                command=self._on_func_change,
            )
            rb.pack(anchor="w", padx=10, pady=1)

        right = tk.Frame(self, bg=THEME["bg"])
        right.pack(side="left", fill="both", expand=True, padx=(4, 8), pady=8)

        input_frame = tk.LabelFrame(
            right, text=" Input Parameters ", bg=THEME["bg"],
            fg=THEME["accent"], font=("Consolas", 9), bd=1, relief="solid"
        )
        input_frame.pack(fill="x", pady=(0, 6))

        self._input_frame = input_frame
        self._entries = {}
        self._build_inputs()

        run_btn = tk.Button(
            right, text="▶  Run Calculation",
            bg=THEME["btn"], fg="white",
            activebackground=THEME["btn_hover"],
            font=("Consolas", 10, "bold"),
            relief="flat", cursor="hand2",
            command=self._run,
        )
        run_btn.pack(fill="x", pady=(0, 6))

        result_frame = tk.LabelFrame(
            right, text=" Results ", bg=THEME["bg"],
            fg=THEME["accent2"], font=("Consolas", 9), bd=1, relief="solid"
        )
        result_frame.pack(fill="both", expand=True)

        self._result_box = scrolledtext.ScrolledText(
            result_frame, bg=THEME["input_bg"], fg=THEME["text"],
            font=("Consolas", 10), relief="flat", state="disabled", height=10
        )
        self._result_box.pack(fill="both", expand=True, padx=4, pady=4)

    FUNC_PARAMS = {
        "permeance":   [("Permeability [Barrer]", "500"),
                        ("Membrane thickness [m]", "1e-6")],
        "selectivity": [("Permeability A [Barrer]", "500"),
                        ("Permeability B [Barrer]", "10")],
        "crossflow":   [("Feed CO2 fraction", "0.15"),
                        ("Permeance CO2 [GPU]", "500"),
                        ("Permeance N2 [GPU]", "10"),
                        ("Feed pressure [bar]", "5.0"),
                        ("Permeate pressure [bar]", "1.0")],
        "hollow":      [("Feed pressure [bar]", "5.0"),
                        ("Permeate pressure [bar]", "1.0"),
                        ("Fiber length [m]", "1.0"),
                        ("Inner radius [m]", "1e-4"),
                        ("Outer radius [m]", "1.5e-4"),
                        ("Number of fibers", "10000"),
                        ("Permeance [GPU]", "500")],
        "sol_diff":    [("Diffusivity D [cm²/s]", "1e-8"),
                        ("Solubility S [cm³(STP)/cm³/cmHg]", "0.02")],
        "temp_flux":   [("J_ref (ref flux)", "1.0"),
                        ("T_ref [K]", "298"),
                        ("T [K]", "323"),
                        ("Ea [kJ/mol]", "30.0")],
        "cp_factor":   [("Mass transfer coeff k [m/s]", "1e-5"),
                        ("Membrane permeance P_mem", "1e-5")],
    }

    def _build_inputs(self):
        for w in self._input_frame.winfo_children():
            w.destroy()
        self._entries.clear()
        func = self._func_var.get()
        params = self.FUNC_PARAMS.get(func, [])
        for label, default in params:
            row = tk.Frame(self._input_frame, bg=THEME["bg"])
            row.pack(fill="x", padx=8, pady=2)
            tk.Label(row, text=label, bg=THEME["bg"], fg=THEME["text_dim"],
                     font=("Consolas", 9), width=28, anchor="w").pack(side="left")
            e = tk.Entry(row, bg=THEME["input_bg"], fg=THEME["text"],
                         insertbackground=THEME["text"],
                         font=("Consolas", 10), relief="flat", bd=4)
            e.insert(0, default)
            e.pack(side="left", fill="x", expand=True)
            self._entries[label] = e

    def _on_func_change(self):
        self._build_inputs()

    def _run(self):
        func = self._func_var.get()
        vals = {k: v.get() for k, v in self._entries.items()}
        try:
            result = self._calculate(func, vals)
        except Exception as ex:
            messagebox.showerror("Calculation Error", str(ex))
            return
        self._show_result(result)

    def _calculate(self, func, vals):
        def fv(key):
            return float(vals[key])

        if func == "permeance":
            gpu = pySembrane.permeability_to_permeance(
                fv("Permeability [Barrer]"), fv("Membrane thickness [m]"))
            return {"Permeance [GPU]": gpu}

        elif func == "selectivity":
            s = pySembrane.ideal_selectivity(
                fv("Permeability A [Barrer]"), fv("Permeability B [Barrer]"))
            return {"α_A/B (ideal selectivity)": s}

        elif func == "crossflow":
            feed_comp  = {"CO2": fv("Feed CO2 fraction"),
                          "N2":  1.0 - fv("Feed CO2 fraction")}
            permeances = {"CO2": fv("Permeance CO2 [GPU]"),
                          "N2":  fv("Permeance N2 [GPU]")}
            return pySembrane.cross_flow_permeation(
                feed_flow=1.0, feed_comp=feed_comp,
                permeances=permeances,
                pressures=(fv("Feed pressure [bar]"), fv("Permeate pressure [bar]")),
            )

        elif func == "hollow":
            return pySembrane.hollow_fiber_module(
                fv("Feed pressure [bar]"), fv("Permeate pressure [bar]"),
                fv("Fiber length [m]"), fv("Inner radius [m]"),
                fv("Outer radius [m]"), int(fv("Number of fibers")),
                fv("Permeance [GPU]"),
            )

        elif func == "sol_diff":
            P = pySembrane.solution_diffusion_permeability(
                fv("Diffusivity D [cm²/s]"),
                fv("Solubility S [cm³(STP)/cm³/cmHg]"))
            return {"Permeability [Barrer]": P}

        elif func == "temp_flux":
            J = pySembrane.membrane_flux_temperature(
                fv("J_ref (ref flux)"), fv("T_ref [K]"),
                fv("T [K]"), fv("Ea [kJ/mol]"))
            return {"Corrected Flux": J}

        elif func == "cp_factor":
            cp = pySembrane.concentration_polarization_factor(
                fv("Mass transfer coeff k [m/s]"),
                fv("Membrane permeance P_mem"))
            return {"CP Factor": cp}

    def _show_result(self, result):
        text = format_result(result)
        self._result_box.config(state="normal")
        self._result_box.delete("1.0", "end")
        self._result_box.insert("end", text)
        self._result_box.config(state="disabled")


# ═══════════════════════════════════════════
#  메인 애플리케이션 윈도우
# ═══════════════════════════════════════════

class SAMPASApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("860x620")
        self.configure(bg=THEME["bg"])
        self.resizable(True, True)
        self._apply_style()
        self._build_header()
        self._build_notebook()
        self._build_statusbar()

    def _apply_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook",
                         background=THEME["bg"], borderwidth=0)
        style.configure("TNotebook.Tab",
                         background=THEME["panel"], foreground=THEME["text_dim"],
                         font=("Consolas", 10, "bold"),
                         padding=[14, 6])
        style.map("TNotebook.Tab",
                  background=[("selected", THEME["header_bg"])],
                  foreground=[("selected", THEME["accent"])])
        style.configure("TFrame", background=THEME["bg"])

    def _build_header(self):
        hdr = tk.Frame(self, bg=THEME["header_bg"], height=54)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(hdr,
                 text="⬡  SAMPAS",
                 bg=THEME["header_bg"], fg=THEME["accent"],
                 font=("Consolas", 18, "bold")).pack(side="left", padx=18)

        tk.Label(hdr,
                 text="Simulation-Aided Material & Processes Analysis System",
                 bg=THEME["header_bg"], fg=THEME["text_dim"],
                 font=("Consolas", 9)).pack(side="left")

        tk.Label(hdr, text=f"v{APP_VERSION}",
                 bg=THEME["header_bg"], fg=THEME["accent3"],
                 font=("Consolas", 9)).pack(side="right", padx=18)

    def _build_notebook(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=0, pady=0)

        # 탭 1 - 흡착 공정
        ads_tab = AdsorptionTab(nb)
        nb.add(ads_tab, text="🔵  Adsorption (pyAEP)")

        # 탭 2 - 분리막 공정
        mem_tab = MembraneTab(nb)
        nb.add(mem_tab, text="🟢  Membrane (pySembrane)")

        # 탭 3 - About
        about_tab = self._build_about_tab(nb)
        nb.add(about_tab, text="ℹ  About")

    def _build_about_tab(self, parent):
        frame = tk.Frame(parent, bg=THEME["bg"])
        content = f"""
  ╔═══════════════════════════════════════════════════════╗
  ║         SAMPAS  –  v{APP_VERSION:<10}                      ║
  ║   Simulation-Aided Material & Processes Analysis      ║
  ╠═══════════════════════════════════════════════════════╣
  ║                                                       ║
  ║  Integrated Modules                                   ║
  ║  ─────────────────────────────────────────────────    ║
  ║  • pyAEP        흡착 공정 해석 패키지                  ║
  ║    - Langmuir / Freundlich / DSL Isotherm             ║
  ║    - PSA Cycle Simulation                             ║
  ║    - TSA Energy Estimation                            ║
  ║    - BET Surface Area Analysis                        ║
  ║                                                       ║
  ║  • pySembrane   분리막 공정 해석 패키지                ║
  ║    - Permeability / Permeance / Selectivity           ║
  ║    - Cross-flow Gas Permeation                        ║
  ║    - Hollow Fiber Module Sizing                       ║
  ║    - Solution-Diffusion Model                         ║
  ║    - Concentration Polarization                       ║
  ║                                                       ║
  ║  Built with  Python + tkinter + numpy                 ║
  ╚═══════════════════════════════════════════════════════╝
"""
        tk.Label(frame, text=content, bg=THEME["bg"], fg=THEME["text"],
                 font=("Consolas", 10), justify="left").pack(padx=20, pady=20)
        return frame

    def _build_statusbar(self):
        bar = tk.Frame(self, bg=THEME["panel"], height=22)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        tk.Label(bar, text="Ready", bg=THEME["panel"], fg=THEME["text_dim"],
                 font=("Consolas", 8)).pack(side="left", padx=10)
        tk.Label(bar, text="Python " + sys.version.split()[0],
                 bg=THEME["panel"], fg=THEME["text_dim"],
                 font=("Consolas", 8)).pack(side="right", padx=10)


# ═══════════════════════════════════════════
#  진입점
# ═══════════════════════════════════════════

def main():
    app = SAMPASApp()
    app.mainloop()


if __name__ == "__main__":
    main()
