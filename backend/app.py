from flask import Flask, render_template, jsonify, request
from flask import Response
import time
import threading
import os
import secrets
import json
import traceback
from functools import wraps
from collections import deque, defaultdict


def _read_ini_setting(key, default=None):
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.ini'))
    if not os.path.exists(config_path):
        return default
    with open(config_path, 'r', encoding='utf-8') as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith('#') or line.startswith('##') or line.startswith(';'):
                continue
            if '=' not in line:
                continue
            name, value = line.split('=', 1)
            if name.strip() == key:
                return value.strip()
    return default


def _env_or_ini_bool(key, default=False):
    env_value = os.getenv(key)
    if env_value is not None:
        return env_value.lower() in ('1', 'true', 'yes', 'on')
    ini_value = _read_ini_setting(key)
    if ini_value is None:
        return default
    return ini_value.lower() in ('1', 'true', 'yes', 'on')


def _env_or_ini_int(key, default):
    env_value = os.getenv(key)
    if env_value is not None:
        try:
            return int(env_value)
        except (ValueError, TypeError):
            pass
    ini_value = _read_ini_setting(key)
    if ini_value is None:
        return default
    try:
        return int(ini_value)
    except (ValueError, TypeError):
        return default


def _env_or_ini_float(key, default):
    env_value = os.getenv(key)
    if env_value is not None:
        try:
            return float(env_value)
        except (ValueError, TypeError):
            pass
    ini_value = _read_ini_setting(key)
    if ini_value is None:
        return default
    try:
        return float(ini_value)
    except (ValueError, TypeError):
        return default


def _env_or_ini_value(key, default):
    env_value = os.getenv(key)
    if env_value is not None:
        return env_value
    ini_value = _read_ini_setting(key)
    if ini_value is None:
        return default
    return ini_value

# OpenCV support for camera testing
try:
    import cv2
    OPENCV_AVAILABLE = True
except Exception:
    cv2 = None
    OPENCV_AVAILABLE = False
# picamera2 (libcamera) support for Raspberry Pi CSI cameras
try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
    PICAMERA2_IMPORT_ERROR = None
except Exception:
    Picamera2 = None
    PICAMERA2_AVAILABLE = False
    PICAMERA2_IMPORT_ERROR = traceback.format_exc()

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
STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'static'))
CAPTURE_DIR = os.path.join(STATIC_DIR, 'captures')

# GPIO Pin Configuration
LEFT_MOTOR_PIN1 = 5    # IN1
LEFT_MOTOR_PIN2 = 6    # IN2
RIGHT_MOTOR_PIN1 = 13  # IN3
RIGHT_MOTOR_PIN2 = 19  # IN4

PWM_FREQUENCY = 50  # Hz
MAX_SPEED_CAP = int(os.getenv('MAX_SPEED_CAP', '80'))
SOFT_ACCEL_STEP = int(os.getenv('SOFT_ACCEL_STEP', '5'))
SOFT_ACCEL_DELAY = float(os.getenv('SOFT_ACCEL_DELAY', '0.03'))
DEADMAN_TIMEOUT_SEC = float(os.getenv('DEADMAN_TIMEOUT_SEC', '1.2'))
DRIVER_PIN = os.getenv('DRIVER_PIN', '4321')
VIEWER_PIN = os.getenv('VIEWER_PIN', '1111')
AUTH_SESSION_TTL_SEC = int(os.getenv('AUTH_SESSION_TTL_SEC', '28800'))
AUDIT_LOG_LIMIT = 200
RATE_LIMIT_WINDOW_SEC = int(os.getenv('RATE_LIMIT_WINDOW_SEC', '10'))
RATE_LIMIT_MAX_REQUESTS = int(os.getenv('RATE_LIMIT_MAX_REQUESTS', '40'))
RESTRICT_TO_LOCAL_NET = os.getenv('RESTRICT_TO_LOCAL_NET', '0').lower() in ('1', 'true', 'yes')
CAMERA_ENABLED = _env_or_ini_bool('CAMERA_ENABLED', True)
CAMERA_DRIVER = _env_or_ini_value('CAMERA_DRIVER', 'auto').strip().lower()
CAMERA_DEVICE = _env_or_ini_value('CAMERA_DEVICE', _env_or_ini_value('CAMERA_DEVICE_INDEX', '0'))
CAMERA_RESOLUTION = _env_or_ini_value('CAMERA_RESOLUTION', '1920x1080')
CAMERA_WARMUP_SECONDS = _env_or_ini_float('CAMERA_WARMUP_SECONDS', 1.5)
CAMERA_READ_ATTEMPTS = _env_or_ini_int('CAMERA_READ_ATTEMPTS', 12)
CAMERA_OPENCV_FOURCCS = _env_or_ini_value('CAMERA_OPENCV_FOURCCS', 'DEFAULT,MJPG,YUYV')

