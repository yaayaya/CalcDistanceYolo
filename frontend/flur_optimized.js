// FlurPaint 前端 - 使用 getUserMedia API 直接取得攝影機畫面
// 僅接收後端距離資料，大幅提升效能

// ===== 全域變數 =====
let ws = null;
let config = null;
let canvas = null;
let ctx = null;
let video = null;
let stream = null;
let animationFrameId = null;

// 當前距離與模糊參數
let currentDistance = 0;
let targetDistance = 0;
let smoothedDistance = 0;
let currentBlurRadius = 0;
let currentOpacity = 0;

// 距離平滑過渡配置
let DISTANCE_SMOOTH_SPEED = 0.15;
let DISTANCE_CHANGE_THRESHOLD = 10;

// FPS 計算
let frameCount = 0;
let lastFpsUpdate = performance.now();
let currentFps = 0;

// ===== 初始化 =====
document.addEventListener('DOMContentLoaded', async () => {
    canvas = document.getElementById('display-canvas');
    ctx = canvas.getContext('2d', { alpha: false, willReadFrequently: false });
    video = document.getElementById('video-source');
    
    await loadConfig();
    applyDisplaySettings();
    await initCamera();
    connectWebSocket();
    bindHotkeys();
});

// ===== 載入配置 =====
async function loadConfig() {
    try {
        const response = await fetch('/api/project-config');
        const result = await response.json();
        
        if (result.status === 'success') {
            config = result.data;
            if (config.distance_smoothing) {
                DISTANCE_SMOOTH_SPEED = config.distance_smoothing.smooth_speed || 0.15;
                DISTANCE_CHANGE_THRESHOLD = config.distance_smoothing.change_threshold || 10;
            }
            console.log('✅ 配置已載入');
        } else {
            useDefaultConfig();
        }
    } catch (error) {
        console.error('❌ 載入配置錯誤:', error);
        useDefaultConfig();
    }
}

function useDefaultConfig() {
    config = {
        distance_mapping: { min_distance: 50, max_distance: 500, easing_function: "linear" },
        display: { debug_mode: false, exhibition_mode: true },
        blur_overlay: { enabled: false, min_distance: 70, max_distance: 120, min_blur_radius: 0, max_blur_radius: 8, min_opacity: 0, max_opacity: 0.3, overlay_color: "#888888", easing_function: "ease-out", layer_count: 3, blend_mode: "normal" },
        canvas_filter: { enabled: true, min_distance: 70, max_distance: 120, min_blur_radius: 0, max_blur_radius: 5, easing_function: "ease-out", noise_enabled: true, min_noise_intensity: 0, max_noise_intensity: 0.08, noise_blend_mode: "overlay" },
        distance_smoothing: { enabled: true, smooth_speed: 0.15, change_threshold: 10 }
    };
}

// ===== 初始化攝影機 =====
async function initCamera() {
    try {
        // 取得後台設定的攝影機編號
        const cameraResponse = await fetch('/api/camera-selection');
        const cameraResult = await cameraResponse.json();
        
        let cameraId = 0;
        if (cameraResult.status === 'success') {
            cameraId = cameraResult.data.selected_camera || 0;
            console.log(`📹 使用攝影機: ${cameraId}`);
            updateDebugInfo('camera', `攝影機 ${cameraId}`);
        }
        
        // 取得可用的攝影機清單
        const devices = await navigator.mediaDevices.enumerateDevices();
        const videoDevices = devices.filter(device => device.kind === 'videoinput');
        
        console.log('📹 可用攝影機:', videoDevices);
        
        if (cameraId >= videoDevices.length) {
            console.warn(`⚠ 攝影機 ${cameraId} 不存在,使用預設攝影機`);
            cameraId = 0;
        }
        
        // 請求攝影機權限並啟動
        const constraints = {
            video: {
                deviceId: videoDevices[cameraId]?.deviceId ? { exact: videoDevices[cameraId].deviceId } : undefined,
                width: { ideal: 1920 },
                height: { ideal: 1080 },
                frameRate: { ideal: 30 }
            },
            audio: false
        };
        
        stream = await navigator.mediaDevices.getUserMedia(constraints);
        video.srcObject = stream;
        
        // 等待 video 載入
        await new Promise((resolve) => {
            video.onloadedmetadata = () => {
                console.log(`✅ 攝影機已啟動: ${video.videoWidth}x${video.videoHeight}`);
                updateDebugInfo('camera', `${cameraId} (${video.videoWidth}x${video.videoHeight})`);
                resolve();
            };
        });
        
        // 設定 Canvas 尺寸
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        updateDebugInfo('resolution', `${canvas.width} x ${canvas.height}`);
        
        // 隱藏載入提示
        document.getElementById('loading-overlay').classList.add('hidden');
        
        // 開始渲染循環
        startRenderLoop();
        
    } catch (error) {
        console.error('❌ 攝影機啟動失敗:', error);
        alert('無法啟動攝影機，請確認權限設定');
        document.getElementById('loading-overlay').querySelector('p').textContent = '攝影機啟動失敗';
    }
}

