# AxialMotorFixedParam.py
import math

MU0 = 4 * math.pi * 1e-7  # H/m


class AxialMotorDesign:
    """
    Physics-correct axial flux motor calculator that supports:
    - RPM or electrical frequency input (pick one)
    - AC line RMS or DC bus input (with modulation index)
    - Auto-select turns from voltage, or use user-provided fixed turns
    - Dual-plate torque doubling
    - ESC limits: phase-current limit, DC current estimate, voltage utilization
    - Legacy getters preserved where reasonable for compatibility
    """

    # ----------------------------- init -------------------------------------
    def __init__(
        self,
        coils,
        input_voltage,
        outer_radius,
        desired_torque,
        esc_frequency=None,                # electrical Hz (if provided)
        turns=None,                        # fixed turns per phase (series). If None, auto-computed
        magnetic_flux_density=0.6,         # average air-gap flux density [T]
        poles=None,                        # optional explicit poles (even, >=4)
        winding_factor=0.92,               # typical 0.85..0.96
        mechanical_rpm=None,               # if given, overrides esc_frequency
        modulation_index=0.95,             # inverter modulation (0..1); used if input_is_vdc=True
        input_is_vdc=False,                # whether input_voltage is DC bus (else: line-line RMS)
        dual_plate=False,                  # dual rotor/dual airgap torque (×2)
        phase_current_limit=None,          # ESC phase current continuous limit [A]
        dc_current_limit=None,             # battery/DC current limit [A] (optional)
        esc_freq_max=None,                 # ESC electrical frequency capability [Hz] (optional)
    ):
        # ---- user inputs & legacy compatibility ----
        self.coils = self.validate_coils(int(round(coils)))
        self.input_voltage = float(input_voltage)     # If input_is_vdc==False: line-line RMS. Else: DC bus.
        self.outer_radius = float(outer_radius)
        self.inner_radius = float(outer_radius) * 0.58
        self.desired_torque = float(desired_torque)
        self.turns = None if turns is None or turns == "" else float(turns)
        self.Bavg = float(magnetic_flux_density)
        self.kw = float(winding_factor)
        self.modulation_index = max(0.0, min(1.0, float(modulation_index)))
        self.input_is_vdc = bool(input_is_vdc)
        self.dual_plate = bool(dual_plate)

        # Pole count: prefer explicit; else legacy heuristic
        if poles is not None:
            poles = int(round(poles))
            if poles % 2 != 0 or poles < 4:
                raise ValueError("Poles must be an even number ≥ 4.")
            self.poles = poles
        else:
            self.poles = self.calculate_poles()  # legacy fallback

        # Frequency / speed: prefer mechanical_rpm if provided
        if mechanical_rpm is not None and str(mechanical_rpm).strip() != "":
            self.mechanical_rpm = float(mechanical_rpm)
            self.electrical_frequency_hz = (self.poles / 2.0) * (self.mechanical_rpm / 60.0)
        elif esc_frequency is not None and str(esc_frequency).strip() != "":
            self.electrical_frequency_hz = float(esc_frequency)
            self.mechanical_rpm = (120.0 * self.electrical_frequency_hz) / self.poles
        else:
            raise ValueError("Provide either electrical frequency (Hz) or mechanical RPM.")

        # Optional ESC limits
        self.phase_current_limit = None if phase_current_limit in (None, "") else float(phase_current_limit)
        self.dc_current_limit = None if dc_current_limit in (None, "") else float(dc_current_limit)
        self.esc_freq_max = None if esc_freq_max in (None, "") else float(esc_freq_max)

        # Legacy fields used by the original GUI
        self.magnets = self.calculate_magnets()
        self.min_rpm = self.mechanical_rpm  # legacy label in GUI

    # ----------------------- legacy helpers kept -----------------------------
    def validate_coils(self, coils):
        if coils % 3 != 0:
            raise ValueError("The number of coils must be divisible by 3 (3-phase).")
        return coils

    def calculate_poles(self):
        """
        Legacy heuristic: two poles per three coils.
        Not generally valid, but preserved when 'poles' not provided.
        """
        return (self.coils // 3) * 2

    def calculate_magnets(self):
        """
        Legacy heuristic: magnets ≈ 2*poles, nudged to be divisible by 4.
        """
        magnets = self.poles * 2
        while magnets % 4 != 0:
            magnets += 1
        return magnets

    def calculate_min_rpm(self):
        """
        Legacy name; returns mechanical RPM implied by current electrical Hz and poles.
        """
        return (120.0 * self.electrical_frequency_hz) / self.poles

    # ------------------------------ geometry --------------------------------
    def calculate_rotor_area(self):
        return math.pi * (self.outer_radius**2 - self.inner_radius**2)

    def _r_av(self):
        return 0.5 * (self.outer_radius + self.inner_radius)

    def _pole_area(self):
        return self.calculate_rotor_area() / self.poles

    # --------------------------- magnetic basics -----------------------------
    def calculate_peak_flux_density(self):
        """Convert average gap B to peak fundamental (sine): B_pk = (π/2)*B_avg"""
        return (math.pi / 2.0) * self.Bavg

    def _flux_per_pole(self):
        """Φ ≈ B_avg * A_pole (first-order axial flux assumption)"""
        return self.Bavg * self._pole_area()

    # --------------------------- inverter voltage ----------------------------
    def _available_line_rms(self):
        """
        Available line-to-line RMS fundamental from the inverter.
        If input is Vdc, convert to approx fundamental RMS (~0.612*m*Vdc).
        """
        if self.input_is_vdc:
            return 0.612 * self.modulation_index * self.input_voltage
        return self.input_voltage  # already line-line RMS

    def _phase_voltage_rms(self):
        return self._available_line_rms() / math.sqrt(3.0)

    # ----------------------------- EMF & turns -------------------------------
    def _emf_fit_turns(self):
        """
        Turns per phase derived from EMF fit (sinusoidal):
        E_ph,rms ≈ 4.44 f_e N Φ k_w  ->  N = E_ph / (4.44 f_e Φ k_w)
        """
        Eph = self._phase_voltage_rms()
        fe = self.electrical_frequency_hz
        Phi = self._flux_per_pole()
        denom = 4.44 * fe * Phi * self.kw
        if denom <= 0:
            return float("nan")
        return Eph / denom

    def calculate_number_of_coil_turns(self):
        """Use fixed turns if provided; else auto from voltage."""
        return float(self.turns) if self.turns is not None else self._emf_fit_turns()

    def _flux_linkage(self):
        """λ_f = N * k_w * Φ  (Wb-turn)"""
        N = self.calculate_number_of_coil_turns()
        return N * self.kw * self._flux_per_pole()

    # -------------------------- torque & current -----------------------------
    def _kt_Nm_per_A_single_plate(self):
        """Torque constant for single plate (Id≈0): Kt = (3/2) * p_pairs * λ_f"""
        p_pairs = self.poles // 2
        return 1.5 * p_pairs * self._flux_linkage()

    def _kt_effective(self):
        """Effective Kt, including dual-plate multiplier."""
        mult = 2.0 if self.dual_plate else 1.0
        return self._kt_Nm_per_A_single_plate() * mult

    def calculate_required_current(self):
        """
        Phase current needed to achieve desired torque at Id≈0:
        Iq = T / Kt_effective
        """
        Kt = self._kt_effective()
        if Kt <= 0:
            return float("nan")
        return self.desired_torque / Kt

    def calculate_total_torque(self):
        """
        Predict torque at the required current (will match desired_torque by construction).
        Kept for legacy API symmetry.
        """
        Kt = self._kt_effective()
        Iq = self.calculate_required_current()
        return Kt * Iq

    # ----------------------------- sanity checks -----------------------------
    def calculate_airgap_shear_stress(self):
        """τ = T / (A_rotor * r_av)  (based on desired torque)"""
        A = self.calculate_rotor_area()
        r_av = self._r_av()
        return self.desired_torque / (A * r_av)

    def _shear_stress_limit(self, C=0.25):
        """Heuristic ceiling: τ_max ≈ C * (B_avg^2 / (2 μ0))"""
        return C * (self.Bavg**2) / (2.0 * MU0)

    def _voltage_utilization(self):
        """
        Ratio of predicted EMF to available fundamental.
        >1 means over-voltage at target RPM with current N.
        """
        N = self.calculate_number_of_coil_turns()
        Eph = 4.44 * self.electrical_frequency_hz * N * self._flux_per_pole() * self.kw
        Vll_pred = math.sqrt(3.0) * Eph
        Vll_avail = self._available_line_rms()
        if Vll_avail <= 0:
            return float("inf")
        return Vll_pred / Vll_avail

    def _max_rpm_at_vlimit(self):
        """
        With current turns N fixed, scale RPM down until utilization == 1.
        (If in auto-turns mode, N was chosen from voltage for THIS speed, so U≈1 and rpm_max≈current RPM.)
        """
        U = self._voltage_utilization()
        if not math.isfinite(U) or U <= 0:
            return float("nan")
        return self.mechanical_rpm / max(U, 1e-9)

    def _mechanical_power_W(self):
        omega = 2.0 * math.pi * (self.mechanical_rpm / 60.0)
        return self.desired_torque * omega

    def _estimated_dc_current(self, assumed_efficiency=0.9):
        """
        Rough DC current estimate from mechanical power and Vdc.
        Only meaningful when input_is_vdc=True (or we can back-calc Vdc from RMS).
        """
        if self.input_is_vdc:
            Vdc = self.input_voltage
        else:
            # Back-calc a Vdc estimate from line RMS and modulation
            Vdc = self._available_line_rms() / max(0.612 * self.modulation_index, 1e-9)
        Pm = self._mechanical_power_W()
        if Vdc <= 0 or assumed_efficiency <= 0:
            return float("nan")
        return Pm / (assumed_efficiency * Vdc)

    # ------------------------------ formatting -------------------------------
    def _fmt(self, x):
        try:
            return f"{x:.6f}"
        except Exception:
            return str(x)

    def get_calculations(self):
        """
        Returns a dict of strings; GUI will pick the ones it knows.
        """
        A = self.calculate_rotor_area()
        r_av = self._r_av()
        Bpk = self.calculate_peak_flux_density()
        Phi = self._flux_per_pole()
        N = self.calculate_number_of_coil_turns()
        lam = self._flux_linkage()
        Kt_single = self._kt_Nm_per_A_single_plate()
        Kt_eff = self._kt_effective()
        Ireq = self.calculate_required_current()
        Tpred = self.calculate_total_torque()
        tau_des = self.calculate_airgap_shear_stress()
        tau_lim = self._shear_stress_limit()
        U = self._voltage_utilization()
        rpm_vmax = self._max_rpm_at_vlimit()
        Pm = self._mechanical_power_W()
        Idc_est = self._estimated_dc_current()

        # Limit checks
        v_pass = (U <= 1.0)
        i_pass = True
        Tmax = None
        if self.phase_current_limit is not None:
            Tmax = Kt_eff * self.phase_current_limit
            i_pass = (Ireq <= self.phase_current_limit)

        esc_f_pass = True
        if self.esc_freq_max is not None:
            esc_f_pass = (self.electrical_frequency_hz <= self.esc_freq_max)

        dc_pass = True
        if (self.dc_current_limit is not None) and math.isfinite(Idc_est):
            dc_pass = (Idc_est <= self.dc_current_limit)

        mode = "Turns-limited (fixed N)" if self.turns is not None else "Voltage-limited (auto N)"

        out = {
            # Legacy-ish fields the old GUI used
            "Number of Poles": self._fmt(self.poles),
            "Number of Magnets": self._fmt(self.magnets),
            "Inner Radius (m)": self._fmt(self.inner_radius),
            "Outer Radius (m)": self._fmt(self.outer_radius),
            "Rotor Area (m^2)": self._fmt(A),
            "Airgap Shear Stress (N/m^2)": self._fmt(tau_des),
            "Minimum RPM": self._fmt(self.mechanical_rpm),
            "Peak Flux Density (T)": self._fmt(Bpk),
            "Number of Coil Turns": self._fmt(N),
            "Total Torque (N-m)": self._fmt(Tpred),
            "Required Current (A)": self._fmt(Ireq),

            # Clear modern outputs
            "Electrical Frequency (Hz)": self._fmt(self.electrical_frequency_hz),
            "Mechanical RPM": self._fmt(self.mechanical_rpm),
            "Flux per Pole (Wb)": self._fmt(Phi),
            "Winding Factor": self._fmt(self.kw),
            "Torque Constant Kt (N·m/A)": self._fmt(Kt_eff),
            "Back-EMF Const Ke_phase_peak (V·s/rad)": self._fmt(lam),
            "Voltage Utilization (V_emf/V_avail)": self._fmt(U),
            "Max RPM @ V-limit (fixed N)": self._fmt(rpm_vmax),
            "Power Mechanical (W)": self._fmt(Pm),
            "Estimated DC Current (A)": self._fmt(Idc_est),
            "Shear Stress Heuristic Limit (N/m^2)": self._fmt(tau_lim),
            "Dual Plate Enabled": str(self.dual_plate),
            "Mode": mode,

            # Pass/fail summaries
            "V-limit Pass": "YES" if v_pass else "NO",
            "I-limit Pass": "—" if self.phase_current_limit is None else ("YES" if i_pass else "NO"),
            "ESC f_e Pass": "—" if self.esc_freq_max is None else ("YES" if esc_f_pass else "NO"),
            "DC-limit Pass": "—" if self.dc_current_limit is None or not math.isfinite(Idc_est) else ("YES" if dc_pass else "NO"),
            "Max Torque @ I_limit (N-m)": "—" if Tmax is None else self._fmt(Tmax),
        }
        return out