# Global variables
left_pwm = None
left_pwm_rev = None
right_pwm = None
right_pwm_rev = None
motor_speed = 50
motor_direction = "stop"
current_left_duty = 0
current_right_duty = 0
last_motion_command_at = time.monotonic()
sessions = {}
audit_log = []
camera_state = "not_connected"
camera_last_snapshot = None
camera_last_snapshot_url = None
camera_latest_frame_bytes = None
request_buckets = defaultdict(deque)
event_log = []
EVENT_LOG_LIMIT = 300
next_event_id = 1
lock = threading.Lock()
camera_access_lock = threading.Lock()

def get_client_ip():
    forwarded = request.headers.get('X-Forwarded-For', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr or 'unknown'

def is_local_ip(ip):
    return (
        ip.startswith('127.')
        or ip.startswith('10.')
        or ip.startswith('192.168.')
        or ip.startswith('172.16.')
        or ip.startswith('172.17.')
        or ip.startswith('172.18.')
        or ip.startswith('172.19.')
        or ip.startswith('172.2')
        or ip == '::1'
        or ip.startswith('fc')
        or ip.startswith('fd')
    )

def enforce_security():
    client_ip = get_client_ip()

    if RESTRICT_TO_LOCAL_NET and not is_local_ip(client_ip):
        add_audit('blocked_non_local', 'system')
        return jsonify({'error': 'non_local_access_denied'}), 403

    now = time.time()
    bucket = request_buckets[client_ip]
    bucket.append(now)
    while bucket and now - bucket[0] > RATE_LIMIT_WINDOW_SEC:
        bucket.popleft()
    if len(bucket) > RATE_LIMIT_MAX_REQUESTS:
        add_audit('rate_limited', 'system')
        return jsonify({'error': 'rate_limited'}), 429

    return None

@app.before_request
def apply_security_guards():
    # Keep static assets and home page unblocked for first load.
    if request.path.startswith('/static/') or request.path == '/':
        return None
    return enforce_security()

def add_audit(event, role='system'):
    entry = {
        'ts': int(time.time()),
        'event': event,
        'role': role
    }
    audit_log.append(entry)
    if len(audit_log) > AUDIT_LOG_LIMIT:
        del audit_log[:len(audit_log) - AUDIT_LOG_LIMIT]

def add_event(event_type, message, severity='info'):
    global next_event_id
    event_log.append({
        'id': next_event_id,
        'ts': int(time.time()),
        'type': event_type,
        'severity': severity,
        'message': message,
        'acknowledged': False
    })
    next_event_id += 1
    if len(event_log) > EVENT_LOG_LIMIT:
        del event_log[:len(event_log) - EVENT_LOG_LIMIT]

def clean_expired_sessions():
    now = time.time()
    expired_tokens = [token for token, meta in sessions.items() if meta['expires_at'] <= now]
    for token in expired_tokens:
        del sessions[token]

def get_auth_context():
    clean_expired_sessions()
    # Prefer Authorization header, but allow a secure fallback for
    # non-AJAX consumers (like an <img> MJPEG tag) via ?token=... or
    # X-Auth-Token header or cookie. This keeps the default behavior
    # strict while enabling the live-image use-case.
    auth_header = request.headers.get('Authorization', '')
    token = None
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ', 1)[1].strip()

    if not token:
        # Fallbacks (query param, custom header, or cookie)
        token = request.args.get('token') or request.headers.get('X-Auth-Token') or request.cookies.get('rr_auth_token')
        if token:
            token = token.strip()

    if not token:
        return None

    return sessions.get(token)

def require_auth(min_role='viewer'):
    role_order = {'viewer': 1, 'driver': 2}

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            auth_ctx = get_auth_context()
            if not auth_ctx:
                return jsonify({'error': 'unauthorized'}), 401
            if role_order.get(auth_ctx['role'], 0) < role_order[min_role]:
                return jsonify({'error': 'forbidden'}), 403
            return fn(*args, **kwargs)
        return wrapper

    return decorator

def init_gpio():
    """Initialize GPIO pins"""
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Setup pins
        pins = [LEFT_MOTOR_PIN1, LEFT_MOTOR_PIN2, RIGHT_MOTOR_PIN1, RIGHT_MOTOR_PIN2]
        for pin in pins:
            GPIO.setup(pin, GPIO.OUT)
        
        # Setup PWM on both motor direction pins
        global left_pwm, left_pwm_rev, right_pwm, right_pwm_rev
        left_pwm = GPIO.PWM(LEFT_MOTOR_PIN1, PWM_FREQUENCY)
        left_pwm_rev = GPIO.PWM(LEFT_MOTOR_PIN2, PWM_FREQUENCY)
        right_pwm = GPIO.PWM(RIGHT_MOTOR_PIN1, PWM_FREQUENCY)
        right_pwm_rev = GPIO.PWM(RIGHT_MOTOR_PIN2, PWM_FREQUENCY)

        left_pwm.start(0)
        left_pwm_rev.start(0)
        right_pwm.start(0)
        right_pwm_rev.start(0)
        
        return True
    except Exception as e:
        print(f"GPIO Init Error: {e}")
        return False

def set_motor_speed(speed):
    """Set motor speed (0-100)"""
    global motor_speed
    with lock:
        motor_speed = max(0, min(MAX_SPEED_CAP, speed))

def mark_motion_command():
    global last_motion_command_at
    last_motion_command_at = time.monotonic()

def ramp_pwm_to(left_target, right_target):
    """Softly ramp PWM duty cycles to target values."""
    global current_left_duty, current_right_duty
    left_target = max(0, min(MAX_SPEED_CAP, int(left_target)))
    right_target = max(0, min(MAX_SPEED_CAP, int(right_target)))

    while current_left_duty != left_target or current_right_duty != right_target:
        if current_left_duty < left_target:
            current_left_duty = min(current_left_duty + SOFT_ACCEL_STEP, left_target)
        elif current_left_duty > left_target:
            current_left_duty = max(current_left_duty - SOFT_ACCEL_STEP, left_target)

        if current_right_duty < right_target:
            current_right_duty = min(current_right_duty + SOFT_ACCEL_STEP, right_target)
        elif current_right_duty > right_target:
            current_right_duty = max(current_right_duty - SOFT_ACCEL_STEP, right_target)

        left_pwm.ChangeDutyCycle(current_left_duty)
        right_pwm.ChangeDutyCycle(current_right_duty)
        time.sleep(SOFT_ACCEL_DELAY)

def stop_motors_locked():
    """Stop all motors"""
    global current_left_duty, current_right_duty
    try:
        if left_pwm and left_pwm_rev and right_pwm and right_pwm_rev:
            GPIO.output(LEFT_MOTOR_PIN1, GPIO.LOW)
            GPIO.output(LEFT_MOTOR_PIN2, GPIO.LOW)
            GPIO.output(RIGHT_MOTOR_PIN1, GPIO.LOW)
            GPIO.output(RIGHT_MOTOR_PIN2, GPIO.LOW)
            left_pwm.ChangeDutyCycle(0)
            left_pwm_rev.ChangeDutyCycle(0)
            right_pwm.ChangeDutyCycle(0)
            right_pwm_rev.ChangeDutyCycle(0)
            if not MOCK_GPIO:
                ramp_pwm_to(0, 0)
            else:
                current_left_duty = 0
                current_right_duty = 0
    except Exception as e:
        print(f"Stop Error: {e}")

def stop_motors():
    with lock:
        stop_motors_locked()

def move_forward():
    """Move robot forward"""
    try:
        GPIO.output(LEFT_MOTOR_PIN2, GPIO.LOW)
        GPIO.output(RIGHT_MOTOR_PIN2, GPIO.LOW)
        left_pwm_rev.ChangeDutyCycle(0)
        right_pwm_rev.ChangeDutyCycle(0)
        ramp_pwm_to(motor_speed, motor_speed)
    except Exception as e:
        print(f"Forward Error: {e}")

def move_backward():
    """Move robot backward"""
    try:
        GPIO.output(LEFT_MOTOR_PIN1, GPIO.LOW)
        GPIO.output(RIGHT_MOTOR_PIN1, GPIO.LOW)
        left_pwm.ChangeDutyCycle(0)
        right_pwm.ChangeDutyCycle(0)
        left_pwm_rev.ChangeDutyCycle(motor_speed)
        right_pwm_rev.ChangeDutyCycle(motor_speed)
    except Exception as e:
        print(f"Backward Error: {e}")

def turn_left():
    """Turn robot left"""
    try:
        GPIO.output(LEFT_MOTOR_PIN1, GPIO.LOW)
        GPIO.output(LEFT_MOTOR_PIN2, GPIO.LOW)
        GPIO.output(RIGHT_MOTOR_PIN2, GPIO.LOW)
        left_pwm.ChangeDutyCycle(0)
        left_pwm_rev.ChangeDutyCycle(0)
        right_pwm_rev.ChangeDutyCycle(0)
        ramp_pwm_to(0, motor_speed)
    except Exception as e:
        print(f"Left Error: {e}")

def turn_right():
    """Turn robot right"""
    try:
        GPIO.output(LEFT_MOTOR_PIN2, GPIO.LOW)
        GPIO.output(RIGHT_MOTOR_PIN1, GPIO.LOW)
        left_pwm_rev.ChangeDutyCycle(0)
        right_pwm.ChangeDutyCycle(0)
        ramp_pwm_to(motor_speed, 0)
    except Exception as e:
        print(f"Right Error: {e}")

def rotate_left():
    """Rotate robot left in place"""
    try:
        GPIO.output(LEFT_MOTOR_PIN1, GPIO.LOW)
        GPIO.output(RIGHT_MOTOR_PIN2, GPIO.LOW)
        left_pwm.ChangeDutyCycle(0)
        left_pwm_rev.ChangeDutyCycle(motor_speed)
        right_pwm.ChangeDutyCycle(motor_speed)
        right_pwm_rev.ChangeDutyCycle(0)
    except Exception as e:
        print(f"Rotate Left Error: {e}")

def rotate_right():
    """Rotate robot right in place"""
    try:
        GPIO.output(LEFT_MOTOR_PIN2, GPIO.LOW)
        GPIO.output(RIGHT_MOTOR_PIN1, GPIO.LOW)
        left_pwm.ChangeDutyCycle(motor_speed)
        left_pwm_rev.ChangeDutyCycle(0)
        right_pwm.ChangeDutyCycle(0)
        right_pwm_rev.ChangeDutyCycle(motor_speed)
    except Exception as e:
        print(f"Rotate Right Error: {e}")

def deadman_monitor():
    """Auto-stop when no motion command is received for timeout window."""
    global motor_direction
    while True:
        time.sleep(0.2)
        with lock:
            if motor_direction == "stop":
                continue
            if time.monotonic() - last_motion_command_at > DEADMAN_TIMEOUT_SEC:
                print("[SAFETY] Deadman timeout reached. Auto-stopping motors.")
                motor_direction = "stop"
                stop_motors_locked()

def get_local_ip():
    try:
        import socket
        host = socket.gethostname()
        return socket.gethostbyname(host)
    except Exception:
        return "unknown"

def parse_camera_resolution(resolution):
    try:
        width, height = resolution.strip().split('x')
        return int(width), int(height)
    except Exception:
        return 1920, 1080


def get_camera_device_source():
    value = str(CAMERA_DEVICE).strip()
    if value.lstrip('-').isdigit():
        return int(value)
    return value


def get_camera_device_sources():
    source = get_camera_device_source()
    sources = [source]
    if isinstance(source, int) and os.name == 'posix':
        for candidate in [
            f'/dev/video{source}',
            source + 1,
            f'/dev/video{source + 1}',
            source + 2,
            f'/dev/video{source + 2}',
        ]:
            if candidate not in sources:
                sources.append(candidate)
    return sources


def release_camera_capture(cap):
    if cap is None:
        return
    try:
        if hasattr(cap, 'release'):
            cap.release()
        elif hasattr(cap, 'stop'):
            cap.stop()
            cap.close()
    except Exception:
        pass
    finally:
        if PICAMERA2_AVAILABLE and isinstance(cap, Picamera2):
            time.sleep(0.4)


def requested_and_fallback_resolutions():
    requested = parse_camera_resolution(CAMERA_RESOLUTION)
    candidates = [requested, (1280, 720), (640, 480)]
    unique = []
    for size in candidates:
        if size not in unique:
            unique.append(size)
    return unique


def opencv_backend_candidates():
    backends = [(None, 'AUTO')]
    if hasattr(cv2, 'CAP_V4L2') and os.name == 'posix':
        backends.insert(0, (cv2.CAP_V4L2, 'V4L2'))
    return backends


def opencv_fourcc_candidates():
    candidates = []
    for raw_item in str(CAMERA_OPENCV_FOURCCS).split(','):
        item = raw_item.strip().upper()
        if not item:
            continue
        if item in ('DEFAULT', 'NONE', 'AUTO'):
            candidate = (None, 'DEFAULT')
        elif len(item) == 4:
            candidate = (item, item)
        else:
            continue
        if candidate not in candidates:
            candidates.append(candidate)
    if not candidates:
        candidates.append((None, 'DEFAULT'))
    return candidates


def describe_opencv_capture(source, backend_name, fourcc_name, width, height):
    return f'source={source} backend={backend_name} format={fourcc_name} requested={width}x{height}'


def open_opencv_capture(source, backend, backend_name, fourcc, fourcc_name, width, height):
    try:
        cap = cv2.VideoCapture(source) if backend is None else cv2.VideoCapture(source, backend)
    except Exception:
        return None

    if not cap.isOpened():
        release_camera_capture(cap)
        return None

    if hasattr(cv2, 'CAP_PROP_BUFFERSIZE'):
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    if fourcc and hasattr(cv2, 'CAP_PROP_FOURCC'):
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*fourcc))
    if width > 0:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    if height > 0:
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    print('[CAMERA] OpenCV opened', describe_opencv_capture(source, backend_name, fourcc_name, width, height))
    return cap


