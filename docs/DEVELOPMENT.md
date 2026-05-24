# Development Guide - RoboRakshak

## Local Development Setup

### On Your Development Machine (macOS/Linux/Windows)

#### Prerequisites
- Python 3.7+
- pip and virtualenv
- Git
- Code editor (VS Code recommended)

#### Setup Steps

```bash
# 1. Clone the repository
git clone https://github.com/abh-awasthi/roborakshak.git
cd roborakshak

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the development server
cd backend
python3 app.py

# 5. Open browser to http://localhost:5000
```

---

## Project Structure Explanation

### Backend (`backend/app.py`)

The Flask application provides:

1. **GPIO Initialization**
   ```python
   def init_gpio():
       # Setup pins in BCM mode
       # Configure PWM at 50Hz
       # Ready for motor commands
   ```

2. **Motor Control Functions**
   - `move_forward()` - Left PIN1 & Right PIN1 HIGH
   - `move_backward()` - Left PIN2 & Right PIN2 HIGH
   - `turn_left()` - Right motor ON, Left motor OFF
   - `turn_right()` - Left motor ON, Right motor OFF
   - `stop_motors()` - All pins LOW

3. **REST API Routes**
   - `/api/motor/forward` - POST
   - `/api/motor/backward` - POST
   - `/api/motor/left` - POST
   - `/api/motor/right` - POST
   - `/api/motor/stop` - POST
   - `/api/motor/speed/<0-100>` - POST
   - `/api/status` - GET

4. **Threading & Locking**
   - Thread-safe motor speed updates
   - Prevents GPIO conflicts
   - Safe concurrent API calls

### Frontend Structure

#### `frontend/index.html`
- Semantic HTML5 structure
- Accessible form controls
- Mobile-first responsive design
- Real-time status display

#### `frontend/static/style.css`
- Gradient background (purple theme)
- Responsive grid layout
- Touch-friendly button sizing
- Mobile breakpoints at 768px and 480px
- Smooth animations and transitions

#### `frontend/static/script.js`
- `RoboRakshakController` class
  - Manages all UI interactions
  - Handles API calls
  - Updates status display
  - Processes keyboard input
  - Maintains connection state

### Key JavaScript Methods

```javascript
// Motor control
controller.moveForward()
controller.moveBackward()
controller.turnLeft()
controller.turnRight()
controller.stop()

// Speed management
controller.setSpeed(speed)
controller.increaseSpeed()
controller.decreaseSpeed()

// API communication
controller.sendCommand(endpoint)

// Status updates
controller.updateStatus()
controller.startStatusPolling()
```

---

## Development Workflow

### Making Code Changes

#### Backend Changes
1. Edit `backend/app.py`
2. Test changes locally with `python3 app.py`
3. Check Flask logs for errors
4. Restart Flask server
5. Test API endpoints with browser/curl

#### Frontend Changes
1. Edit files in `frontend/static/`
2. No build step needed (vanilla JS)
3. Refresh browser to see changes
4. Check browser console for errors

#### Styling Updates
1. Edit `frontend/static/style.css`
2. Changes apply immediately on refresh
3. Test on different screen sizes
4. Use browser DevTools for debugging

### Testing Locally (Without Raspberry Pi)

```bash
# Create mock GPIO library
cat > mock_gpio.py << 'EOF'
import sys

class MockGPIO:
    BCM = 'BCM'
    OUT = 'OUT'
    LOW = 0
    HIGH = 1
    
    @staticmethod
    def setmode(mode): pass
    @staticmethod
    def setwarnings(flag): pass
    @staticmethod
    def setup(pin, mode): pass
    @staticmethod
    def output(pin, state): print(f"GPIO {pin} = {state}")
    @staticmethod
    def PWM(pin, freq): return MockPWM()
    @staticmethod
    def cleanup(): pass

class MockPWM:
    def start(self, duty): pass
    def ChangeDutyCycle(self, duty): pass

sys.modules['RPi.GPIO'] = MockGPIO()
sys.modules['RPi'] = MockGPIO()
EOF

# Run with mock GPIO
python3 app.py
```

---

## Extending the Application

### Adding New Motor Commands

```python
# In backend/app.py

@app.route('/api/motor/custom', methods=['POST'])
def custom_movement():
    global motor_direction
    with lock:
        motor_direction = "custom"
        # Your custom motor control logic here
        GPIO.output(LEFT_MOTOR_PIN1, GPIO.HIGH)
        # ... etc
    return jsonify({'status': 'custom movement'})
```

### Adding UI Controls

```html
<!-- In frontend/index.html -->
<button id="customBtn" class="arrow-btn">Custom</button>
```

```javascript
// In frontend/static/script.js
document.getElementById('customBtn').addEventListener('click', 
    () => this.sendCommand('/api/motor/custom'));
```

### Adding Camera Support

```python
# In backend/app.py
from picamera2 import Picamera2

def init_camera():
    camera = Picamera2()
    camera.start()
    return camera

@app.route('/api/camera/stream')
def camera_stream():
    # Implement video streaming
    pass
```

---

## Configuration & Optimization

### Adjusting Motor Speed

In `backend/app.py`:
```python
DEFAULT_SPEED = 50  # Change default
MAX_SPEED = 100     # Max safe speed
MIN_SPEED = 0       # Min safe speed
```

