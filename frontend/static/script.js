// RoboRakshak Motor Control UI
class RoboRakshakController {
    constructor() {
        this.baseURL = window.location.origin;
        this.authToken = localStorage.getItem('rr_auth_token') || '';
        this.userRole = localStorage.getItem('rr_user_role') || '';
        this.currentSpeed = 50;
        this.currentDirection = 'stop';
        this.isConnected = true;
        this.activeDirection = null;
        this.activeProfile = 'indoor';
        this.profileConfig = {
            indoor: { speed: 35, note: 'Indoor profile active: smoother, lower speed.' },
            outdoor: { speed: 60, note: 'Outdoor profile active: balanced speed and control.' },
            test: { speed: 80, note: 'Test profile active: highest allowed speed for validation.' }
        };
        this.joystickActive = false;
        this.joystickPointerId = null;
        this.joystickCenter = { x: 0, y: 0 };
        this.joystickRadius = 90;
        this.joystickTicker = null;
        this.joystickVector = { x: 0, y: 0 };
        this.lastJoystickDirection = 'stop';
        this.lastJoystickSpeed = null;
        this.lastJoystickCommandAt = 0;
        this.joystickIntervalMs = 120;
        this.directionChangeCooldownMs = 140;
        this.lastDirectionChangeAt = 0;
        this.smoothedMagnitude = 0;
        this.speedLerpAlpha = 0.35;
        this.hapticEnabled = true;
        this.soundEnabled = false;
        this.audioContext = null;
        this.lastFeedbackAt = 0;
        this.latencyHistory = [];
        this.maxLatencySamples = 8;
        this.networkOnline = navigator.onLine;
        this.eventsCache = [];
        this.severityFilter = 'all';
        
        this.initializeEventListeners();
        this.initializeTabs();
        this.initializeAuth();
        this.initializeProfiles();
        this.initializeJoystick();
        this.initializeTouchDrive();
        this.initializePWA();
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
                if (!speed) {
                    return;
                }
                speedSlider.value = speed;
                this.setSpeed(speed);
            });
        });

        const cameraRefreshBtn = document.getElementById('cameraRefreshBtn');
        if (cameraRefreshBtn) {
            cameraRefreshBtn.addEventListener('click', () => this.updateCameraStatus());
        }
        const cameraReadyBtn = document.getElementById('cameraReadyBtn');
        if (cameraReadyBtn) {
            cameraReadyBtn.addEventListener('click', () => this.cameraMarkReady());
        }
        const cameraStartBtn = document.getElementById('cameraStartBtn');
        if (cameraStartBtn) {
            cameraStartBtn.addEventListener('click', () => this.cameraStart());
        }
        const cameraStopBtn = document.getElementById('cameraStopBtn');
        if (cameraStopBtn) {
            cameraStopBtn.addEventListener('click', () => this.cameraStop());
        }
        const cameraSnapshotBtn = document.getElementById('cameraSnapshotBtn');
        if (cameraSnapshotBtn) {
            cameraSnapshotBtn.addEventListener('click', () => this.cameraSnapshot());
        }
        const cameraTestBtn = document.getElementById('cameraTestBtn');
        if (cameraTestBtn) {
            cameraTestBtn.addEventListener('click', () => this.cameraTest());
        }

        const refreshDiagBtn = document.getElementById('refreshDiagBtn');
        if (refreshDiagBtn) {
            refreshDiagBtn.addEventListener('click', () => this.updateDiagnostics());
        }
        const exportAuditBtn = document.getElementById('exportAuditBtn');
        if (exportAuditBtn) {
            exportAuditBtn.addEventListener('click', () => this.exportAuditLog());
        }
        const mockEventBtn = document.getElementById('mockEventBtn');
        if (mockEventBtn) {
            mockEventBtn.addEventListener('click', () => this.createMockEvent());
        }
        const clearEventsBtn = document.getElementById('clearEventsBtn');
        if (clearEventsBtn) {
            clearEventsBtn.addEventListener('click', () => this.clearEvents());
        }
        const severityFilter = document.getElementById('severityFilter');
        if (severityFilter) {
            severityFilter.addEventListener('change', (e) => {
                this.severityFilter = e.target.value;
                this.renderEvents(this.eventsCache);
            });
        }
        const timeline = document.getElementById('eventTimeline');
        if (timeline) {
            timeline.addEventListener('click', (e) => this.handleTimelineClick(e));
        }

        const emergencyFab = document.getElementById('emergencyFab');
        if (emergencyFab) {
            emergencyFab.addEventListener('click', () => {
                if (!this.isDriver()) {
                    return;
                }
                this.stop();
            });
        }

        const hapticToggle = document.getElementById('hapticToggle');
        if (hapticToggle) {
            hapticToggle.checked = this.hapticEnabled;
            hapticToggle.addEventListener('change', (e) => {
                this.hapticEnabled = e.target.checked;
            });
        }

        const soundToggle = document.getElementById('soundToggle');
        if (soundToggle) {
            soundToggle.checked = this.soundEnabled;
            soundToggle.addEventListener('change', (e) => {
                this.soundEnabled = e.target.checked;
                if (this.soundEnabled) {
                    this.playTone(740, 0.05, 0.03);
                }
            });
        }

        // Keyboard controls
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));
        document.addEventListener('keyup', (e) => this.handleKeyUp(e));

        window.addEventListener('online', () => {
            this.networkOnline = true;
            this.updateNetworkQuality();
            this.updateStatus();
        });
        window.addEventListener('offline', () => {
            this.networkOnline = false;
            this.isConnected = false;
            this.updateConnectionStatus();
            this.updateNetworkQuality();
        });
    }

    initializeAuth() {
        const loginBtn = document.getElementById('loginBtn');
        const pinInput = document.getElementById('pinInput');
        const logoutBtn = document.getElementById('logoutBtn');

        if (loginBtn) {
            loginBtn.addEventListener('click', () => this.login());
        }
        if (pinInput) {
            pinInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    this.login();
                }
            });
        }
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.logout());
        }

        this.applyRoleUIState();
    }

    authHeaders(extra = {}) {
        const headers = { ...extra };
        if (this.authToken) {
            headers.Authorization = `Bearer ${this.authToken}`;
        }
        return headers;
    }

    isDriver() {
        return this.userRole === 'driver';
    }

    setAuthError(message = '') {
        const authError = document.getElementById('authError');
        if (!authError) {
            return;
        }
        authError.textContent = message || 'Invalid PIN';
        authError.classList.toggle('show', Boolean(message));
    }

    applyRoleUIState() {
        const overlay = document.getElementById('authOverlay');
        const roleValue = document.getElementById('roleValue');
        const container = document.querySelector('.container');
        const emergencyFab = document.getElementById('emergencyFab');
        const isLoggedIn = Boolean(this.authToken && this.userRole);

        if (overlay) {
            overlay.classList.toggle('hidden', isLoggedIn);
        }
        if (roleValue) {
            roleValue.textContent = isLoggedIn
                ? this.userRole.charAt(0).toUpperCase() + this.userRole.slice(1)
                : 'Guest';
        }
        const controlsLocked = !isLoggedIn || !this.isDriver() || !this.isConnected || !this.networkOnline;
        if (container) {
            container.classList.toggle('viewer-mode', controlsLocked);
        }
        const controlButtons = [
            'forwardBtn',
            'backwardBtn',
            'leftBtn',
            'rightBtn',
            'stopBtn',
            'speedSlider'
        ];
        controlButtons.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.disabled = controlsLocked;
        });
        document.querySelectorAll('.speed-control .preset-btn').forEach(btn => {
            btn.disabled = controlsLocked;
        });
        if (emergencyFab) {
            emergencyFab.style.display = this.isDriver() ? 'block' : 'none';
        }
    }

    async login() {
        const pinInput = document.getElementById('pinInput');
        const pin = (pinInput?.value || '').trim();
        if (!pin) {
            this.setAuthError('Please enter PIN');
            return;
        }
        try {
            const response = await fetch(`${this.baseURL}/api/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pin })
            });
            if (!response.ok) {
                throw new Error('Invalid PIN');
            }
            const data = await response.json();
            this.authToken = data.token;
            this.userRole = data.role;
            localStorage.setItem('rr_auth_token', this.authToken);
            localStorage.setItem('rr_user_role', this.userRole);
            if (pinInput) {
                pinInput.value = '';
            }
            this.setAuthError('');
            this.applyRoleUIState();
            await this.updateStatus();
            await this.updateDiagnostics();
            await this.updateCameraStatus();
            await this.updateEvents();
        } catch (error) {
            this.setAuthError('Invalid PIN');
        }
    }

    async logout() {
        try {
            if (this.authToken) {
                await fetch(`${this.baseURL}/api/auth/logout`, {
                    method: 'POST',
                    headers: this.authHeaders({ 'Content-Type': 'application/json' })
                });
            }
        } catch (error) {
            console.warn('Logout request failed:', error);
        } finally {
            this.authToken = '';
            this.userRole = '';
            localStorage.removeItem('rr_auth_token');
            localStorage.removeItem('rr_user_role');
            this.applyRoleUIState();
            this.isConnected = false;
            this.updateConnectionStatus();
            this.renderDiagnosticsText('No data yet.', 'No data yet.');
            this.renderCameraState('not_connected', null);
            this.renderEvents([]);
        }
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
        if (endpoint.startsWith('/api/motor/') && !this.isDriver()) {
            const statusEl = document.getElementById('statusValue');
            if (statusEl) {
                statusEl.textContent = 'Driver login required';
            }
            this.triggerFeedback('error');
            return null;
        }
        if (!this.networkOnline || !this.isConnected) {
            this.triggerFeedback('error');
            return null;
        }
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                method: 'POST',
                headers: this.authHeaders({
                    'Content-Type': 'application/json',
                })
            });

            if (!response.ok) {
                if (response.status === 401 || response.status === 403) {
                    await this.logout();
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            document.getElementById('lastCommand').textContent = new Date().toLocaleTimeString();
            this.isConnected = true;
            this.updateConnectionStatus();
            this.applyRoleUIState();
            this.triggerFeedback('ok');
            
            return data;
        } catch (error) {
            console.error('Error sending command:', error);
            this.isConnected = false;
            this.updateConnectionStatus();
            this.applyRoleUIState();
            this.triggerFeedback('error');
        }
    }

    handleKeyDown(e) {
        if (!this.isDriver()) {
            return;
        }
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
        if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
            this.stop();
        }
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
        if (this.isConnected && this.networkOnline) {
            statusEl.textContent = 'Connected';
            statusEl.className = 'status-connected';
        } else if (!this.networkOnline) {
            statusEl.textContent = 'Offline';
            statusEl.className = 'status-disconnected';
        } else {
            statusEl.textContent = 'Reconnecting';
            statusEl.className = 'status-disconnected';
        }
    }

    async updateStatus() {
        if (!this.authToken) {
            this.isConnected = false;
            this.updateConnectionStatus();
            return;
        }
        try {
            const start = performance.now();
            const response = await fetch(`${this.baseURL}/api/status`, {
                headers: this.authHeaders()
            });
            if (response.ok) {
                const data = await response.json();
                const latency = performance.now() - start;
                this.recordLatency(latency);
                this.currentSpeed = data.speed;
                this.currentDirection = data.direction;
                this.userRole = data.role || this.userRole;
                
                document.getElementById('speedSlider').value = data.speed;
                document.getElementById('speedDisplay').textContent = data.speed;
                document.getElementById('speedValue').textContent = data.speed + '%';
                document.getElementById('directionValue').textContent = 
                    data.direction.charAt(0).toUpperCase() + data.direction.slice(1);
                
                this.isConnected = true;
                this.applyRoleUIState();
            } else if (response.status === 401 || response.status === 403) {
                await this.logout();
            }
            this.updateConnectionStatus();
            this.updateNetworkQuality();
            await this.updateCameraStatus();
        } catch (error) {
            console.error('Error updating status:', error);
            this.isConnected = false;
            this.updateConnectionStatus();
            this.updateNetworkQuality();
        }
    }

    startStatusPolling() {
        setInterval(() => this.updateStatus(), 2000);
        setInterval(() => this.updateDiagnostics(), 5000);
        setInterval(() => this.updateCameraStatus(), 4000);
        setInterval(() => this.updateEvents(), 5000);
    }

    getHostInfo() {
        const host = window.location.host;
        document.getElementById('hostInfo').textContent = host;
    }

    initializeTouchDrive() {
        const bindings = [
            { id: 'forwardBtn', cmd: () => this.moveForward(), dir: 'forward' },
            { id: 'backwardBtn', cmd: () => this.moveBackward(), dir: 'backward' },
            { id: 'leftBtn', cmd: () => this.turnLeft(), dir: 'left' },
            { id: 'rightBtn', cmd: () => this.turnRight(), dir: 'right' }
        ];

        bindings.forEach(({ id, cmd, dir }) => {
            const btn = document.getElementById(id);
            btn.addEventListener('pointerdown', (e) => {
                e.preventDefault();
                if (!this.isDriver()) {
                    return;
                }
                if (this.joystickActive) {
                    return;
                }
                this.activeDirection = dir;
                cmd();
            });
        });

        const stopOnRelease = (e) => {
            if (!this.activeDirection) {
                return;
            }
            if (this.joystickActive) {
                return;
            }
            e.preventDefault();
            this.activeDirection = null;
            this.stop();
        };

        document.addEventListener('pointerup', stopOnRelease);
        document.addEventListener('pointercancel', stopOnRelease);
        document.addEventListener('visibilitychange', () => {
            if (document.hidden && this.activeDirection) {
                this.activeDirection = null;
                this.stop();
            }
        });
    }

    initializeProfiles() {
        const profileButtons = document.querySelectorAll('.profile-btn');
        const profileNote = document.getElementById('profileNote');

        const applyProfile = (profile) => {
            if (!this.isDriver()) {
                return;
            }
            const config = this.profileConfig[profile];
            if (!config) {
                return;
            }
            this.activeProfile = profile;
            profileButtons.forEach((btn) => btn.classList.toggle('active', btn.dataset.profile === profile));
            profileNote.textContent = config.note;
            this.setSpeed(config.speed);
        };

        profileButtons.forEach((btn) => {
            btn.addEventListener('click', () => applyProfile(btn.dataset.profile));
        });

        applyProfile(this.activeProfile);
    }

    initializeJoystick() {
        const base = document.getElementById('joystickBase');
        const knob = document.getElementById('joystickKnob');
        if (!base || !knob) {
            return;
        }

        const recalculateGeometry = () => {
            const rect = base.getBoundingClientRect();
            this.joystickCenter = {
                x: rect.left + rect.width / 2,
                y: rect.top + rect.height / 2
            };
            this.joystickRadius = rect.width * 0.4;
        };

        const renderKnob = (x, y) => {
            knob.style.transform = `translate(calc(-50% + ${x}px), calc(-50% + ${y}px))`;
        };

        const resetJoystick = async () => {
            this.joystickActive = false;
            this.joystickPointerId = null;
            this.joystickVector = { x: 0, y: 0 };
            renderKnob(0, 0);
            if (this.joystickTicker) {
                clearInterval(this.joystickTicker);
                this.joystickTicker = null;
            }
            this.lastJoystickDirection = 'stop';
            this.lastJoystickSpeed = null;
            await this.stop();
        };

        const updateFromPoint = (clientX, clientY) => {
            let dx = clientX - this.joystickCenter.x;
            let dy = clientY - this.joystickCenter.y;
            const distance = Math.hypot(dx, dy);
            const maxDistance = this.joystickRadius;
            if (distance > maxDistance) {
                const scale = maxDistance / distance;
                dx *= scale;
                dy *= scale;
            }
            this.joystickVector = { x: dx / maxDistance, y: dy / maxDistance };
            renderKnob(dx, dy);
        };

        const tickJoystickCommand = async () => {
            const x = this.joystickVector.x;
            const y = this.joystickVector.y;
            const deadzone = 0.2;
            const magnitudeRaw = Math.min(1, Math.hypot(x, y));
            this.smoothedMagnitude =
                this.smoothedMagnitude + ((magnitudeRaw - this.smoothedMagnitude) * this.speedLerpAlpha);
            const magnitude = this.smoothedMagnitude;

            let direction = 'stop';
            if (magnitude >= deadzone) {
                if (Math.abs(y) >= Math.abs(x)) {
                    direction = y < 0 ? 'forward' : 'backward';
                } else {
                    direction = x < 0 ? 'left' : 'right';
                }
            }

            const profileSpeed = this.profileConfig[this.activeProfile].speed;
            const scaledSpeed = Math.max(0, Math.min(80, Math.round(profileSpeed * magnitude)));

            const now = performance.now();
            if (scaledSpeed !== this.lastJoystickSpeed && now - this.lastJoystickCommandAt >= this.joystickIntervalMs) {
                this.lastJoystickSpeed = scaledSpeed;
                await this.setSpeed(scaledSpeed);
                this.lastJoystickCommandAt = now;
            }

            if (direction === this.lastJoystickDirection) {
                return;
            }

            if (now - this.lastDirectionChangeAt < this.directionChangeCooldownMs) {
                return;
            }

            this.lastJoystickDirection = direction;
            this.lastDirectionChangeAt = now;

            if (direction === 'forward') {
                await this.moveForward();
            } else if (direction === 'backward') {
                await this.moveBackward();
            } else if (direction === 'left') {
                await this.turnLeft();
            } else if (direction === 'right') {
                await this.turnRight();
            } else {
                await this.stop();
            }
        };

        const onPointerDown = (e) => {
            if (!this.isDriver()) {
                return;
            }
            recalculateGeometry();
            this.joystickActive = true;
            this.joystickPointerId = e.pointerId;
            this.lastDirectionChangeAt = 0;
            this.lastJoystickCommandAt = 0;
            this.smoothedMagnitude = 0;
            base.setPointerCapture(e.pointerId);
            updateFromPoint(e.clientX, e.clientY);
            if (!this.joystickTicker) {
                this.joystickTicker = setInterval(() => {
                    tickJoystickCommand();
                }, this.joystickIntervalMs);
            }
        };

        const onPointerMove = (e) => {
            if (!this.joystickActive || e.pointerId !== this.joystickPointerId) {
                return;
            }
            updateFromPoint(e.clientX, e.clientY);
        };

        const onPointerUp = (e) => {
            if (e.pointerId !== this.joystickPointerId) {
                return;
            }
            resetJoystick();
        };

        base.addEventListener('pointerdown', onPointerDown);
        base.addEventListener('pointermove', onPointerMove);
        base.addEventListener('pointerup', onPointerUp);
        base.addEventListener('pointercancel', onPointerUp);
        window.addEventListener('resize', recalculateGeometry);
    }

    initializePWA() {
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/static/sw.js').catch((error) => {
                    console.warn('Service worker registration failed:', error);
                });
            });
        }
    }

    triggerFeedback(kind) {
        const now = performance.now();
        if (now - this.lastFeedbackAt < 75 && kind === 'ok') {
            return;
        }
        this.lastFeedbackAt = now;

        if (this.hapticEnabled && navigator.vibrate) {
            if (kind === 'ok') {
                navigator.vibrate(12);
            } else {
                navigator.vibrate([20, 25, 20]);
            }
        }

        if (this.soundEnabled) {
            if (kind === 'ok') {
                this.playTone(520, 0.04, 0.025);
            } else {
                this.playTone(280, 0.08, 0.05);
            }
        }
    }

    recordLatency(latencyMs) {
        this.latencyHistory.push(latencyMs);
        if (this.latencyHistory.length > this.maxLatencySamples) {
            this.latencyHistory.shift();
        }
        const avgLatency = this.latencyHistory.reduce((a, b) => a + b, 0) / this.latencyHistory.length;
        const latencyEl = document.getElementById('latencyValue');
        if (latencyEl) {
            latencyEl.textContent = `${Math.round(avgLatency)} ms`;
        }
    }

    updateNetworkQuality() {
        const el = document.getElementById('networkQuality');
        if (!el) {
            return;
        }
        if (!this.networkOnline) {
            el.textContent = 'Offline';
            return;
        }
        if (!this.isConnected || this.latencyHistory.length === 0) {
            el.textContent = 'Reconnecting';
            return;
        }
        const avgLatency = this.latencyHistory.reduce((a, b) => a + b, 0) / this.latencyHistory.length;
        if (avgLatency <= 120) {
            el.textContent = 'Excellent';
        } else if (avgLatency <= 260) {
            el.textContent = 'Good';
        } else if (avgLatency <= 500) {
            el.textContent = 'Fair';
        } else {
            el.textContent = 'Poor';
        }
    }

    renderDiagnosticsText(healthText, auditText) {
        const healthEl = document.getElementById('healthPayload');
        const auditEl = document.getElementById('auditPayload');
        if (healthEl) {
            healthEl.textContent = healthText;
        }
        if (auditEl) {
            auditEl.textContent = auditText;
        }
    }

    async updateDiagnostics() {
        if (!this.authToken) {
            return;
        }
        try {
            const [healthRes, auditRes] = await Promise.all([
                fetch(`${this.baseURL}/api/health`, { headers: this.authHeaders() }),
                fetch(`${this.baseURL}/api/audit`, { headers: this.authHeaders() })
            ]);

            if ((healthRes.status === 401 || healthRes.status === 403) || (auditRes.status === 401 || auditRes.status === 403)) {
                await this.logout();
                return;
            }

            if (!healthRes.ok || !auditRes.ok) {
                throw new Error('Diagnostics request failed');
            }

            const healthData = await healthRes.json();
            const auditData = await auditRes.json();

            const healthText = JSON.stringify(healthData, null, 2);
            const auditText = JSON.stringify(auditData.entries || [], null, 2);
            this.renderDiagnosticsText(healthText, auditText);
        } catch (error) {
            this.renderDiagnosticsText('Failed to fetch diagnostics.', 'Failed to fetch diagnostics.');
        }
    }

    async exportAuditLog() {
        if (!this.authToken) {
            return;
        }
        try {
            const response = await fetch(`${this.baseURL}/api/audit/export`, {
                headers: this.authHeaders()
            });
            if (response.status === 401 || response.status === 403) {
                await this.logout();
                return;
            }
            if (!response.ok) {
                throw new Error('Export failed');
            }

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `roborakshak-audit-${Date.now()}.json`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
            this.triggerFeedback('ok');
        } catch (error) {
            this.triggerFeedback('error');
        }
    }

    renderEvents(events) {
        const el = document.getElementById('eventTimeline');
        if (!el) {
            return;
        }
        if (!events || events.length === 0) {
            el.innerHTML = '<li class="event-item">No events yet.</li>';
            return;
        }
        const filtered = (events || []).filter((event) => {
            if (this.severityFilter === 'all') {
                return true;
            }
            return event.severity === this.severityFilter;
        });
        if (filtered.length === 0) {
            el.innerHTML = '<li class="event-item">No matching events.</li>';
            return;
        }
        const items = filtered
            .slice()
            .reverse()
            .map((event) => {
                const when = new Date(event.ts * 1000).toLocaleTimeString();
                const sev = event.severity || 'info';
                const ackClass = event.acknowledged ? 'acknowledged' : '';
                const ackLabel = event.acknowledged ? 'Acknowledged' : 'Acknowledge';
                const ackDisabled = (!this.isDriver() || event.acknowledged) ? 'disabled' : '';
                return `<li class="event-item ${sev} ${ackClass}">
                    <strong>[${sev.toUpperCase()}]</strong> ${event.message}
                    <div class="event-meta">
                        <small>${event.type} • ${when} • #${event.id}</small>
                        <button class="event-ack-btn" data-event-id="${event.id}" ${ackDisabled}>${ackLabel}</button>
                    </div>
                </li>`;
            });
        el.innerHTML = items.join('');
    }

    async updateEvents() {
        if (!this.authToken) {
            return;
        }
        try {
            const response = await fetch(`${this.baseURL}/api/events`, {
                headers: this.authHeaders()
            });
            if (response.status === 401 || response.status === 403) {
                await this.logout();
                return;
            }
            if (!response.ok) {
                throw new Error('Events request failed');
            }
            const data = await response.json();
            this.eventsCache = data.events || [];
            this.renderEvents(this.eventsCache);
        } catch (error) {
            this.renderEvents([]);
        }
    }

    async createMockEvent() {
        if (!this.isDriver()) {
            this.triggerFeedback('error');
            return;
        }
        try {
            const response = await fetch(`${this.baseURL}/api/events/mock`, {
                method: 'POST',
                headers: this.authHeaders({ 'Content-Type': 'application/json' }),
                body: JSON.stringify({
                    type: 'motion',
                    severity: 'warning',
                    message: 'Mock motion event detected'
                })
            });
            if (response.status === 401 || response.status === 403) {
                await this.logout();
                return;
            }
            if (!response.ok) {
                throw new Error('Mock event failed');
            }
            this.triggerFeedback('ok');
            await this.updateEvents();
            await this.updateDiagnostics();
        } catch (error) {
            this.triggerFeedback('error');
        }
    }

    async clearEvents() {
        if (!this.isDriver()) {
            this.triggerFeedback('error');
            return;
        }
        try {
            const response = await fetch(`${this.baseURL}/api/events/clear`, {
                method: 'POST',
                headers: this.authHeaders({ 'Content-Type': 'application/json' })
            });
            if (response.status === 401 || response.status === 403) {
                await this.logout();
                return;
            }
            if (!response.ok) {
                throw new Error('Clear events failed');
            }
            this.triggerFeedback('ok');
            await this.updateEvents();
            await this.updateDiagnostics();
        } catch (error) {
            this.triggerFeedback('error');
        }
    }

    async handleTimelineClick(e) {
        const target = e.target;
        if (!(target instanceof HTMLElement)) {
            return;
        }
        const eventId = target.dataset.eventId;
        if (!eventId) {
            return;
        }
        if (!this.isDriver()) {
            this.triggerFeedback('error');
            return;
        }
        try {
            const response = await fetch(`${this.baseURL}/api/events/ack/${eventId}`, {
                method: 'POST',
                headers: this.authHeaders({ 'Content-Type': 'application/json' })
            });
            if (response.status === 401 || response.status === 403) {
                await this.logout();
                return;
            }
            if (!response.ok) {
                throw new Error('Acknowledge failed');
            }
            this.triggerFeedback('ok');
            await this.updateEvents();
            await this.updateDiagnostics();
        } catch (error) {
            this.triggerFeedback('error');
        }
    }

    playTone(freq, duration, gainLevel) {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (!AudioCtx) {
            return;
        }
        if (!this.audioContext) {
            this.audioContext = new AudioCtx();
        }

        const ctx = this.audioContext;
        if (ctx.state === 'suspended') {
            ctx.resume().catch(() => {});
        }

        const oscillator = ctx.createOscillator();
        const gainNode = ctx.createGain();

        oscillator.type = 'sine';
        oscillator.frequency.value = freq;
        gainNode.gain.value = gainLevel;

        oscillator.connect(gainNode);
        gainNode.connect(ctx.destination);
        oscillator.start();
        oscillator.stop(ctx.currentTime + duration);
    }

    renderCameraState(state, snapshotTs) {
        const stateEl = document.getElementById('cameraStateValue');
        const snapEl = document.getElementById('cameraSnapshotValue');
        const feedEl = document.getElementById('cameraFeed');
        const hintEl = document.getElementById('cameraFeedHint');

        if (stateEl) {
            const labels = {
                not_connected: 'Not Connected',
                ready: 'Ready',
                streaming: 'Streaming'
            };
            stateEl.textContent = labels[state] || state || 'Unknown';
        }
        if (snapEl) {
            snapEl.textContent = snapshotTs ? new Date(snapshotTs * 1000).toLocaleString() : 'Never';
        }

        if (state === 'streaming' && feedEl) {
            feedEl.style.display = 'block';
            feedEl.src = `${this.baseURL}/api/camera/stream?ts=${Date.now()}`;
            if (hintEl) {
                hintEl.textContent = 'Live camera stream active.';
            }
        } else {
            if (feedEl) {
                feedEl.style.display = 'none';
                feedEl.src = '';
            }
            if (hintEl) {
                hintEl.textContent = state === 'ready'
                    ? 'Camera is ready. Start the stream to view live footage.'
                    : 'Start the stream to view live camera footage here.';
            }
        }
    }

    async updateCameraStatus() {
        if (!this.authToken) {
            return;
        }
        try {
            const response = await fetch(`${this.baseURL}/api/camera/status`, {
                headers: this.authHeaders()
            });
            if (response.status === 401 || response.status === 403) {
                await this.logout();
                return;
            }
            if (!response.ok) {
                throw new Error('Camera status failed');
            }
            const data = await response.json();
            this.renderCameraState(data.state, data.last_snapshot_ts);
        } catch (error) {
            this.renderCameraState('not_connected', null);
        }
    }

    async sendCameraCommand(endpoint) {
        if (!this.isDriver()) {
            this.triggerFeedback('error');
            return null;
        }
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                method: 'POST',
                headers: this.authHeaders({ 'Content-Type': 'application/json' })
            });
            if (response.status === 401 || response.status === 403) {
                await this.logout();
                return null;
            }
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || 'Camera command failed');
            }
            this.triggerFeedback('ok');
            this.renderCameraState(data.state, data.captured_at || null);
            await this.updateDiagnostics();
            return data;
        } catch (error) {
            this.triggerFeedback('error');
            return null;
        }
    }

    async cameraMarkReady() {
        await this.sendCameraCommand('/api/camera/ready');
        await this.updateCameraStatus();
    }

    async cameraStart() {
        await this.sendCameraCommand('/api/camera/start');
        await this.updateCameraStatus();
    }

    async cameraStop() {
        await this.sendCameraCommand('/api/camera/stop');
        await this.updateCameraStatus();
    }

    async cameraSnapshot() {
        await this.sendCameraCommand('/api/camera/snapshot');
        await this.updateCameraStatus();
    }

    async cameraTest() {
        if (!this.isDriver()) {
            this.triggerFeedback('error');
            return;
        }
        try {
            const response = await fetch(`${this.baseURL}/api/camera/test`, {
                method: 'POST',
                headers: this.authHeaders({ 'Content-Type': 'application/json' })
            });

            if (response.status === 401 || response.status === 403) {
                await this.logout();
                return;
            }

            const data = await response.json().catch(() => ({}));
            const resultEl = document.getElementById('cameraTestResult');
            if (resultEl) {
                if (response.ok) {
                    resultEl.textContent = data.message || 'Camera test passed';
                } else {
                    resultEl.textContent = data.message || `Camera test failed (${response.status})`;
                }
            }
            if (response.ok) {
                this.triggerFeedback('ok');
                this.renderCameraState(data.state, data.captured_at || null);
            } else {
                this.triggerFeedback('error');
            }
        } catch (error) {
            console.error('Camera test failed:', error);
            const resultEl = document.getElementById('cameraTestResult');
            if (resultEl) {
                resultEl.textContent = error.message || 'Camera test failed: network error';
            }
            this.triggerFeedback('error');
        }
    }

    initializeTabs() {
        const tabs = document.querySelectorAll('.tab-btn');
        const panels = document.querySelectorAll('.tab-panel');

        tabs.forEach((tab) => {
            tab.addEventListener('click', () => {
                const target = tab.dataset.tab;
                tabs.forEach((btn) => btn.classList.remove('active'));
                panels.forEach((panel) => panel.classList.remove('active'));
                tab.classList.add('active');
                const panel = document.getElementById(target);
                if (panel) {
                    panel.classList.add('active');
                }
            });
        });
    }
}

// Initialize controller when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const controller = new RoboRakshakController();
    controller.getHostInfo();
    console.log('RoboRakshak Control Panel Initialized');
});
