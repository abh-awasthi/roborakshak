#!/usr/bin/env python3
import argparse
import os
import time

# GPIO pin mapping for L298N
LEFT_MOTOR_PIN1 = 5   # IN1
LEFT_MOTOR_PIN2 = 6   # IN2
RIGHT_MOTOR_PIN1 = 13  # IN3
RIGHT_MOTOR_PIN2 = 19  # IN4
PWM_FREQUENCY = 100

FORCE_MOCK = os.getenv('FORCE_MOCK', '').lower() in ('1', 'true', 'yes')

try:
    if FORCE_MOCK:
        raise ImportError('FORCE_MOCK enabled')
    import RPi.GPIO as GPIO
    MOCK_GPIO = False
except Exception:
    MOCK_GPIO = True

    class MockPWM:
        def __init__(self, pin, freq):
            self.pin = pin
            self.freq = freq
            self.duty = 0

        def start(self, duty):
            self.duty = duty
            print(f"[MOCK] PWM start: pin={self.pin}, duty={duty}%")

        def ChangeDutyCycle(self, duty):
            self.duty = duty
            print(f"[MOCK] PWM change: pin={self.pin}, duty={duty}%")

        def stop(self):
            print(f"[MOCK] PWM stop: pin={self.pin}")

    class GPIO:
        BCM = 'BCM'
        OUT = 'OUT'
        LOW = 0
        HIGH = 1

        @staticmethod
        def setmode(mode):
            print(f"[MOCK] setmode({mode})")

        @staticmethod
        def setwarnings(flag):
            print(f"[MOCK] setwarnings({flag})")

        @staticmethod
        def setup(pin, mode):
            print(f"[MOCK] setup(pin={pin}, mode={mode})")

        @staticmethod
        def output(pin, state):
            state_label = 'HIGH' if state else 'LOW'
            print(f"[MOCK] output(pin={pin}, state={state_label})")

        @staticmethod
        def PWM(pin, freq):
            return MockPWM(pin, freq)

        @staticmethod
        def cleanup():
            print('[MOCK] cleanup()')


def init_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for pin in [LEFT_MOTOR_PIN1, LEFT_MOTOR_PIN2, RIGHT_MOTOR_PIN1, RIGHT_MOTOR_PIN2]:
        GPIO.setup(pin, GPIO.OUT)

    left_pwm = GPIO.PWM(LEFT_MOTOR_PIN1, PWM_FREQUENCY)
    left_pwm_rev = GPIO.PWM(LEFT_MOTOR_PIN2, PWM_FREQUENCY)
    right_pwm = GPIO.PWM(RIGHT_MOTOR_PIN1, PWM_FREQUENCY)
    right_pwm_rev = GPIO.PWM(RIGHT_MOTOR_PIN2, PWM_FREQUENCY)

    left_pwm.start(0)
    left_pwm_rev.start(0)
    right_pwm.start(0)
    right_pwm_rev.start(0)

    return left_pwm, left_pwm_rev, right_pwm, right_pwm_rev


def stop_all(left_pwm, left_pwm_rev, right_pwm, right_pwm_rev):
    left_pwm.ChangeDutyCycle(0)
    left_pwm_rev.ChangeDutyCycle(0)
    right_pwm.ChangeDutyCycle(0)
    right_pwm_rev.ChangeDutyCycle(0)


def forward(left_pwm, left_pwm_rev, right_pwm, right_pwm_rev, speed):
    print(f"Running forward at {speed}%")
    left_pwm.ChangeDutyCycle(speed)
    left_pwm_rev.ChangeDutyCycle(0)
    right_pwm.ChangeDutyCycle(speed)
    right_pwm_rev.ChangeDutyCycle(0)


def backward(left_pwm, left_pwm_rev, right_pwm, right_pwm_rev, speed):
    print(f"Running backward at {speed}%")
    left_pwm.ChangeDutyCycle(0)
    left_pwm_rev.ChangeDutyCycle(speed)
    right_pwm.ChangeDutyCycle(0)
    right_pwm_rev.ChangeDutyCycle(speed)


def turn_left(left_pwm, left_pwm_rev, right_pwm, right_pwm_rev, speed):
    print(f"Turning left at {speed}%")
    left_pwm.ChangeDutyCycle(0)
    left_pwm_rev.ChangeDutyCycle(0)
    right_pwm.ChangeDutyCycle(speed)
    right_pwm_rev.ChangeDutyCycle(0)


def turn_right(left_pwm, left_pwm_rev, right_pwm, right_pwm_rev, speed):
    print(f"Turning right at {speed}%")
    left_pwm.ChangeDutyCycle(speed)
    left_pwm_rev.ChangeDutyCycle(0)
    right_pwm.ChangeDutyCycle(0)
    right_pwm_rev.ChangeDutyCycle(0)


def rotate_left(left_pwm, left_pwm_rev, right_pwm, right_pwm_rev, speed):
    print(f"Rotating left in place at {speed}%")
    left_pwm.ChangeDutyCycle(0)
    left_pwm_rev.ChangeDutyCycle(speed)
    right_pwm.ChangeDutyCycle(speed)
    right_pwm_rev.ChangeDutyCycle(0)


def rotate_right(left_pwm, left_pwm_rev, right_pwm, right_pwm_rev, speed):
    print(f"Rotating right in place at {speed}%")
    left_pwm.ChangeDutyCycle(speed)
    left_pwm_rev.ChangeDutyCycle(0)
    right_pwm.ChangeDutyCycle(0)
    right_pwm_rev.ChangeDutyCycle(speed)


def parse_args():
    parser = argparse.ArgumentParser(description='RoboRakshak motor test helper')
    parser.add_argument('command', choices=[
        'forward', 'backward', 'left', 'right', 'rotate_left', 'rotate_right', 'stop'
    ], help='Motor command to execute')
    parser.add_argument('--speed', type=int, default=60, help='PWM speed percentage (0-100)')
    parser.add_argument('--duration', type=float, default=3.0, help='Duration to run the command in seconds')
    return parser.parse_args()


def main():
    args = parse_args()
    print('FORCE_MOCK mode:', FORCE_MOCK)
    left_pwm, left_pwm_rev, right_pwm, right_pwm_rev = init_gpio()

    try:
        if args.command == 'forward':
            forward(left_pwm, left_pwm_rev, right_pwm, right_pwm_rev, args.speed)
        elif args.command == 'backward':
            backward(left_pwm, left_pwm_rev, right_pwm, right_pwm_rev, args.speed)
        elif args.command == 'left':
            turn_left(left_pwm, left_pwm_rev, right_pwm, right_pwm_rev, args.speed)
        elif args.command == 'right':
            turn_right(left_pwm, left_pwm_rev, right_pwm, right_pwm_rev, args.speed)
        elif args.command == 'rotate_left':
            rotate_left(left_pwm, left_pwm_rev, right_pwm, right_pwm_rev, args.speed)
        elif args.command == 'rotate_right':
            rotate_right(left_pwm, left_pwm_rev, right_pwm, right_pwm_rev, args.speed)
        elif args.command == 'stop':
            stop_all(left_pwm, left_pwm_rev, right_pwm, right_pwm_rev)

        if args.command != 'stop':
            time.sleep(args.duration)
            stop_all(left_pwm, left_pwm_rev, right_pwm, right_pwm_rev)
    finally:
        if not MOCK_GPIO:
            GPIO.cleanup()
        else:
            print('Mock cleanup finished')


if __name__ == '__main__':
    main()