def read_opencv_frame(cap):
    deadline = time.monotonic() + CAMERA_WARMUP_SECONDS
    attempts = max(CAMERA_READ_ATTEMPTS, 1)
    for _ in range(attempts):
        ret, frame = cap.read()
        if ret and frame is not None:
            return frame
        try:
            if cap.grab():
                ret, frame = cap.retrieve()
                if ret and frame is not None:
                    return frame
        except Exception:
            pass
        if time.monotonic() < deadline:
            time.sleep(0.1)
    return None


def get_opencv_capture_with_frame():
    if not OPENCV_AVAILABLE:
        return None, None, 'OpenCV is not available on the server'

    last_message = f'Unable to open camera device {get_camera_device_source()}'
    for source in get_camera_device_sources():
        for width, height in requested_and_fallback_resolutions():
            for fourcc, fourcc_name in opencv_fourcc_candidates():
                for backend, backend_name in opencv_backend_candidates():
                    descriptor = describe_opencv_capture(source, backend_name, fourcc_name, width, height)
                    cap = open_opencv_capture(source, backend, backend_name, fourcc, fourcc_name, width, height)
                    if cap is None:
                        continue
                    frame = read_opencv_frame(cap)
                    if frame is not None:
                        return cap, frame, f'{frame.shape[1]}x{frame.shape[0]} ({descriptor})'
                    release_camera_capture(cap)
                    last_message = f'Opened camera ({descriptor}), but could not read a frame'
    return None, None, last_message


