/**
 * APK U Lator — Frontend App Logic
 * All Python backend calls go through window.pywebview.api.*
 * which returns Promises (auto-wrapped by pywebview).
 */

const App = {

  // ── State ──────────────────────────────────────────────────
  state: {
    vmStatus: 'stopped',      // 'stopped' | 'running'
    adbStatus: 'disconnected',// 'disconnected' | 'connecting' | 'connected'
    activeTab: 'desktop',     // 'desktop' | 'mobile' | 'tv'
    activeSideNav: 'power',
    apkQueue: [],
    pollCount: 0,
  },

  api: null,

  // ── Bootstrap ──────────────────────────────────────────────
  async init() {
    // Wait for pywebview bridge to be ready
    if (window.pywebview) {
      this.api = window.pywebview.api;
      this._ready();
    } else {
      document.addEventListener('pywebviewready', () => {
        this.api = window.pywebview.api;
        this._ready();
      });
    }
  },

  _ready() {
    this._bindEvents();
    this._startClock();
    this._startPolling();
    this._addLog('✓ APK U Lator UI ready.');
  },

  // ── Event Wiring ───────────────────────────────────────────
  _bindEvents() {
    // Top nav tabs
    document.querySelectorAll('[data-tab]').forEach(el =>
      el.addEventListener('click', () => this.switchTab(el.dataset.tab))
    );

    // Sidebar nav
    document.querySelectorAll('[data-nav]').forEach(el =>
      el.addEventListener('click', () => this.switchSideNav(el.dataset.nav))
    );

    // Sidebar action buttons
    safeOn('btn-power',      () => this.handlePower());
    safeOn('btn-adb',        () => this.handleADB());
    safeOn('btn-screenshot', () => this.handleScreenshot());
    safeOn('btn-restart',    () => this.handleRestart());
    safeOn('btn-gps',        () => this.showModal('gps-modal'));
    safeOn('btn-keyboard',   () => this.showModal('keyboard-modal'));

    // Bottom bar
    safeOn('btn-install',    () => this.handleInstall());
    safeOn('btn-library',    () => this.handleLibrary());

    // Install modal
    safeOn('install-confirm', () => this.confirmInstall());
    safeOn('install-cancel',  () => this.hideModal('install-modal'));

    // GPS modal
    safeOn('gps-confirm', () => this.confirmGPS());
    safeOn('gps-cancel',  () => this.hideModal('gps-modal'));

    // Keyboard modal key buttons
    document.querySelectorAll('[data-keycode]').forEach(el =>
      el.addEventListener('click', () => this.sendKey(parseInt(el.dataset.keycode)))
    );

    // Library modal close
    safeOn('library-close', () => this.hideModal('library-modal'));

    // Viewport first-boot button
    safeOn('btn-first-boot', () => this.handleFirstBoot());
  },

  // ── Clock ──────────────────────────────────────────────────
  _startClock() {
    const DAYS   = ['SUNDAY','MONDAY','TUESDAY','WEDNESDAY','THURSDAY','FRIDAY','SATURDAY'];
    const MONTHS = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];

    const tick = () => {
      const now = new Date();
      setTextContent('clock-time',
        now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })
      );
      setTextContent('clock-date',
        `${DAYS[now.getDay()]}, ${MONTHS[now.getMonth()]} ${now.getDate()}`
      );
    };
    tick();
    setInterval(tick, 1000);
  },

  // ── Stats Polling (500 ms) ─────────────────────────────────
  _startPolling() {
    setInterval(async () => {
      if (!this.api) return;
      try {
        const [stats, logs] = await Promise.all([
          this.api.get_stats(),
          this.api.get_logs(),
        ]);
        this._applyStats(stats);
        if (logs && logs.length) logs.forEach(l => this._addLog(l));
        this.state.pollCount++;
      } catch (_) { /* ignore transient errors */ }
    }, 500);
  },

  // ── Apply Stats to UI ──────────────────────────────────────
  _applyStats(s) {
    if (!s) return;
    const { cpu_pct, ram_used_gb, ram_total_gb, vm_status, adb_status, vm_pid } = s;

    this.state.vmStatus  = vm_status;
    this.state.adbStatus = adb_status;

    // CPU bar
    setWidth('cpu-bar', `${cpu_pct}%`);
    setTextContent('cpu-label', `${cpu_pct.toFixed(1)}%`);

    // RAM bar
    const ramPct = ram_total_gb > 0 ? (ram_used_gb / ram_total_gb) * 100 : 0;
    setWidth('ram-bar', `${ramPct.toFixed(1)}%`);
    setTextContent('ram-label', `${ram_used_gb} GB / ${ram_total_gb} GB`);

    // Diagnostics status dot
    const dot = document.getElementById('status-dot');
    if (dot) {
      dot.className = vm_status === 'running'
        ? 'flex h-2 w-2 rounded-full bg-green-500 animate-pulse'
        : 'flex h-2 w-2 rounded-full bg-slate-600';
    }

    // Viewport
    this._updateViewport(vm_status, vm_pid, adb_status);

    // Power button label
    const powerLabel = document.getElementById('power-label');
    if (powerLabel) {
      powerLabel.textContent = vm_status === 'running' ? 'Stop VM' : 'Power';
    }
    const powerBtn = document.getElementById('btn-power');
    if (powerBtn) {
      powerBtn.className = vm_status === 'running'
        ? 'nav-btn-active flex items-center gap-3 py-3 w-full cursor-pointer text-red-400 border-l-red-400 bg-red-400/5'
        : 'nav-btn-active flex items-center gap-3 py-3 w-full cursor-pointer';
    }

    // ADB button label
    const adbLabel = document.getElementById('adb-label');
    if (adbLabel) {
      adbLabel.textContent =
        adb_status === 'connected'   ? 'ADB ✓' :
        adb_status === 'connecting'  ? 'ADB…'  : 'ADB';
    }
  },

  _updateViewport(vmStatus, vmPid, adbStatus) {
    const stopped = document.getElementById('viewport-stopped');
    const running = document.getElementById('viewport-running');
    if (!stopped || !running) return;

    if (vmStatus === 'running') {
      stopped.classList.add('hidden');
      running.classList.remove('hidden');
      setTextContent('vm-pid',        vmPid || '—');
      const adbEl = document.getElementById('vm-adb-badge');
      if (adbEl) {
        adbEl.textContent  = adbStatus === 'connected' ? '● ADB Connected' : '○ ADB Disconnected';
        adbEl.className    = adbStatus === 'connected'
          ? 'text-xs text-cyan-400 font-mono'
          : 'text-xs text-slate-500 font-mono';
      }
    } else {
      stopped.classList.remove('hidden');
      running.classList.add('hidden');
    }
  },

  // ── Log Panel ──────────────────────────────────────────────
  _addLog(msg) {
    const container = document.getElementById('log-stream');
    if (!container) return;

    const now = new Date();
    const ts  = now.toLocaleTimeString('en-US', { hour12: false });

    const line = document.createElement('div');
    line.textContent = `[${ts}] ${msg}`;
    line.className   = this._logColour(msg);

    container.appendChild(line);

    // Trim to last 300 lines
    while (container.children.length > 300) {
      container.removeChild(container.firstChild);
    }
    container.scrollTop = container.scrollHeight;
  },

  _logColour(msg) {
    if (/✓|Connected|started|created|ready/i.test(msg))  return 'text-green-400/80';
    if (/✗|WARN|Error|fail|not found/i.test(msg))         return 'text-red-400/80';
    if (/\[ADB\]|\[VM\]|\[Init\]|DEBUG/i.test(msg))       return 'text-cyan-400/80';
    if (/ℹ|screenshot|GPS/i.test(msg))                     return 'text-amber-400/80';
    return 'text-slate-400';
  },

  // ── Actions ────────────────────────────────────────────────
  async handlePower() {
    if (this.state.vmStatus === 'running') {
      this._addLog('Stopping VM…');
      const r = await this.api.vm_stop();
      this._addLog(r.message);
    } else {
      this._addLog('Starting VM…');
      const r = await this.api.vm_start();
      this._addLog(r.message);
    }
  },

  async handleFirstBoot() {
    this._addLog('Starting first boot from ISO…');
    const r = await this.api.vm_first_boot();
    this._addLog(r.message);
  },

  async handleADB() {
    if (this.state.adbStatus === 'connected') {
      const r = await this.api.adb_disconnect();
      this._addLog(r.message);
    } else {
      this.state.adbStatus = 'connecting';
      const adbLabel = document.getElementById('adb-label');
      if (adbLabel) adbLabel.textContent = 'ADB…';
      const r = await this.api.adb_connect();
      this._addLog(r.message);
    }
  },

  async handleScreenshot() {
    this._addLog('Capturing screenshot…');
    const r = await this.api.take_screenshot();
    if (r.ok) this._addLog(`✓ Saved: ${r.path}`);
  },

  async handleRestart() {
    this._addLog('Restarting VM…');
    const r = await this.api.vm_restart();
    this._addLog(r.message);
  },

  async handleInstall() {
    const paths = await this.api.browse_apk();
    if (!paths || paths.length === 0) return;
    this.state.apkQueue = paths;

    // Populate the install modal queue list
    const list = document.getElementById('install-queue');
    if (list) {
      list.innerHTML = '';
      paths.forEach(p => {
        const name = p.split(/[\\/]/).pop();
        const item = document.createElement('div');
        item.className = 'flex items-center gap-3 p-3 bg-white/5 rounded-lg border border-white/5';
        item.innerHTML = `
          <span class="material-symbols-outlined text-cyan-400 text-lg">android</span>
          <span class="text-sm text-slate-300 truncate flex-1">${name}</span>
          <span class="text-xs text-slate-500 font-mono">APK</span>`;
        list.appendChild(item);
      });
    }
    this.showModal('install-modal');
  },

  async confirmInstall() {
    this.hideModal('install-modal');
    for (const path of this.state.apkQueue) {
      const name = path.split(/[\\/]/).pop();
      this._addLog(`Installing ${name}…`);
      const r = await this.api.install_apk(path);
      this._addLog(r.ok ? `✓ ${name} installed.` : `✗ ${name}: ${r.message}`);
    }
    this.state.apkQueue = [];
  },

  async handleLibrary() {
    const list = document.getElementById('library-list');
    if (!list) return;
    list.innerHTML = '<div class="text-slate-500 text-xs p-4">Fetching packages…</div>';
    this.showModal('library-modal');

    const pkgs = await this.api.get_installed_packages();
    list.innerHTML = '';
    if (!pkgs || pkgs.length === 0) {
      list.innerHTML = '<div class="text-slate-500 text-xs p-4">No third-party packages installed.</div>';
      return;
    }
    pkgs.forEach(p => {
      const item = document.createElement('div');
      item.className = 'flex items-center gap-3 p-3 border-b border-white/5 hover:bg-white/5 transition-colors';
      item.innerHTML = `
        <span class="material-symbols-outlined text-cyan-400/60 text-base">android</span>
        <span class="text-xs font-mono text-slate-300 flex-1 truncate">${p.name}</span>`;
      list.appendChild(item);
    });
  },

  async confirmGPS() {
    const lat = parseFloat(document.getElementById('gps-lat')?.value || '0');
    const lng = parseFloat(document.getElementById('gps-lng')?.value || '0');
    if (isNaN(lat) || isNaN(lng)) return;
    const r = await this.api.set_gps_location(lat, lng);
    this._addLog(r.message);
    this.hideModal('gps-modal');
  },

  async sendKey(keycode) {
    await this.api.send_key_event(keycode);
  },

  // ── Tab / Nav switching ────────────────────────────────────
  switchTab(tab) {
    this.state.activeTab = tab;
    document.querySelectorAll('[data-tab]').forEach(el => {
      const active = el.dataset.tab === tab;
      el.className = active
        ? 'text-cyan-400 border-b-2 border-cyan-400 pb-1 font-bold text-sm flex items-center gap-2 cursor-pointer'
        : 'text-slate-400 hover:text-white transition-colors text-sm flex items-center gap-2 cursor-pointer';
    });
    this._addLog(`Switched to ${tab.charAt(0).toUpperCase() + tab.slice(1)} view.`);
  },

  switchSideNav(nav) {
    this.state.activeSideNav = nav;
    document.querySelectorAll('[data-nav]').forEach(el => {
      const active = el.dataset.nav === nav;
      el.classList.toggle('nav-btn-active', active);
      el.classList.toggle('nav-btn', !active);
    });
  },

  // ── Modal helpers ──────────────────────────────────────────
  showModal(id)  { document.getElementById(id)?.classList.remove('hidden'); },
  hideModal(id)  { document.getElementById(id)?.classList.add('hidden'); },
};

// ── DOM helpers ─────────────────────────────────────────────
function safeOn(id, fn) {
  const el = document.getElementById(id);
  if (el) el.addEventListener('click', fn);
}
function setTextContent(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}
function setWidth(id, w) {
  const el = document.getElementById(id);
  if (el) el.style.width = w;
}

// ── Boot ────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => App.init());
window.App = App;