### Changing GPIO Pins

If your wiring is different:
```python
LEFT_MOTOR_PIN1 = 5    # Adjust these
LEFT_MOTOR_PIN2 = 6
RIGHT_MOTOR_PIN1 = 13
RIGHT_MOTOR_PIN2 = 19
```

### Adjusting PWM Frequency

```python
PWM_FREQUENCY = 50  # Hz - affects motor smoothness
```

### UI Theme Customization

Edit colors in `frontend/static/style.css`:
```css
/* Primary color */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Change to your preferred colors */
```

---

## Debugging & Troubleshooting

### Backend Debugging

```bash
# Run with debug mode
python3 -c "import app; app.app.debug=True; app.app.run()"

# Check Flask logs
tail -f app.log

# Test API endpoints
curl -X POST http://localhost:5000/api/motor/forward

# Check GPIO access
python3 -c "import RPi.GPIO as GPIO; print('GPIO OK')"
```

### Frontend Debugging

1. Open Browser DevTools (F12)
2. Check Console tab for JavaScript errors
3. Check Network tab for API call failures
4. Use `console.log()` for debugging
5. Check Application tab for stored data

### Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Import error: RPi.GPIO | Use mock GPIO for testing on non-Pi |
| Port already in use | Change port in app.py or kill process |
| GPIO permission denied | Add user to gpio group: `sudo usermod -a -G gpio $USER` |
| UI doesn't respond | Check browser console for JavaScript errors |
| API returns 404 | Verify Flask is running and endpoint name is correct |

---

## Performance Optimization

### Backend Optimization
- Use PWM for smooth speed control
- Implement thread-safe locking
- Efficient GPIO operations
- Minimal Flask middleware

### Frontend Optimization
- Vanilla JavaScript (no heavy frameworks)
- Responsive CSS Grid layout
- Lazy loading (future)
- Minimize API polling

### Network Optimization
- Status polling every 2 seconds (configurable)
- JSON response format (lightweight)
- Keep-alive connections
- Minimize data transfer

---

## Testing Checklist

Before deploying to Raspberry Pi:

- [ ] Backend tests
  - [ ] Flask server starts without errors
  - [ ] All endpoints return valid responses
  - [ ] GPIO operations work correctly
  - [ ] Speed and direction changes work
  - [ ] Stop command works reliably

- [ ] Frontend tests
  - [ ] All buttons are clickable
  - [ ] Speed slider is responsive
  - [ ] Keyboard controls work
  - [ ] Status updates display correctly
  - [ ] Mobile responsive design works

- [ ] Integration tests
  - [ ] API calls trigger motor movement
  - [ ] Status updates reflect current state
  - [ ] Multiple simultaneous requests handled
  - [ ] Connection handles reconnection

- [ ] Hardware tests
  - [ ] Motors respond to commands
  - [ ] Speed changes affect motor behavior
  - [ ] Direction changes work correctly
  - [ ] Emergency stop functions
  - [ ] All GPIO pins work

---

## Git Workflow

```bash
# Create feature branch
git checkout -b feature/motor-improvements

# Make changes and test
# ... edit files ...

# Commit changes
git add .
git commit -m "Add motor speed smoothing feature"

# Push to remote
git push origin feature/motor-improvements

# Create pull request on GitHub
# ... review and merge ...
```

---

## Resources & References

### Documentation
- [Flask Documentation](https://flask.palletsprojects.com/)
- [RPi.GPIO Python Library](https://sourceforge.net/projects/raspberry-gpio-python/files/RPi.GPIO-0.7.0/)
- [L298N Motor Driver](https://www.datasheetspdf.com/pdf/L298N)
- [Raspberry Pi GPIO Pinout](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html)

### Tools
- [Postman](https://www.postman.com/) - API testing
- [Insomnia](https://insomnia.rest/) - API client
- [VS Code](https://code.visualstudio.com/) - Code editor
- [PyCharm](https://www.jetbrains.com/pycharm/) - Python IDE

### Learning
- PWM (Pulse Width Modulation)
- GPIO (General Purpose Input/Output)
- REST API design
- Flask routing and blueprints
- Frontend responsive design

---

## Contributing Guidelines

1. Fork the repository
2. Create a feature branch (`feature/your-feature`)
3. Commit your changes with clear messages
4. Push to your fork
5. Create pull request with description

**Code Style:**
- Python: PEP 8 (4-space indentation)
- JavaScript: ES6+ (2-space indentation)
- CSS: BEM naming convention
- Comments for complex logic

---

## Future Development Ideas

1. **Camera Support**
   - Live video streaming
   - Snapshot capture
   - Motion detection

2. **Advanced Controls**
   - Joystick/gamepad support
   - Preset movement patterns
   - Autonomous navigation

3. **Data Logging**
   - Motor telemetry
   - GPS tracking
   - Movement history

4. **Machine Learning**
   - Face detection
   - Object recognition
   - Autonomous decision-making

5. **Cloud Integration**
   - Remote monitoring
   - Data sync
   - Multiple robot control

---

## Support & Questions

- Review this guide thoroughly
- Check [README.md](README.md) for general info
- Look at code comments for implementation details
- Test changes thoroughly before committing
- Ask questions in GitHub Issues

---

**Happy Developing! 👨‍💻**

*Last Updated: May 2026*