def get_picamera2_capture():
    if not PICAMERA2_AVAILABLE:
        message = 'Picamera2 is not available in this Python environment'
        if PICAMERA2_IMPORT_ERROR:
            message = f'{message}: {PICAMERA2_IMPORT_ERROR.strip().splitlines()[-1]}'
        return None, message

    picam = None
    try:
        picam = Picamera2()
        width, height = parse_camera_resolution(CAMERA_RESOLUTION)
        cfg = picam.create_preview_configuration(
            main={'format': 'XRGB8888', 'size': (width, height)}
        )
        picam.configure(cfg)
        picam.start()
        time.sleep(max(CAMERA_WARMUP_SECONDS, 0.2))
        return picam, None
    except Exception as exc:
        try:
            if picam is not None:
                picam.close()
        except Exception:
            pass
        return None, str(exc)


def encode_frame_as_jpeg(frame):
    if frame is None:
        return None
    try:
        if frame.ndim == 3 and frame.shape[2] == 4:
            frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
        elif frame.ndim == 3 and frame.shape[2] == 1:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        elif frame.ndim == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        ok, jpeg = cv2.imencode('.jpg', frame)
        if not ok:
            return None
        return jpeg.tobytes()
    except Exception:
        return None


def save_camera_frame(frame):
    global camera_last_snapshot, camera_last_snapshot_url
    frame_bytes = encode_frame_as_jpeg(frame)
    if frame_bytes is None:
        return None, None

    os.makedirs(CAPTURE_DIR, exist_ok=True)
    captured_at = int(time.time())
    filename = f'camera-{int(time.time() * 1000)}.jpg'
    filepath = os.path.join(CAPTURE_DIR, filename)
    with open(filepath, 'wb') as handle:
        handle.write(frame_bytes)

    camera_last_snapshot = captured_at
    camera_last_snapshot_url = f'/static/captures/{filename}'
    return camera_last_snapshot_url, captured_at


