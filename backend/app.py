from flask import Flask, render_template, jsonify, request
import time
import threading
import os

# FORCE_MOCK env var (set to 1/true/yes to force mock GPIO even on Raspberry Pi)
FORCE_MOCK = os.getenv('FORCE_MOCK', '').lower() in ('1', 'true', 'yes')

# Try to import RPi.GPIO, fall back to mock for development or if FORCE_MOCK is set
try:
    if not FORCE_MOCK:
        import RPi.GPIO as GPIO
        MOCK_GPIO = False
    else:
        raise ImportError("FORCE_MOCK enabled")
except Exception:
    # Mock GPIO for local development (non-Raspberry Pi)
    class MockGPIO:
        BCM = 'BCM'
        OUT = 'OUT'
        LOW = 0
        HIGH = 1

        @staticmethod
        def setmode(mode):
            pass

        @staticmethod
        def setwarnings(flag):
            pass

        @staticmethod
        def setup(pin, mode):
            print(f"[MOCK] GPIO {pin} setup as output")

        @staticmethod
        def output(pin, state):
            state_label = "HIGH" if state else "LOW"
            print(f"[MOCK] GPIO {pin} = {state_label}")

        @staticmethod
        def PWM(pin, freq):
            return MockPWM(pin, freq)

        @staticmethod
        def cleanup():
            print("[MOCK] GPIO cleanup")

    class MockPWM:
        def __init__(self, pin, freq):
            self.pin = pin
            self.freq = freq
            self.duty = 0

        def start(self, duty):
            self.duty = duty
            print(f"[MOCK] PWM on GPIO {self.pin} started: {duty}% duty cycle")

        def ChangeDutyCycle(self, duty):
            self.duty = duty
            print(f"[MOCK] PWM on GPIO {self.pin} changed: {duty}% duty cycle")

    GPIO = MockGPIO()
    MOCK_GPIO = True

if MOCK_GPIO:
    print("=" * 50)
    print("Running in DEVELOPMENT MODE (Mock GPIO)")
    if FORCE_MOCK:
        print("FORCE_MOCK is set — mock GPIO forced via environment variable")
    print("GPIO commands will be logged but not execute")
    print("=" * 50)
    print()

app = Flask(__name__, template_folder='../frontend', static_folder='../frontend/static')

# GPIO Pin Configuration
LEFT_MOTOR_PIN1 = 5    # IN1
LEFT_MOTOR_PIN2 = 6    # IN2
RIGHT_MOTOR_PIN1 = 13  # IN3
RIGHT_MOTOR_PIN2 = 19  # IN4

PWM_FREQUENCY = 50  # Hz

# Global variables
left_pwm = None
right_pwm = None
motor_speed = 50
motor_direction = "stop"
lock = threading.Lock()

def init_gpio():
    """Initialize GPIO pins"""
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Setup pins
        pins = [LEFT_MOTOR_PIN1, LEFT_MOTOR_PIN2, RIGHT_MOTOR_PIN1, RIGHT_MOTOR_PIN2]
        for pin in pins:
            GPIO.setup(pin, GPIO.OUT)
        
        # Setup PWM
        global left_pwm, right_pwm
        left_pwm = GPIO.PWM(LEFT_MOTOR_PIN1, PWM_FREQUENCY)
        right_pwm = GPIO.PWM(RIGHT_MOTOR_PIN1, PWM_FREQUENCY)
        
        left_pwm.start(0)
        right_pwm.start(0)
        
        return True
    except Exception as e:
        print(f"GPIO Init Error: {e}")
        return False

def set_motor_speed(speed):
    """Set motor speed (0-100)"""
    global motor_speed
    with lock:
        motor_speed = max(0, min(100, speed))

def stop_motors():
    """Stop all motors"""
    with lock:
        try:
            if left_pwm and right_pwm:
                GPIO.output(LEFT_MOTOR_PIN1, GPIO.LOW)
                GPIO.output(LEFT_MOTOR_PIN2, GPIO.LOW)
                GPIO.output(RIGHT_MOTOR_PIN1, GPIO.LOW)
                GPIO.output(RIGHT_MOTOR_PIN2, GPIO.LOW)
                if not MOCK_GPIO:
                    left_pwm.ChangeDutyCycle(0)
                    right_pwm.ChangeDutyCycle(0)
        except Exception as e:
            print(f"Stop Error: {e}")

def move_forward():
    """Move robot forward"""
    try:
        GPIO.output(LEFT_MOTOR_PIN2, GPIO.LOW)
        GPIO.output(RIGHT_MOTOR_PIN2, GPIO.LOW)
        left_pwm.ChangeDutyCycle(motor_speed)
        right_pwm.ChangeDutyCycle(motor_speed)
    except Exception as e:
        print(f"Forward Error: {e}")

def move_backward():
    """Move robot backward"""
    try:
        GPIO.output(LEFT_MOTOR_PIN1, GPIO.LOW)
        GPIO.output(RIGHT_MOTOR_PIN1, GPIO.LOW)
        left_pwm.ChangeDutyCycle(motor_speed)
        right_pwm.ChangeDutyCycle(motor_speed)
    except Exception as e:
        print(f"Backward Error: {e}")

def turn_left():
    """Turn robot left"""
    try:
        GPIO.output(LEFT_MOTOR_PIN2, GPIO.LOW)
        GPIO.output(RIGHT_MOTOR_PIN1, GPIO.LOW)
        left_pwm.ChangeDutyCycle(0)
        right_pwm.ChangeDutyCycle(motor_speed)
    except Exception as e:
        print(f"Left Error: {e}")

def turn_right():
    """Turn robot right"""
    try:
        GPIO.output(LEFT_MOTOR_PIN1, GPIO.LOW)
        GPIO.output(RIGHT_MOTOR_PIN2, GPIO.LOW)
        left_pwm.ChangeDutyCycle(motor_speed)
        right_pwm.ChangeDutyCycle(0)
    except Exception as e:
        print(f"Right Error: {e}")

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/status')
def status():
    return jsonify({
        'status': 'running',
        'speed': motor_speed,
        'direction': motor_direction
    })

@app.route('/api/motor/forward', methods=['POST'])
def forward():
    global motor_direction
    with lock:
        motor_direction = "forward"
        move_forward()
    return jsonify({'status': 'moving forward', 'speed': motor_speed})

@app.route('/api/motor/backward', methods=['POST'])
def backward():
    global motor_direction
    with lock:
        motor_direction = "backward"
        move_backward()
    return jsonify({'status': 'moving backward', 'speed': motor_speed})

@app.route('/api/motor/left', methods=['POST'])
def left():
    global motor_direction
    with lock:
        motor_direction = "left"
        turn_left()
    return jsonify({'status': 'turning left', 'speed': motor_speed})

@app.route('/api/motor/right', methods=['POST'])
def right():
    global motor_direction
    with lock:
        motor_direction = "right"
        turn_right()
    return jsonify({'status': 'turning right', 'speed': motor_speed})

@app.route('/api/motor/stop', methods=['POST'])
def stop():
    global motor_direction
    with lock:
        motor_direction = "stop"
        stop_motors()
    return jsonify({'status': 'stopped', 'speed': motor_speed})

@app.route('/api/motor/speed/<int:speed>', methods=['POST'])
def set_speed(speed):
    set_motor_speed(speed)
    return jsonify({'status': 'speed set', 'speed': motor_speed})

if __name__ == '__main__':
    # Initialize GPIO
    init_gpio()
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()
