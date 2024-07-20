import math

class AxialMotorDesign:
    def __init__(self, coils, input_voltage, outer_radius, desired_torque, esc_frequency, magnetic_flux_density=0.6):
        self.coils = self.validate_coils(coils)
        self.input_voltage = input_voltage
        self.outer_radius = outer_radius
        self.inner_radius = outer_radius * 0.58  # Optimal ratio
        self.desired_torque = desired_torque
        self.esc_frequency = esc_frequency
        self.magnetic_flux_density = magnetic_flux_density  # Adjustable parameter
        self.poles = self.calculate_poles()
        self.magnets = self.calculate_magnets()
        self.min_rpm = self.calculate_min_rpm()

    def validate_coils(self, coils):
        """
        Validate that the number of coils is divisible by 3 for the 3-phase design.
        """
        if coils % 3 != 0:
            raise ValueError("The number of coils must be divisible by 3.")
        return coils

    def calculate_poles(self):
        """
        Determine the appropriate number of poles based on the number of coils.
        """
        return (self.coils // 3) * 2  # Two poles per three coils

    def calculate_magnets(self):
        """
        Determine the appropriate number of magnets based on the poles.
        The number of magnets should be the next number up that is divisible by 4.
        """
        magnets = self.poles * 2
        while magnets % 4 != 0:
            magnets += 1
        return magnets

    def calculate_min_rpm(self):
        """
        Calculate the minimum RPM based on the ESC frequency and the number of poles.
        """
        return (self.esc_frequency * 60) / (self.poles / 2)

    def calculate_rotor_area(self):
        """
        Calculate the active surface area of the rotor.
        Equation: A_rotor = π * (r_o^2 - r_i^2)
        """
        return math.pi * (self.outer_radius**2 - self.inner_radius**2)

    def calculate_airgap_shear_stress(self):
        """
        Calculate the airgap shear stress (τ).
        Equation: τ = T / (A_rotor * r_av)
        """
        A_rotor = self.calculate_rotor_area()
        r_av = (self.outer_radius + self.inner_radius) / 2
        return self.desired_torque / (A_rotor * r_av)

    def calculate_peak_flux_density(self):
        """
        Calculate the peak flux density (B_m).
        """
        return self.magnetic_flux_density / (2 / math.pi)

    def calculate_number_of_coil_turns(self):
        """
        Calculate the number of turns per coil.
        Equation: N_ph = e_ph / (A_coil * ω_e * B_m)
        """
        A_rotor = self.calculate_rotor_area()
        A_coil = A_rotor / self.coils  # Assuming the coil area is the rotor area divided by the number of coils
        B_m = self.calculate_peak_flux_density()
        omega_e = self.esc_frequency * 2 * math.pi  # Convert to rad/s
        e_ph = self.input_voltage / math.sqrt(3)  # Line-to-neutral voltage for Y connection
        N_ph = e_ph / (A_coil * omega_e * B_m)
        return N_ph

    def calculate_required_current(self):
        """
        Calculate the required current to produce the desired torque.
        """
        T_per_phase = self.desired_torque / 3  # Assume torque is equally distributed in three phases
        B_m = self.calculate_peak_flux_density()
        r_av = (self.outer_radius + self.inner_radius) / 2
        Z = self.calculate_number_of_coil_turns()
        required_current = T_per_phase / (B_m * Z * r_av)
        return required_current

    def calculate_total_torque(self):
        """
        Calculate the total torque based on design parameters.
        """
        B_m = self.calculate_peak_flux_density()
        A_rotor = self.calculate_rotor_area()
        r_av = (self.outer_radius + self.inner_radius) / 2
        τ = self.calculate_airgap_shear_stress()
        T = τ * A_rotor * r_av
        return T

    def format_value(self, value):
        return f"{value:.5f}"

    def get_calculations(self):
        """
        Get all calculations as a dictionary.
        """
        calculations = {
            "Number of Poles": self.format_value(self.poles),
            "Number of Magnets": self.format_value(self.magnets),
            "Inner Radius (m)": self.format_value(self.inner_radius),
            "Outer Radius (m)": self.format_value(self.outer_radius),
            "Rotor Area (m^2)": self.format_value(self.calculate_rotor_area()),
            "Airgap Shear Stress (N/m^2)": self.format_value(self.calculate_airgap_shear_stress()),
            "Minimum RPM": self.format_value(self.min_rpm),
            "Peak Flux Density (T)": self.format_value(self.calculate_peak_flux_density()),
            "Number of Coil Turns": self.format_value(self.calculate_number_of_coil_turns()),
            "Total Torque (N-m)": self.format_value(self.calculate_total_torque()),
            "Required Current (A)": self.format_value(self.calculate_required_current())
        }
        return calculations
