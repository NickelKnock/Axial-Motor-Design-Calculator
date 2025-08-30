# AxialMotorFixedParamGUI.py
import os, sys, math, traceback, faulthandler
faulthandler.enable()
# Helps avoid odd GPU driver issues when painting
os.environ.setdefault("QT_OPENGL", "software")

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QFormLayout, QGridLayout, QHBoxLayout, QCheckBox
)
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import Qt

from AxialMotorFixedParam import AxialMotorDesign


class VisualizationWidget(QWidget):
    """Dedicated canvas for the motor sketch; never throws out of paintEvent."""
    def __init__(self, get_num_coils_callable):
        super().__init__()
        self.get_num_coils = get_num_coils_callable
        self.setMinimumSize(340, 340)

    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            if not painter.isActive():
                return
            painter.setRenderHint(QPainter.Antialiasing)

            try:
                raw = self.get_num_coils()
                num_coils = int(str(raw).strip()) if str(raw).strip() else 12
            except Exception:
                num_coils = 12
            num_coils = max(1, num_coils)

            w = self.width() // 2
            h = self.height() // 2
            radius_outer = max(30, min(w, h) - 20)
            radius_inner = int(radius_outer * 0.58)

            painter.setPen(QPen(QColor(0, 0, 0)))
            painter.setBrush(QColor(200, 200, 200))
            painter.drawEllipse(w - radius_outer, h - radius_outer, 2 * radius_outer, 2 * radius_outer)
            painter.drawEllipse(w - radius_inner, h - radius_inner, 2 * radius_inner, 2 * radius_inner)

            painter.setBrush(QColor(150, 150, 150))
            angle_step = 360.0 / float(num_coils)
            max_markers = min(num_coils, 720)  # cap to avoid silly perf
            for i in range(max_markers):
                angle_deg = i * angle_step
                x = w + radius_outer * 0.9 * math.cos(math.radians(angle_deg))
                y = h + radius_outer * 0.9 * math.sin(math.radians(angle_deg))
                painter.drawEllipse(int(x - 5), int(y - 5), 10, 10)
        except Exception:
            # swallow to avoid C++ aborts
            pass


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    # ------------------------------ UI --------------------------------------
    def initUI(self):
        self.setWindowTitle('Axial Flux Motor Calculator')
        main_layout = QHBoxLayout(self)
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        form_layout = QFormLayout()

        # Inputs: QLineEdit for numeric; QCheckBox for booleans
        self.inputs = {
            "Number of Coils": QLineEdit(),
            "Number of Turns": QLineEdit(),  # leave blank for auto from voltage
            "Input Voltage (V)": QLineEdit(),
            "Voltage Is DC Bus": QCheckBox(),
            "Modulation Index (0-1)": QLineEdit(),
            "Outer Radius (m)": QLineEdit(),
            "Desired Torque (N-m)": QLineEdit(),
            "ESC Frequency (Hz)": QLineEdit(),     # electrical Hz
            "Mechanical RPM": QLineEdit(),         # if provided, overrides Hz
            "Poles": QLineEdit(),
            "Winding Factor": QLineEdit(),
            "Magnetic Flux Density (T)": QLineEdit(),
            "Dual Plate": QCheckBox(),
            "Phase Current Limit (A)": QLineEdit(),
            "DC Current Limit (A)": QLineEdit(),
            "ESC Freq Max (Hz)": QLineEdit(),
        }

        self.defaults = {
            "Number of Coils": 12,
            "Number of Turns": None,           # None => auto
            "Input Voltage (V)": 36,
            "Voltage Is DC Bus": False,
            "Modulation Index (0-1)": 0.95,
            "Outer Radius (m)": 0.127,         # ~5 in
            "Desired Torque (N-m)": 50.0,
            "ESC Frequency (Hz)": 50.0,
            "Mechanical RPM": 750.0,
            "Poles": 8,
            "Winding Factor": 0.92,
            "Magnetic Flux Density (T)": 0.6,
            "Dual Plate": False,
            "Phase Current Limit (A)": "",
            "DC Current Limit (A)": "",
            "ESC Freq Max (Hz)": "",
        }

        # Build form
        for key, widget in self.inputs.items():
            label = QLabel(key)
            form_layout.addRow(label, widget)
            default_val = self.defaults[key]
            if isinstance(widget, QCheckBox):
                widget.setChecked(bool(default_val))
            else:
                widget.setText("" if default_val is None else str(default_val))

        left_layout.addLayout(form_layout)

        # Calculate button
        self.calculate_button = QPushButton('Calculate')
        self.calculate_button.clicked.connect(self.calculate)
        left_layout.addWidget(self.calculate_button)

        # Results (left grid)
        self.result_labels = {
            # Legacy-ish
            "Number of Poles": QLabel("Number of Poles:"),
            "Number of Magnets": QLabel("Number of Magnets:"),
            "Inner Radius (m)": QLabel("Inner Radius (m):"),
            "Outer Radius (m)": QLabel("Outer Radius (m):"),
            "Rotor Area (m^2)": QLabel("Rotor Area (m^2):"),
            "Airgap Shear Stress (N/m^2)": QLabel("Airgap Shear Stress (N/m^2):"),
            "Minimum RPM": QLabel("RPM (from inputs):"),
            "Peak Flux Density (T)": QLabel("Peak Flux Density (T):"),
            "Number of Coil Turns": QLabel("Number of Coil Turns:"),
            "Total Torque (N-m)": QLabel("Total Torque (N-m):"),
            "Required Current (A)": QLabel("Required Current (A):"),

            # New, clearer data
            "Electrical Frequency (Hz)": QLabel("Electrical Frequency (Hz):"),
            "Mechanical RPM": QLabel("Mechanical RPM:"),
            "Flux per Pole (Wb)": QLabel("Flux per Pole (Wb):"),
            "Winding Factor": QLabel("Winding Factor:"),
            "Torque Constant Kt (N·m/A)": QLabel("Torque Constant Kt (N·m/A):"),
            "Back-EMF Const Ke_phase_peak (V·s/rad)": QLabel("Back-EMF Const Ke_phase_peak (V·s/rad):"),
            "Voltage Utilization (V_emf/V_avail)": QLabel("Voltage Utilization:"),
            "Max RPM @ V-limit (fixed N)": QLabel("Max RPM @ V-limit (fixed N):"),
            "Power Mechanical (W)": QLabel("Mechanical Power (W):"),
            "Estimated DC Current (A)": QLabel("Estimated DC Current (A):"),
            "Shear Stress Heuristic Limit (N/m^2)": QLabel("Heuristic τ limit (N/m^2):"),
            "Dual Plate Enabled": QLabel("Dual Plate Enabled:"),
            "Mode": QLabel("Mode:"),

            # Pass/Fail summaries
            "V-limit Pass": QLabel("Voltage limit pass?"),
            "I-limit Pass": QLabel("Current limit pass?"),
            "ESC f_e Pass": QLabel("ESC f_e pass?"),
            "DC-limit Pass": QLabel("DC limit pass?"),
            "Max Torque @ I_limit (N-m)": QLabel("Max Torque @ I_limit (N-m):"),
        }

        self.result_values = {}
        results_layout = QGridLayout()
        row = 0
        for key, label in self.result_labels.items():
            results_layout.addWidget(label, row, 0)
            value_label = QLabel("—")
            value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            results_layout.addWidget(value_label, row, 1)
            self.result_values[key] = value_label
            row += 1

        left_layout.addLayout(results_layout)

        # Visualization on the right
        self.visualization_widget = VisualizationWidget(
            get_num_coils_callable=lambda: self.inputs["Number of Coils"].text()
        )
        right_layout.addWidget(self.visualization_widget)

        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 1)
        self.setLayout(main_layout)

    # ----------------------------- helpers ----------------------------------
    def _float_or_default(self, text, default):
        text = (text or "").strip()
        if text == "":
            return default
        try:
            return float(text)
        except Exception:
            return default

    def _build_parameters(self):
        """
        Build kwargs for AxialMotorDesign from current inputs with safe fallbacks.
        """
        # Simple numeric parses
        coils = int(self._float_or_default(self.inputs["Number of Coils"].text(), self.defaults["Number of Coils"]))
        turns_text = self.inputs["Number of Turns"].text().strip()
        turns = None if turns_text == "" else self._float_or_default(turns_text, None)

        params = {
            "coils": coils,
            "turns": turns,
            "input_voltage": self._float_or_default(self.inputs["Input Voltage (V)"].text(), self.defaults["Input Voltage (V)"]),
            "outer_radius": self._float_or_default(self.inputs["Outer Radius (m)"].text(), self.defaults["Outer Radius (m)"]),
            "desired_torque": self._float_or_default(self.inputs["Desired Torque (N-m)"].text(), self.defaults["Desired Torque (N-m)"]),
            "magnetic_flux_density": self._float_or_default(self.inputs["Magnetic Flux Density (T)"].text(), self.defaults["Magnetic Flux Density (T)"]),
            "poles": int(self._float_or_default(self.inputs["Poles"].text(), self.defaults["Poles"])),
            "winding_factor": self._float_or_default(self.inputs["Winding Factor"].text(), self.defaults["Winding Factor"]),
            "modulation_index": self._float_or_default(self.inputs["Modulation Index (0-1)"].text(), self.defaults["Modulation Index (0-1)"]),
            "input_is_vdc": self.inputs["Voltage Is DC Bus"].isChecked(),
            "dual_plate": self.inputs["Dual Plate"].isChecked(),
            "phase_current_limit": self._float_or_default(self.inputs["Phase Current Limit (A)"].text(), self.defaults["Phase Current Limit (A)"]),
            "dc_current_limit": self._float_or_default(self.inputs["DC Current Limit (A)"].text(), self.defaults["DC Current Limit (A)"]),
            "esc_freq_max": self._float_or_default(self.inputs["ESC Freq Max (Hz)"].text(), self.defaults["ESC Freq Max (Hz)"]),
        }

        # Frequency vs RPM priority: if Mechanical RPM provided, use it; else use ESC Frequency
        mech_text = self.inputs["Mechanical RPM"].text().strip()
        if mech_text != "":
            params["mechanical_rpm"] = self._float_or_default(mech_text, self.defaults["Mechanical RPM"])
            params["esc_frequency"] = None
        else:
            params["esc_frequency"] = self._float_or_default(self.inputs["ESC Frequency (Hz)"].text(), self.defaults["ESC Frequency (Hz)"])
            params["mechanical_rpm"] = None

        return params

    # ----------------------------- actions ----------------------------------
    def calculate(self):
        try:
            parameters = self._build_parameters()
            motor = AxialMotorDesign(**parameters)
            results = motor.get_calculations()

            # Only update labels we have; default to —
            for key, lbl in self.result_values.items():
                lbl.setText(str(results.get(key, "—")))

        except Exception as e:
            # Show the error on the first row so it's visible
            self.result_values["Number of Poles"].setText(f"Error: {e}")
            traceback.print_exc()
        finally:
            self.visualization_widget.update()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
