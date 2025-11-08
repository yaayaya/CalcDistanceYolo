// ===== WebSocket 管理 =====
let ws = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;

// 偵測器啟動時間
let detectorStartTime = null;

// ===== 初始化 =====
document.addEventListener('DOMContentLoaded', () => {
    // 載入網路配置
    loadNetworkConfig();
    
    // 建立 WebSocket 連線
    connectWebSocket();
    
    // 綁定事件
    bindEvents();
    
    // 啟動運行時間計時器
    setInterval(updateUptime, 1000);
});

// ===== WebSocket 連線 =====
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/detection`;
    
    updateConnectionStatus('connecting', '連線中...');
    
    try {
        ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
            console.log('✅ WebSocket 已連線');
            updateConnectionStatus('connected', '已連線');
            reconnectAttempts = 0;
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            updateMonitorDisplay(data);
        };
        
        ws.onerror = (error) => {
            console.error('❌ WebSocket 錯誤:', error);
            updateConnectionStatus('disconnected', '連線錯誤');
        };
        
        ws.onclose = () => {
            console.log('⏹ WebSocket 已斷線');
            updateConnectionStatus('disconnected', '未連線');
            
            // 不自動重連,需手動刷新
            ws = null;
        };
        
    } catch (error) {
        console.error('❌ 建立 WebSocket 失敗:', error);
        updateConnectionStatus('disconnected', '連線失敗');
    }
}

// ===== 更新連線狀態 =====
function updateConnectionStatus(status, text) {
    const statusElement = document.getElementById('connection-status');
    const statusText = document.getElementById('status-text');
    
    statusElement.className = `connection-status ${status}`;
    statusText.textContent = text;
}

// ===== 更新監控顯示 =====
function updateMonitorDisplay(data) {
    // 偵測人數
    document.getElementById('total-count').textContent = data.total_count || 0;
    
    // 最近距離 (含顏色標示)
    const closestDistance = data.closest_distance || 0;
    const distanceElement = document.getElementById('closest-distance');
    distanceElement.textContent = closestDistance.toFixed(1);
    
    // 根據距離改變顏色
    distanceElement.className = 'status-value';
    if (closestDistance > 300) {
        distanceElement.classList.add('distance-safe');
    } else if (closestDistance > 150) {
        distanceElement.classList.add('distance-warning');
    } else if (closestDistance > 0) {
        distanceElement.classList.add('distance-danger');
    }
    
    // FPS
    const fps = data.fps || 0;
    const actualFps = data.actual_fps || 0;
    document.getElementById('fps-value').textContent = `${fps} / ${actualFps}`;
    
    // 記錄啟動時間
    if (!detectorStartTime && data.total_count !== undefined) {
        detectorStartTime = Date.now();
    }
}

// ===== 更新運行時間 =====
function updateUptime() {
    if (!detectorStartTime) {
        document.getElementById('uptime').textContent = '--:--:--';
        return;
    }
    
    const elapsed = Math.floor((Date.now() - detectorStartTime) / 1000);
    const hours = Math.floor(elapsed / 3600);
    const minutes = Math.floor((elapsed % 3600) / 60);
    const seconds = elapsed % 60;
    
    document.getElementById('uptime').textContent = 
        `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

// ===== 載入網路配置 =====
async function loadNetworkConfig() {
    try {
        const response = await fetch('/api/network-config');
        const result = await response.json();
        
        if (result.status === 'success' && result.data) {
            const config = result.data.websocket;
            document.getElementById('broadcast-interval').value = config.broadcast_interval || 33;
            document.getElementById('websocket-host').value = config.host || '0.0.0.0';
            document.getElementById('websocket-port').value = config.port || 8000;
        }
    } catch (error) {
        console.error('❌ 載入網路配置失敗:', error);
        showNotification('載入網路配置失敗', 'error');
    }
}

// ===== 儲存網路配置 =====
async function saveNetworkConfig(event) {
    event.preventDefault();
    
    const config = {
        websocket: {
            host: document.getElementById('websocket-host').value,
            port: parseInt(document.getElementById('websocket-port').value),
            broadcast_interval: parseInt(document.getElementById('broadcast-interval').value)
        }
    };
    
    try {
        const response = await fetch('/api/network-config', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            showNotification('網路配置已儲存,請手動刷新連線', 'success');
        } else {
            showNotification('儲存失敗: ' + result.message, 'error');
        }
    } catch (error) {
        console.error('❌ 儲存網路配置失敗:', error);
        showNotification('儲存網路配置失敗', 'error');
    }
}

// ===== 刷新 WebSocket 連線 =====
function refreshConnection() {
    if (ws) {
        ws.close();
        ws = null;
    }
    
    detectorStartTime = null;
    
    showNotification('正在重新建立連線...', 'info');
    
    setTimeout(() => {
        connectWebSocket();
    }, 500);
}

// ===== 重啟偵測器 =====
async function reloadDetector() {
    try {
        showNotification('正在重啟偵測器...', 'info');
        
        const response = await fetch('/api/detector/refresh', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            showNotification('偵測器已重啟,配置已重新載入', 'success');
            detectorStartTime = null;
        } else {
            showNotification('重啟失敗: ' + result.message, 'error');
        }
    } catch (error) {
        console.error('❌ 重啟偵測器失敗:', error);
        showNotification('重啟偵測器失敗', 'error');
    }
}

// ===== 查看 API 文件 =====
function viewDocs() {
    window.open('/docs', '_blank');
}

// ===== 顯示通知 =====
function showNotification(message, type = 'info') {
    // 簡易通知實作
    const notification = document.createElement('div');
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 25px;
        background: ${type === 'success' ? '#4ade80' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        z-index: 9999;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// ===== 綁定事件 =====
function bindEvents() {
    // 網路配置表單
    document.getElementById('network-config-form').addEventListener('submit', saveNetworkConfig);
    
    // 控制按鈕
    document.getElementById('btn-refresh-connection').addEventListener('click', refreshConnection);
    document.getElementById('btn-reload-detector').addEventListener('click', reloadDetector);
    document.getElementById('btn-view-docs').addEventListener('click', viewDocs);
}

// ===== CSS 動畫 =====
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