def save_camera_frame_bytes(frame_bytes):
    global camera_last_snapshot, camera_last_snapshot_url
    if not frame_bytes:
        return None, None

    os.makedirs(CAPTURE_DIR, exist_ok=True)
    captured_at = int(time.time())
    filename = f'camera-{int(time.time() * 1000)}.jpg'
    filepath = os.path.join(CAPTURE_DIR, filename)
    with open(filepath, 'wb') as handle:
        handle.write(frame_bytes)

    camera_last_snapshot = captured_at
    camera_last_snapshot_url = f'/static/captures/{filename}'
    return camera_last_snapshot_url, captured_at


def test_camera_connection():
    if not CAMERA_ENABLED:
        return False, 'Camera support is disabled (CAMERA_ENABLED=false)', None, None

    if CAMERA_DRIVER not in ('auto', 'picamera2', 'opencv'):
        return False, f'Unsupported CAMERA_DRIVER={CAMERA_DRIVER}', None, None

    if camera_state == 'streaming':
        return True, 'Camera stream is active', camera_last_snapshot_url, camera_last_snapshot

    if not camera_access_lock.acquire(timeout=5):
        return False, 'Camera is busy; stop the stream or try again in a moment', None, None

    picamera2_error = None
    try:
        if CAMERA_DRIVER in ('auto', 'picamera2'):
            picam, picamera2_error = get_picamera2_capture()
            if picam is not None:
                try:
                    frame = picam.capture_array()
                finally:
                    release_camera_capture(picam)
                if frame is None:
                    picamera2_error = 'Picamera2 opened the camera but captured no frame'
                else:
                    url, captured_at = save_camera_frame(frame)
                    return True, f'Camera connected (picamera2), frame captured ({frame.shape[1]}x{frame.shape[0]})', url, captured_at
            print('[CAMERA] picamera2 test failed:', picamera2_error)
            if CAMERA_DRIVER == 'picamera2':
                return False, f'Failed to capture a frame from the camera (picamera2): {picamera2_error}', None, None

        cap = None
        try:
            cap, frame, message = get_opencv_capture_with_frame()
            if frame is None:
                if picamera2_error:
                    return False, (
                        f'Failed to capture a frame from the camera. '
                        f'Picamera2 failed: {picamera2_error}; OpenCV failed: {message}'
                    ), None, None
                return False, f'Failed to capture a frame from the camera (opencv): {message}', None, None
            url, captured_at = save_camera_frame(frame)
            return True, f'Camera connected (opencv), frame captured ({message})', url, captured_at
        except Exception as exc:
            return False, str(exc), None, None
        finally:
            release_camera_capture(cap)
    finally:
        camera_access_lock.release()


