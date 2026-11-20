// Fallback configuration if not dynamically served by server.js
function normalizeApiBase(url) {
  if (!url) return 'http://localhost:3000/api';
  url = url.trim().replace(/\/+$/, '');
  if (!url.endsWith('/api')) {
    url += '/api';
  }
  return url;
}

if (typeof window.API_BASE === 'undefined') {
  window.API_BASE = normalizeApiBase(
    (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' || window.location.protocol === 'file:')
      ? 'http://localhost:3000/api'
      : (window.location.origin + '/api')
  );
} else {
  window.API_BASE = normalizeApiBase(window.API_BASE);
}
var API_BASE = window.API_BASE;

window.GOOGLE_CLIENT_ID = window.GOOGLE_CLIENT_ID || '918237465012-sampleclientid.apps.googleusercontent.com';

console.log('[Config] Active API_BASE:', window.API_BASE);
