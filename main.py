from flask import Flask, render_template, request, jsonify
import math

app = Flask(__name__)

def extrusion_calculator(setpoint_speed, runout_length, ratio, die_cavities, billet_temp_C=470, alloy='6xxx', mass_kg_m=1):
    # Dynamic ratio_factor based on alloy and ratio ranges
    if alloy == '6xxx':
        if 10 <= ratio <= 30:
            ratio_factor = 0.1
        elif 31 <= ratio <= 69:
            ratio_factor = 0.2
        else:
            ratio_factor = 0.25
    else:  # 7xxx
        if 5 <= ratio <= 10:
            ratio_factor = 0.1
        elif 11 <= ratio <= 19:
            ratio_factor = 0.2
        else:
            ratio_factor = 0.25

    burp_psi = 1500 + 400 * ((math.log(ratio) - math.log(10)) / (math.log(100) - math.log(10)))
    if alloy == '7xxx':
        burp_psi *= 1.2
    burp_psi = min(2500, max(800, burp_psi))
    burp_psi = round(burp_psi / 100) * 100

    puller_speed_pct = (setpoint_speed / 15) * 100 * 1.04
    if alloy == '7xxx':
        puller_speed_pct *= 0.9
    puller_speed_pct = min(100, max(1, puller_speed_pct))

    torque_ramp_time = 0.1 + 9.9 * (setpoint_speed / 15) * (470 / billet_temp_C)
    if alloy == '7xxx':
        torque_ramp_time *= 1.1
    torque_ramp_time *= (1 + mass_kg_m * 0.1)  # Longer for heavier
    torque_ramp_time *= 0.9  # Shorten by 10% overall
    torque_ramp_time = min(10.0, max(0.1, torque_ramp_time))

    if die_cavities == 1:
        base_force = 1000
    else:
        base_force = 500 + 800 * ((die_cavities - 1) / 3)
    temp_factor = 0.1 * ((500 - billet_temp_C) / 30)
    speed_factor = 0.2 * (setpoint_speed / 15)
    length_factor = 0.05 * (runout_length / 41)
    puller_force = base_force * (1 + ratio_factor + temp_factor + speed_factor + length_factor) * 1.15
    if alloy == '7xxx':
        puller_force *= 1.15
    puller_force = min(1900, max(500, puller_force))
    puller_force = round(puller_force / 50) * 50

    hotsaw_speed_pct = 70 + (mass_kg_m * setpoint_speed * 0.2)
    hotsaw_speed_pct = min(95, max(50, hotsaw_speed_pct))

    return burp_psi, puller_speed_pct, torque_ramp_time, puller_force / 10, hotsaw_speed_pct

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.form
    ratio = float(data.get('ratio') or 0)
    runout_length = float(data.get('runout') or 0)
    setpoint_speed = float(data.get('speed') or 0)
    die_cavities = int(data.get('cavities') or 1)
    billet_temp_C = float(data.get('billet_temp') or 470)
    alloy = data.get('alloy') or '6xxx'
    mass_kg_m = float(data.get('mass_kg_m') or 1)
    burp, puller_pct, ramp, force, hotsaw_pct = extrusion_calculator(setpoint_speed, runout_length, ratio, die_cavities, billet_temp_C, alloy, mass_kg_m)
    return jsonify({'burp_psi': burp, 'puller_speed_pct': round(puller_pct), 'torque_ramp_time': round(ramp, 1), 'puller_force': force, 'hotsaw_speed_pct': round(hotsaw_pct)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