def get_camera_capture():
    # Prefer Picamera2 (libcamera) for CSI cameras, fall back to OpenCV VideoCapture
    if not CAMERA_ENABLED:
        return None
    if CAMERA_DRIVER in ('auto', 'picamera2'):
        picam, message = get_picamera2_capture()
        if picam is not None:
            return picam
        print('[CAMERA] picamera2 capture initialization failed:', message)
        if CAMERA_DRIVER == 'picamera2':
            return None

    if CAMERA_DRIVER not in ('auto', 'opencv'):
        print('[CAMERA] Unsupported CAMERA_DRIVER:', CAMERA_DRIVER)
        return None

    cap, frame, message = get_opencv_capture_with_frame()
    if cap is None:
        print('[CAMERA] OpenCV capture initialization failed:', message)
        return None
    return cap


def capture_camera_frame_once():
    picamera2_error = None
    if CAMERA_DRIVER in ('auto', 'picamera2'):
        picam, picamera2_error = get_picamera2_capture()
        if picam is not None:
            try:
                frame = picam.capture_array()
            finally:
                release_camera_capture(picam)
            if frame is not None:
                return frame, f'picamera2 frame captured ({frame.shape[1]}x{frame.shape[0]})'
            picamera2_error = 'Picamera2 opened the camera but captured no frame'
        if CAMERA_DRIVER == 'picamera2':
            return None, f'Failed to capture a frame from the camera (picamera2): {picamera2_error}'

    cap = None
    try:
        cap, frame, message = get_opencv_capture_with_frame()
        if frame is not None:
            return frame, f'opencv frame captured ({message})'
        if picamera2_error:
            return None, f'Picamera2 failed: {picamera2_error}; OpenCV failed: {message}'
        return None, f'Failed to capture a frame from the camera (opencv): {message}'
    finally:
        release_camera_capture(cap)


def generate_camera_frames():
    global camera_latest_frame_bytes
    if not camera_access_lock.acquire(timeout=5):
        print('[CAMERA] Stream could not start because the camera is busy')
        return
    cap = get_camera_capture()
    if cap is None:
        camera_access_lock.release()
        return
    try:
        if PICAMERA2_AVAILABLE and isinstance(cap, Picamera2):
            picam = cap
            try:
                while camera_state == 'streaming':
                    frame = picam.capture_array()
                    if frame is None:
                        break
                    frame_bytes = encode_frame_as_jpeg(frame)
                    if frame_bytes is None:
                        break
                    camera_latest_frame_bytes = frame_bytes
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                    time.sleep(0.05)
            finally:
                try:
                    picam.stop()
                    picam.close()
                except Exception as exc:
                    print('[CAMERA] picamera2 cleanup failed:', exc)
                    traceback.print_exc()
        else:
            # OpenCV capture
            cap_cv = cap
            try:
                while camera_state == 'streaming':
                    ret, frame = cap_cv.read()
                    if not ret or frame is None:
                        break
                    ret, jpeg = cv2.imencode('.jpg', frame)
                    if not ret:
                        break
                    frame_bytes = jpeg.tobytes()
                    camera_latest_frame_bytes = frame_bytes
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                    time.sleep(0.05)
            finally:
                try:
                    cap_cv.release()
                except Exception:
                    pass
    except GeneratorExit:
        # Stream closed by client
        pass
    finally:
        camera_access_lock.release()


# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/auth/login', methods=['POST'])
def login():
    payload = request.get_json(silent=True) or {}
    pin = str(payload.get('pin', '')).strip()
    if not pin:
        return jsonify({'error': 'pin_required'}), 400

    role = None
    if pin == DRIVER_PIN:
        role = 'driver'
    elif pin == VIEWER_PIN:
        role = 'viewer'
    else:
        return jsonify({'error': 'invalid_pin'}), 401

    token = secrets.token_urlsafe(24)
    sessions[token] = {
        'role': role,
        'created_at': time.time(),
        'expires_at': time.time() + AUTH_SESSION_TTL_SEC
    }
    add_audit('login', role)
    return jsonify({
        'token': token,
        'role': role,
        'expires_in_sec': AUTH_SESSION_TTL_SEC
    })

@app.route('/api/auth/logout', methods=['POST'])
@require_auth('viewer')
def logout():
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.split(' ', 1)[1].strip()
    auth_ctx = sessions.get(token)
    if auth_ctx:
        add_audit('logout', auth_ctx['role'])
    sessions.pop(token, None)
    return jsonify({'status': 'logged_out'})

@app.route('/api/status')
@require_auth('viewer')
def status():
    auth_ctx = get_auth_context()
    return jsonify({
        'status': 'running',
        'speed': motor_speed,
        'direction': motor_direction,
        'role': auth_ctx['role'] if auth_ctx else 'viewer',
        'camera': {
            'state': camera_state,
            'last_snapshot_ts': camera_last_snapshot,
            'last_snapshot_url': camera_last_snapshot_url
        },
        'safety': {
            'max_speed_cap': MAX_SPEED_CAP,
            'deadman_timeout_sec': DEADMAN_TIMEOUT_SEC,
            'soft_accel_step': SOFT_ACCEL_STEP,
            'soft_accel_delay': SOFT_ACCEL_DELAY
        }
    })

@app.route('/api/audit', methods=['GET'])
@require_auth('viewer')
def get_audit():
    return jsonify({'entries': audit_log[-50:]})

