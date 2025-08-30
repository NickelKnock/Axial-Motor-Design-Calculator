# ⚡ Axial Flux Motor Calculator

An open-hardware project to design and build high-performance axial flux motors.

🛠 The goal: work backwards from the application →
“I want X torque at Y RPM on Z volts” →
get a realistic first-cut design matched to real-world controllers & batteries.

## ✨ Features

### 🔌 Voltage-aware winding calc: auto-selects turns from DC bus & modulation index, or lock to fixed N.

### 🔁 Dual-plate toggle: double the torque constant instantly.

### 📊 ESC sanity checks:

### Phase current limit

### DC current limit

## Electrical frequency bandwidth

### 🚦 Pass/Fail indicators for voltage, current, frequency.

### ⚙ Mechanical power output in W and kW.

### 🔍 Rotor visualization with coil placement.

### 🧩 Extensible: copper loss, thermal modeling, and more can be added.

## 🚀 Getting Started
Requirements
python 3.9+
pip install PyQt5

Run
python AxialMotorFixedParamGUI.py


You’ll see the calculator window:

Inputs on the left

Results table below

Motor visualization on the right

## 🧭 Usage Guide

Define your use case
Example: “200 N·m at 750 RPM on a 72 V controller”.

Fill inputs

Set coils, poles, outer radius, flux density

Choose DC bus or AC RMS

Enter torque & speed (RPM or electrical Hz)

Leave Turns blank for auto (voltage-limited) or fix it manually (turns-limited)

Enable Dual Plate for two-rotor setups

Calculate → Review results
Key fields to watch:

Required Current (A) — phase current demand

Motor Power (W/kW) — shaft output

Voltage Utilization — must be < 1.0 to pass

Max Torque @ I-limit — torque ceiling at your controller’s phase limit

Max RPM @ V-limit — top speed before over-voltage

Adjust to pass

If U ≥ 1.0 → reduce turns, reduce RPM, or raise bus voltage

If I > ESC limit → enable dual-plate, enlarge rotor, or increase voltage

Use the headroom trick: set Turns ≈ 0.8 × auto → ~20% voltage margin

## 🏍 Example Configurations
<details> <summary>🔋 72 V “grunt” motor</summary>

200 N·m @ 750 RPM (~16 kW)

Auto-turns ≈ 47 → 153 A phase, U≈1.0

With headroom (Turns=38): 191 A phase, U≈0.8

</details> <details> <summary>🏁 100 V “supercross” motor</summary>

50 N·m @ 6000 RPM (~31 kW)

Auto-turns ≈ 12 → ~220 A phase, U≈1.0

With headroom (Turns=10): ~260 A phase, U≈0.85

</details>
## 🛠 Project Vision

This is the start of a larger open hardware initiative:

📂 Publish fully parametric axial flux motor designs

⚡ Pair with off-the-shelf hobby/EV controllers

📖 Document trade-offs clearly so anyone can build & improve

🌍 Grow a community-driven open motor library: DIY, hobby, industrial

### 📜 License

Released under the MIT License
. Free to use, modify, and share.

### 🤝 Contributing

Contributions welcome: issues, pull requests, test results, and build notes.
This project grows through real designs & feedback.

# 📸 Screenshots
<img width="692" height="1025" alt="image" src="https://github.com/user-attachments/assets/982eb279-311f-429a-b3ea-5759cb762d3a" />

<img width="1839" height="742" alt="Exploded Axial Gear Motor" src="https://github.com/user-attachments/assets/672ee92f-26b3-4bf1-938b-a85468b41241" />