// ===== 套用顯示設定 =====
function applyDisplaySettings() {
    const debugOverlay = document.getElementById('debug-overlay');
    const exhibitionInfo = document.getElementById('exhibition-info');
    
    if (config.display.debug_mode) {
        debugOverlay.classList.add('active');
        exhibitionInfo.classList.remove('active');
    } else if (config.display.exhibition_mode) {
        debugOverlay.classList.remove('active');
        exhibitionInfo.classList.add('active');
    } else {
        debugOverlay.classList.remove('active');
        exhibitionInfo.classList.remove('active');
    }
}

// ===== WebSocket 連線 =====
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/flur`;
    
    updateConnectionUI('connecting');
    
    try {
        ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
            console.log('✅ WebSocket 已連線');
            updateConnectionUI('connected');
            updateDebugInfo('connection', '已連線');
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleDistanceData(data);
        };
        
        ws.onerror = (error) => {
            console.error('❌ WebSocket 錯誤:', error);
            updateConnectionUI('disconnected');
        };
        
        ws.onclose = () => {
            console.log('⏹ WebSocket 已斷線');
            updateConnectionUI('disconnected');
            setTimeout(connectWebSocket, 5000);
        };
        
    } catch (error) {
        console.error('❌ 建立 WebSocket 失敗:', error);
        updateConnectionUI('disconnected');
    }
}

// ===== 處理距離資料 =====
function handleDistanceData(data) {
    if (data.type !== 'distance_data') return;
    
    targetDistance = data.distance || 0;
    
    if (smoothedDistance === 0) {
        smoothedDistance = targetDistance;
    }
    
    const distanceDiff = Math.abs(targetDistance - smoothedDistance);
    if (distanceDiff > DISTANCE_CHANGE_THRESHOLD) {
        smoothedDistance += (targetDistance - smoothedDistance) * DISTANCE_SMOOTH_SPEED;
    } else {
        smoothedDistance = targetDistance;
    }
    
    currentDistance = smoothedDistance;
    updateDebugInfo('distance', `${targetDistance.toFixed(1)} cm → ${smoothedDistance.toFixed(1)} cm`);
    updateDebugInfo('count', data.total_count || 0);
}

// ===== 渲染循環 =====
function startRenderLoop() {
    function render() {
        drawFrame();
        
        frameCount++;
        const now = performance.now();
        const elapsed = now - lastFpsUpdate;
        if (elapsed >= 1000) {
            currentFps = Math.round((frameCount * 1000) / elapsed);
            frameCount = 0;
            lastFpsUpdate = now;
            updateDebugInfo('fps', currentFps);
        }
        
        animationFrameId = requestAnimationFrame(render);
    }
    
    render();
}

// ===== 繪製影像幀 =====
function drawFrame() {
    if (!video || video.readyState < 2) return;
    
    if (config.canvas_filter && config.canvas_filter.enabled) {
        applyCanvasFilter();
    } else {
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    }
    
    if (config.blur_overlay && config.blur_overlay.enabled) {
        drawBlurOverlay();
    }
}

// ===== 套用 Canvas Filter 模糊（GPU 加速）=====
function applyCanvasFilter() {
    const filterConfig = config.canvas_filter;
    
    const normalizedDistance = calculateNormalizedDistance(
        currentDistance,
        filterConfig.min_distance,
        filterConfig.max_distance
    );
    
    const easedValue = applyEasing(normalizedDistance, filterConfig.easing_function || 'ease-out');
    const blurRadius = lerp(filterConfig.max_blur_radius, filterConfig.min_blur_radius, easedValue);
    
    ctx.save();
    if (blurRadius > 0) {
        ctx.filter = `blur(${blurRadius}px)`;
    }
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    ctx.filter = 'none';
    ctx.restore();
    
    if (filterConfig.noise_enabled) {
        const noiseIntensity = lerp(
            filterConfig.max_noise_intensity,
            filterConfig.min_noise_intensity,
            easedValue
        );
        if (noiseIntensity > 0) {
            drawNoiseLayer(noiseIntensity, filterConfig.noise_blend_mode || 'overlay');
        }
    }
    
    updateDebugInfo('blur', `Canvas Filter: ${blurRadius.toFixed(1)} px`);
}

// ===== 繪製模糊圖層 =====
function drawBlurOverlay() {
    const overlay = config.blur_overlay;
    
    const normalizedDistance = calculateNormalizedDistance(
        currentDistance,
        overlay.min_distance,
        overlay.max_distance
    );
    
    const easedValue = applyEasing(normalizedDistance, overlay.easing_function);
    
    currentBlurRadius = lerp(overlay.max_blur_radius, overlay.min_blur_radius, easedValue);
    currentOpacity = lerp(overlay.max_opacity, overlay.min_opacity, easedValue);
    
    updateDebugInfo('blur', `${currentBlurRadius.toFixed(1)} px`);
    updateDebugInfo('opacity', `${(currentOpacity * 100).toFixed(1)}%`);
    
    if (currentBlurRadius > 0 && currentOpacity > 0) {
        const layerCount = overlay.layer_count || 3;
        const opacityPerLayer = currentOpacity / layerCount;
        
        for (let i = 0; i < layerCount; i++) {
            ctx.save();
            ctx.globalCompositeOperation = overlay.blend_mode || 'normal';
            ctx.globalAlpha = opacityPerLayer;
            
            const blurPerLayer = currentBlurRadius * (1 - i / layerCount * 0.3);
            ctx.filter = `blur(${blurPerLayer}px)`;
            
            ctx.fillStyle = overlay.overlay_color || '#888888';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            ctx.restore();
        }
        
        ctx.filter = 'none';
        ctx.globalAlpha = 1.0;
        ctx.globalCompositeOperation = 'source-over';
    }
}

// ===== 繪製噪點層 =====
let noiseCanvas = null;
let noiseCtx = null;

function drawNoiseLayer(intensity, blendMode) {
    if (!noiseCanvas || noiseCanvas.width !== canvas.width || noiseCanvas.height !== canvas.height) {
        noiseCanvas = document.createElement('canvas');
        noiseCanvas.width = canvas.width;
        noiseCanvas.height = canvas.height;
        noiseCtx = noiseCanvas.getContext('2d', { alpha: false });
    }
    
    const scale = 0.5;
    const noiseData = noiseCtx.createImageData(canvas.width * scale, canvas.height * scale);
    const pixels = noiseData.data;
    const intensityValue = 255 * intensity;
    
    for (let i = 0; i < pixels.length; i += 4) {
        const noise = (Math.random() - 0.5) * intensityValue;
        const gray = 128 + noise;
        pixels[i] = gray;
        pixels[i + 1] = gray;
        pixels[i + 2] = gray;
        pixels[i + 3] = 255;
    }
    
    noiseCtx.putImageData(noiseData, 0, 0);
    
    ctx.save();
    ctx.globalCompositeOperation = blendMode;
    ctx.drawImage(noiseCanvas, 0, 0, canvas.width, canvas.height);
    ctx.restore();
    ctx.globalCompositeOperation = 'source-over';
}

// ===== 計算正規化距離 (0-1) =====
function calculateNormalizedDistance(distance, minDist, maxDist) {
    if (distance <= minDist) return 0;
    if (distance >= maxDist) return 1;
    return (distance - minDist) / (maxDist - minDist);
}

// ===== 緩動函數 =====
function applyEasing(t, easingType) {
    switch (easingType) {
        case 'linear': return t;
        case 'ease-in': return t * t;
        case 'ease-out': return 1 - Math.pow(1 - t, 2);
        case 'ease-in-out': return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
        default: return t;
    }
}

// ===== 線性插值 =====
function lerp(start, end, t) {
    return start + (end - start) * t;
}

// ===== 更新連線狀態 UI =====
function updateConnectionUI(status) {
    const statusElement = document.getElementById('connection-status');
    statusElement.className = status;
    
    const statusText = {
        'connecting': '連線中...',
        'connected': '已連線',
        'disconnected': '連線中斷'
    };
    
    statusElement.textContent = statusText[status] || '未知狀態';
}

// ===== 更新除錯資訊 =====
function updateDebugInfo(key, value) {
    const element = document.getElementById(`debug-${key}`);
    if (element) {
        element.textContent = value;
    }
}

// ===== 綁定熱鍵 =====
function bindHotkeys() {
    document.addEventListener('keydown', (e) => {
        // Ctrl+Shift+D: 切換除錯模式
        if (e.ctrlKey && e.shiftKey && e.key === 'D') {
            config.display.debug_mode = !config.display.debug_mode;
            applyDisplaySettings();
            e.preventDefault();
        }
        
        // Ctrl+Shift+E: 切換展覽模式
        if (e.ctrlKey && e.shiftKey && e.key === 'E') {
            config.display.exhibition_mode = !config.display.exhibition_mode;
            applyDisplaySettings();
            e.preventDefault();
        }
    });
}

// ===== 清理資源 =====
window.addEventListener('beforeunload', () => {
    if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
    }
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }
    if (ws) {
        ws.close();
    }
});