@app.route('/api/audit/export', methods=['GET'])
@require_auth('viewer')
def export_audit():
    payload = {
        'exported_at': int(time.time()),
        'entries': audit_log
    }
    return Response(
        response=json.dumps(payload),
        mimetype='application/json',
        headers={
            'Content-Disposition': f'attachment; filename=roborakshak-audit-{int(time.time())}.json'
        }
    )

@app.route('/api/events', methods=['GET'])
@require_auth('viewer')
def get_events():
    return jsonify({'events': event_log[-80:]})

@app.route('/api/events/mock', methods=['POST'])
@require_auth('driver')
def create_mock_event():
    payload = request.get_json(silent=True) or {}
    event_type = str(payload.get('type', 'motion')).strip() or 'motion'
    severity = str(payload.get('severity', 'warning')).strip() or 'warning'
    message = str(payload.get('message', 'Mock security event')).strip() or 'Mock security event'
    add_event(event_type, message, severity)
    add_audit('event_mock_created', 'driver')
    return jsonify({'status': 'event created', 'event_type': event_type, 'severity': severity})

@app.route('/api/events/ack/<int:event_id>', methods=['POST'])
@require_auth('driver')
def acknowledge_event(event_id):
    for event in event_log:
        if event['id'] == event_id:
            event['acknowledged'] = True
            add_audit(f'event_ack_{event_id}', 'driver')
            return jsonify({'status': 'acknowledged', 'event_id': event_id})
    return jsonify({'error': 'event_not_found'}), 404

@app.route('/api/events/clear', methods=['POST'])
@require_auth('driver')
def clear_events():
    event_log.clear()
    add_audit('events_cleared', 'driver')
    return jsonify({'status': 'events_cleared'})

@app.route('/api/health', methods=['GET'])
@require_auth('viewer')
def health():
    clean_expired_sessions()
    return jsonify({
        'status': 'ok',
        'mode': 'mock' if MOCK_GPIO else 'hardware',
        'uptime_sec': int(time.monotonic()),
        'host': {
            'ip': get_local_ip(),
            'port': 5000
        },
        'auth': {
            'active_sessions': len(sessions),
            'ttl_sec': AUTH_SESSION_TTL_SEC
        },
        'security': {
            'rate_limit_window_sec': RATE_LIMIT_WINDOW_SEC,
            'rate_limit_max_requests': RATE_LIMIT_MAX_REQUESTS,
            'restrict_to_local_net': RESTRICT_TO_LOCAL_NET
        },
        'camera': {
            'state': camera_state,
            'last_snapshot_ts': camera_last_snapshot,
            'last_snapshot_url': camera_last_snapshot_url
        },
        'motor': {
            'direction': motor_direction,
            'speed': motor_speed,
            'max_speed_cap': MAX_SPEED_CAP
        },
        'safety': {
            'deadman_timeout_sec': DEADMAN_TIMEOUT_SEC,
            'soft_accel_step': SOFT_ACCEL_STEP,
            'soft_accel_delay': SOFT_ACCEL_DELAY
        }
    })

@app.route('/api/camera/status', methods=['GET'])
@require_auth('viewer')
def camera_status():
    return jsonify({
        'state': camera_state,
        'last_snapshot_ts': camera_last_snapshot,
        'last_snapshot_url': camera_last_snapshot_url
    })

@app.route('/api/camera/ready', methods=['POST'])
@require_auth('driver')
def camera_ready():
    global camera_state
    camera_state = 'ready'
    add_audit('camera_ready', 'driver')
    add_event('camera', 'Camera marked ready', 'info')
    return jsonify({'status': 'camera ready', 'state': camera_state})

@app.route('/api/camera/start', methods=['POST'])
@require_auth('driver')
def camera_start():
    global camera_state
    if camera_state == 'not_connected':
        return jsonify({'error': 'camera_not_connected'}), 400
    camera_state = 'streaming'
    add_audit('camera_stream_start', 'driver')
    add_event('camera', 'Camera stream started', 'info')
    return jsonify({'status': 'camera streaming', 'state': camera_state})

@app.route('/api/camera/stop', methods=['POST'])
@require_auth('driver')
def camera_stop():
    global camera_state
    if camera_state == 'streaming':
        camera_state = 'ready'
    add_audit('camera_stream_stop', 'driver')
    add_event('camera', 'Camera stream stopped', 'info')
    return jsonify({'status': 'camera stopped', 'state': camera_state})

