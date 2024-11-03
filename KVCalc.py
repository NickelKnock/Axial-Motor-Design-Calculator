import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFormLayout

class KVCalculatorSimple(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('KV Rating Calculator')

        form_layout = QFormLayout()

        self.inputs = {
            "Desired RPM": QLineEdit(),
            "Voltage (V)": QLineEdit(),
        }

        for key, line_edit in self.inputs.items():
            form_layout.addRow(QLabel(key), line_edit)

        self.calculate_button = QPushButton('Calculate')
        self.calculate_button.clicked.connect(self.calculate)

        self.result_label = QLabel("New Number of Turns: ")

        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(self.calculate_button)
        layout.addWidget(self.result_label)

        self.setLayout(layout)

    def calculate(self):
        try:
            original_kv = 62.5  # default original KV rating (RPM/V)
            original_turns = 30  # default original number of turns

            desired_rpm = float(self.inputs["Desired RPM"].text())
            voltage = float(self.inputs["Voltage (V)"].text())

            new_kv = desired_rpm / voltage
            ratio = new_kv / original_kv
            new_turns = int(round(original_turns / ratio))

            self.result_label.setText(f"New Number of Turns: {new_turns}")
        except ValueError:
            self.result_label.setText("Invalid input. Please enter numeric values.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    calculator = KVCalculatorSimple()
    calculator.show()
    sys.exit(app.exec_())
