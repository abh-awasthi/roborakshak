// RoboRakshak Motor Control UI
class RoboRakshakController {
    constructor() {
        this.baseURL = `http://${window.location.hostname}:5000`;
        this.currentSpeed = 50;
        this.currentDirection = 'stop';
        this.isConnected = true;
        
        this.initializeEventListeners();
        this.updateStatus();
        this.startStatusPolling();
    }

    initializeEventListeners() {
        // Direction buttons
        document.getElementById('forwardBtn').addEventListener('click', () => this.moveForward());
        document.getElementById('backwardBtn').addEventListener('click', () => this.moveBackward());
        document.getElementById('leftBtn').addEventListener('click', () => this.turnLeft());
        document.getElementById('rightBtn').addEventListener('click', () => this.turnRight());
        document.getElementById('stopBtn').addEventListener('click', () => this.stop());

        // Speed control
        const speedSlider = document.getElementById('speedSlider');
        speedSlider.addEventListener('input', (e) => this.setSpeed(e.target.value));

        // Preset speed buttons
        document.querySelectorAll('.preset-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const speed = e.target.dataset.speed;
                speedSlider.value = speed;
                this.setSpeed(speed);
            });
        });

        // Keyboard controls
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));
        document.addEventListener('keyup', (e) => this.handleKeyUp(e));
    }

    async moveForward() {
        await this.sendCommand('/api/motor/forward');
        this.currentDirection = 'forward';
        this.updateUI('Moving Forward');
    }

    async moveBackward() {
        await this.sendCommand('/api/motor/backward');
        this.currentDirection = 'backward';
        this.updateUI('Moving Backward');
    }

    async turnLeft() {
        await this.sendCommand('/api/motor/left');
        this.currentDirection = 'left';
        this.updateUI('Turning Left');
    }

    async turnRight() {
        await this.sendCommand('/api/motor/right');
        this.currentDirection = 'right';
        this.updateUI('Turning Right');
    }

    async stop() {
        await this.sendCommand('/api/motor/stop');
        this.currentDirection = 'stop';
        this.updateUI('Stopped');
    }

    async setSpeed(speed) {
        speed = parseInt(speed);
        this.currentSpeed = speed;
        await this.sendCommand(`/api/motor/speed/${speed}`);
        
        document.getElementById('speedSlider').value = speed;
        document.getElementById('speedDisplay').textContent = speed;
        document.getElementById('speedValue').textContent = speed + '%';
    }

    async sendCommand(endpoint) {
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            document.getElementById('lastCommand').textContent = new Date().toLocaleTimeString();
            this.isConnected = true;
            this.updateConnectionStatus();
            
            return data;
        } catch (error) {
            console.error('Error sending command:', error);
            this.isConnected = false;
            this.updateConnectionStatus();
        }
    }

    handleKeyDown(e) {
        const key = e.key;
        
        switch(key) {
            case 'ArrowUp':
                e.preventDefault();
                this.moveForward();
                break;
            case 'ArrowDown':
                e.preventDefault();
                this.moveBackward();
                break;
            case 'ArrowLeft':
                e.preventDefault();
                this.turnLeft();
                break;
            case 'ArrowRight':
                e.preventDefault();
                this.turnRight();
                break;
            case ' ':
                e.preventDefault();
                this.stop();
                break;
            case '+':
            case '=':
                e.preventDefault();
                this.increaseSpeed();
                break;
            case '-':
            case '_':
                e.preventDefault();
                this.decreaseSpeed();
                break;
        }
    }

    handleKeyUp(e) {
        // Could add key-up specific handling if needed
    }

    increaseSpeed() {
        const newSpeed = Math.min(100, this.currentSpeed + 5);
        this.setSpeed(newSpeed);
    }

    decreaseSpeed() {
        const newSpeed = Math.max(0, this.currentSpeed - 5);
        this.setSpeed(newSpeed);
    }

    updateUI(direction) {
        document.getElementById('directionValue').textContent = direction;
    }

    updateConnectionStatus() {
        const statusEl = document.getElementById('connectionStatus');
        if (this.isConnected) {
            statusEl.textContent = 'Connected';
            statusEl.className = 'status-connected';
        } else {
            statusEl.textContent = 'Disconnected';
            statusEl.className = 'status-disconnected';
        }
    }

    async updateStatus() {
        try {
            const response = await fetch(`${this.baseURL}/api/status`);
            if (response.ok) {
                const data = await response.json();
                this.currentSpeed = data.speed;
                this.currentDirection = data.direction;
                
                document.getElementById('speedSlider').value = data.speed;
                document.getElementById('speedDisplay').textContent = data.speed;
                document.getElementById('speedValue').textContent = data.speed + '%';
                document.getElementById('directionValue').textContent = 
                    data.direction.charAt(0).toUpperCase() + data.direction.slice(1);
                
                this.isConnected = true;
            }
            this.updateConnectionStatus();
        } catch (error) {
            console.error('Error updating status:', error);
            this.isConnected = false;
            this.updateConnectionStatus();
        }
    }

    startStatusPolling() {
        setInterval(() => this.updateStatus(), 2000);
    }

    getHostInfo() {
        const protocol = window.location.protocol;
        const host = window.location.host;
        document.getElementById('hostInfo').textContent = host;
    }
}

// Initialize controller when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const controller = new RoboRakshakController();
    controller.getHostInfo();
    console.log('RoboRakshak Control Panel Initialized');
});