@app.route('/api/camera/snapshot', methods=['POST'])
@require_auth('driver')
def camera_snapshot():
    global camera_last_snapshot
    if camera_state == 'not_connected':
        return jsonify({'error': 'camera_not_connected'}), 400

    if camera_state == 'streaming':
        snapshot_url, captured_at = save_camera_frame_bytes(camera_latest_frame_bytes)
        if snapshot_url is None:
            return jsonify({
                'error': 'snapshot_failed',
                'message': 'No live camera frame is available yet. Wait for the stream preview to appear, then try again.'
            }), 503
    else:
        if not camera_access_lock.acquire(timeout=5):
            return jsonify({
                'error': 'camera_busy',
                'message': 'Camera is busy; stop the stream or try again in a moment.'
            }), 409
        try:
            frame, message = capture_camera_frame_once()
            if frame is None:
                return jsonify({'error': 'snapshot_failed', 'message': message}), 500
            snapshot_url, captured_at = save_camera_frame(frame)
            if snapshot_url is None:
                return jsonify({'error': 'snapshot_failed', 'message': 'Captured frame could not be encoded as JPEG'}), 500
        finally:
            camera_access_lock.release()

    add_audit('camera_snapshot', 'driver')
    add_event('camera', f'Snapshot saved: {snapshot_url}', 'info')
    return jsonify({
        'status': 'snapshot captured',
        'state': camera_state,
        'captured_at': captured_at,
        'snapshot_url': snapshot_url,
        'saved_to': os.path.join(CAPTURE_DIR, os.path.basename(snapshot_url))
    })

@app.route('/api/camera/test', methods=['POST'])
@require_auth('driver')
def camera_test():
    global camera_state
    ok, message, snapshot_url, captured_at = test_camera_connection()
    add_audit('camera_test', 'driver' if ok else 'system')
    if ok:
        if camera_state == 'not_connected':
            camera_state = 'ready'
        add_event('camera', f'Camera test passed: {message}', 'info')
        return jsonify({
            'status': 'camera_ok',
            'message': message,
            'state': camera_state,
            'captured_at': captured_at,
            'snapshot_url': snapshot_url
        })
    add_event('camera', f'Camera test failed: {message}', 'warning')
    return jsonify({'error': 'camera_test_failed', 'message': message}), 500


@app.route('/api/camera/stream')
@require_auth('viewer')
def camera_stream():
    if camera_state != 'streaming':
        return jsonify({'error': 'camera_not_streaming'}), 400
    if not CAMERA_ENABLED:
        return jsonify({'error': 'camera_unavailable'}), 503
    return Response(generate_camera_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/motor/forward', methods=['POST'])
@require_auth('driver')
def forward():
    global motor_direction
    with lock:
        mark_motion_command()
        motor_direction = "forward"
        move_forward()
    add_audit('motor_forward', 'driver')
    add_event('motor', 'Moved forward', 'info')
    return jsonify({'status': 'moving forward', 'speed': motor_speed})

@app.route('/api/motor/backward', methods=['POST'])
@require_auth('driver')
def backward():
    global motor_direction
    with lock:
        mark_motion_command()
        motor_direction = "backward"
        move_backward()
    add_audit('motor_backward', 'driver')
    add_event('motor', 'Moved backward', 'info')
    return jsonify({'status': 'moving backward', 'speed': motor_speed})

@app.route('/api/motor/left', methods=['POST'])
@require_auth('driver')
def left():
    global motor_direction
    with lock:
        mark_motion_command()
        motor_direction = "left"
        turn_left()
    add_audit('motor_left', 'driver')
    add_event('motor', 'Turned left', 'info')
    return jsonify({'status': 'turning left', 'speed': motor_speed})

@app.route('/api/motor/right', methods=['POST'])
@require_auth('driver')
def right():
    global motor_direction
    with lock:
        mark_motion_command()
        motor_direction = "right"
        turn_right()
    add_audit('motor_right', 'driver')
    add_event('motor', 'Turned right', 'info')
    return jsonify({'status': 'turning right', 'speed': motor_speed})

@app.route('/api/motor/rotate/left', methods=['POST'])
@require_auth('driver')
def rotate_left_route():
    global motor_direction
    with lock:
        mark_motion_command()
        motor_direction = "rotate_left"
        rotate_left()
    add_audit('motor_rotate_left', 'driver')
    add_event('motor', 'Rotated left', 'info')
    return jsonify({'status': 'rotating left', 'speed': motor_speed})

@app.route('/api/motor/rotate/right', methods=['POST'])
@require_auth('driver')
def rotate_right_route():
    global motor_direction
    with lock:
        mark_motion_command()
        motor_direction = "rotate_right"
        rotate_right()
    add_audit('motor_rotate_right', 'driver')
    add_event('motor', 'Rotated right', 'info')
    return jsonify({'status': 'rotating right', 'speed': motor_speed})

@app.route('/api/motor/stop', methods=['POST'])
@require_auth('driver')
def stop():
    global motor_direction
    with lock:
        mark_motion_command()
        motor_direction = "stop"
        stop_motors_locked()
    add_audit('motor_stop', 'driver')
    add_event('motor', 'Motor stopped', 'info')
    return jsonify({'status': 'stopped', 'speed': motor_speed})

@app.route('/api/motor/speed/<int:speed>', methods=['POST'])
@require_auth('driver')
def set_speed(speed):
    set_motor_speed(speed)
    add_audit(f'speed_set_{motor_speed}', 'driver')
    add_event('motor', f'Speed set to {motor_speed}', 'info')
    return jsonify({'status': 'speed set', 'speed': motor_speed})

if __name__ == '__main__':
    # Initialize GPIO
    init_gpio()
    threading.Thread(target=deadman_monitor, daemon=True).start()
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()
