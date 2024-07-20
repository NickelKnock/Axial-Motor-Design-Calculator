import sys
import math
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFormLayout, QGridLayout, QHBoxLayout
from PyQt5.QtGui import QPainter, QColor, QPen
from AxialMotorFixedParam import AxialMotorDesign

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Axial Flux Motor Calculator')

        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.inputs = {
            "Number of Coils": QLineEdit(),
            "Input Voltage (V)": QLineEdit(),
            "Outer Radius (m)": QLineEdit(),
            "Desired Torque (N-m)": QLineEdit(),
            "ESC Frequency (Hz)": QLineEdit(),
            "Magnetic Flux Density (T)": QLineEdit()
        }

        self.defaults = {
            "Number of Coils": 12,
            "Input Voltage (V)": 12,
            "Outer Radius (m)": 0.127,  # 5 inches converted to meters
            "Desired Torque (N-m)": 5.94,
            "ESC Frequency (Hz)": 50,
            "Magnetic Flux Density (T)": 0.6
        }

        for key, line_edit in self.inputs.items():
            form_layout.addRow(QLabel(key), line_edit)
            line_edit.setText(str(self.defaults[key]))

        left_layout.addLayout(form_layout)

        self.calculate_button = QPushButton('Calculate')
        self.calculate_button.clicked.connect(self.calculate)

        left_layout.addWidget(self.calculate_button)

        self.result_labels = {
            "Number of Poles": QLabel("Number of Poles: Number of poles calculated based on the number of coils."),
            "Number of Magnets": QLabel("Number of Magnets: Number of magnets calculated based on the number of poles."),
            "Inner Radius (m)": QLabel("Inner Radius (m): Inner radius calculated based on the outer radius and optimal ratio."),
            "Outer Radius (m)": QLabel("Outer Radius (m): Outer radius provided as input."),
            "Rotor Area (m^2)": QLabel("Rotor Area (m^2): Active surface area of the rotor."),
            "Airgap Shear Stress (N/m^2)": QLabel("Airgap Shear Stress (N/m^2): Shear stress in the airgap."),
            "Minimum RPM": QLabel("Minimum RPM: Minimum RPM calculated based on the ESC frequency and number of poles."),
            "Peak Flux Density (T)": QLabel("Peak Flux Density (T): Peak flux density in the motor."),
            "Number of Coil Turns": QLabel("Number of Coil Turns: Number of turns per coil."),
            "Total Torque (N-m)": QLabel("Total Torque (N-m): Total torque produced by the motor."),
            "Required Current (A)": QLabel("Required Current (A): Current required to produce the desired torque.")
        }

        self.result_values = {}
        results_layout = QGridLayout()
        row = 0
        for key, label in self.result_labels.items():
            results_layout.addWidget(label, row, 0)
            label_result = QLabel()
            results_layout.addWidget(label_result, row, 1)
            self.result_values[key] = label_result
            row += 1

        left_layout.addLayout(results_layout)
        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)

        self.visualization_widget = QWidget()
        right_layout.addWidget(self.visualization_widget)
        self.setLayout(main_layout)

    def calculate(self):
        parameter_mapping = {
            "Number of Coils": "coils",
            "Input Voltage (V)": "input_voltage",
            "Outer Radius (m)": "outer_radius",
            "Desired Torque (N-m)": "desired_torque",
            "ESC Frequency (Hz)": "esc_frequency",
            "Magnetic Flux Density (T)": "magnetic_flux_density"
        }

        parameters = {}
        for key, line_edit in self.inputs.items():
            try:
                parameters[parameter_mapping[key]] = float(line_edit.text())
            except ValueError:
                parameters[parameter_mapping[key]] = self.defaults[key]

        try:
            motor = AxialMotorDesign(**parameters)
            results = motor.get_calculations()

            for key, value in results.items():
                self.result_values[key].setText(value)
        except ValueError as e:
            # Display error message if any validation fails
            self.result_values["Number of Poles"].setText(f"Error: {e}")

        self.visualization_widget.update()

    def paintEvent(self, event):
        painter = QPainter(self.visualization_widget)
        self.drawMotorVisualization(painter)

    def drawMotorVisualization(self, painter):
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(0, 0, 0))
        painter.setPen(pen)
        painter.setBrush(QColor(200, 200, 200))

        width = self.visualization_widget.width() // 2
        height = self.visualization_widget.height() // 2
        radius_outer = min(width, height) // 2 - 20
        radius_inner = int(radius_outer * 0.58)

        painter.drawEllipse(width - radius_outer, height - radius_outer, 2 * radius_outer, 2 * radius_outer)
        painter.drawEllipse(width - radius_inner, height - radius_inner, 2 * radius_inner, 2 * radius_inner)

        painter.setBrush(QColor(150, 150, 150))
        num_coils = int(self.inputs["Number of Coils"].text())
        angle_step = 360 / num_coils
        for i in range(num_coils):
            angle = i * angle_step
            x = width + radius_outer * 0.9 * math.cos(math.radians(angle))
            y = height + radius_outer * 0.9 * math.sin(math.radians(angle))
            painter.drawEllipse(int(x - 5), int(y - 5), 10, 10)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
