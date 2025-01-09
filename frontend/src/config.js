// Default to '/api' if REACT_APP_API_URL is not set
const apiBaseUrl = window.__RUNTIME_CONFIG__?.REACT_APP_API_URL || '/api';
console.log('API_BASE_URL configured as:', apiBaseUrl);
export const API_BASE_URL = apiBaseUrl;
