/**
 * API 客戶端
 * 封裝所有後端 API 呼叫
 */

const apiClient = {
    baseURL: '',
    
    /**
     * 發送 GET 請求
     */
    async get(endpoint) {
        const response = await axios.get(this.baseURL + endpoint);
        return response.data;
    },
    
    /**
     * 發送 POST 請求
     */
    async post(endpoint, data = null) {
        const response = await axios.post(this.baseURL + endpoint, data);
        return response.data;
    },
    
    /**
     * 發送 PUT 請求
     */
    async put(endpoint, data) {
        const response = await axios.put(this.baseURL + endpoint, data);
        return response.data;
    },
    
    /**
     * 發送 DELETE 請求
     */
    async delete(endpoint) {
        const response = await axios.delete(this.baseURL + endpoint);
        return response.data;
    },
    
    // ========== 配置管理 API ==========
    
    /**
     * 取得專案配置
     */
    async getConfig() {
        return await this.get('/api/admin/config');
    },
    
    /**
     * 更新配置 (部分更新)
     */
    async updateConfig(config) {
        return await this.put('/api/admin/config', config);
    },
    
    /**
     * 重置配置為預設值
     */
    async resetConfig() {
        return await this.post('/api/admin/config/reset');
    },
    
    // ========== 影片管理 API ==========
    
    /**
     * 取得影片列表
     */
    async getVideoList() {
        return await this.get('/api/admin/videos');
    },
    
    /**
     * 上傳影片
     */
    async uploadVideo(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await axios.post(
            this.baseURL + '/api/admin/videos/upload',
            formData,
            {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            }
        );
        return response.data;
    },
    
    /**
     * 刪除影片
     */
    async deleteVideo(filename) {
        return await this.delete(`/api/admin/videos/${filename}`);
    },
    
    /**
     * 設定當前播放影片
     */
    async setCurrentVideo(filename) {
        return await this.put(`/api/admin/videos/current/${filename}`);
    },
    
    /**
     * 取得影片詳細資訊
     */
    async getVideoInfo(filename) {
        return await this.get(`/api/admin/videos/${filename}/info`);
    },
    
    // ========== 距離偵測 API ==========
    
    /**
     * 取得當前距離資料快照
     */
    async getCurrentDistance() {
        return await this.get('/api/distance/current');
    },
    
    /**
     * 取得偵測統計資訊
     */
    async getDetectionStats() {
        return await this.get('/api/detection/stats');
    },
    
    /**
     * 建立 WebSocket 連線
     */
    createWebSocket(endpoint = '/ws/detection') {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}${endpoint}`;
        return new WebSocket(wsUrl);
    }
};

// 導出供其他模組使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = apiClient;
}
