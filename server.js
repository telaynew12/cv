const http = require('http');
const fs = require('fs');
const path = require('path');

// 1. Parse .env file if it exists
function loadEnv() {
  const envPath = path.join(__dirname, '.env');
  const env = {};
  if (fs.existsSync(envPath)) {
    try {
      const content = fs.readFileSync(envPath, 'utf-8');
      const lines = content.split(/\r?\n/);
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith('#')) continue;
        const eqIdx = trimmed.indexOf('=');
        if (eqIdx > 0) {
          const key = trimmed.substring(0, eqIdx).trim();
          let val = trimmed.substring(eqIdx + 1).trim();
          if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
            val = val.slice(1, -1);
          }
          env[key] = val;
          if (!process.env[key]) {
            process.env[key] = val;
          }
        }
      }
    } catch (err) {
      console.warn('Could not parse .env file:', err.message);
    }
  }
  return env;
}

const envVars = loadEnv();

function getBackendUrl() {
  let url = process.env.BACKEND_URL || 
            process.env.API_URL || 
            envVars.BACKEND_URL || 
            envVars.API_URL || 
            'http://localhost:3000/api';
  url = url.trim().replace(/\/+$/, '');
  if (!url.endsWith('/api')) {
    url += '/api';
  }
  return url;
}

function getGoogleClientId() {
  return process.env.GOOGLE_CLIENT_ID ||
         process.env.VITE_GOOGLE_CLIENT_ID ||
         process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ||
         envVars.GOOGLE_CLIENT_ID ||
         envVars.VITE_GOOGLE_CLIENT_ID ||
         '918237465012-sampleclientid.apps.googleusercontent.com';
}

const port = process.env.PORT || 8080;

const mimeTypes = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.xml': 'application/xml; charset=utf-8',
  '.txt': 'text/plain; charset=utf-8'
};

const server = http.createServer((req, res) => {
  const safePath = req.url.split('?')[0];

  // Config endpoint: returns window.API_BASE & window.GOOGLE_CLIENT_ID read from .env
  if (safePath === '/config.js') {
    const backendUrl = getBackendUrl();
    const googleClientId = getGoogleClientId();
    res.writeHead(200, { 'Content-Type': 'application/javascript; charset=utf-8' });
    res.end(
      'window.API_BASE = "' + backendUrl + '";\n' +
      'window.GOOGLE_CLIENT_ID = "' + googleClientId + '";\n' +
      'console.log("[Config] Loaded API_BASE from .env:", window.API_BASE);\n' +
      'console.log("[Config] Loaded GOOGLE_CLIENT_ID from .env:", window.GOOGLE_CLIENT_ID);'
    );
    return;
  }

  let requestedPath = safePath;
  // Public Privacy Policy routes
  if (requestedPath === '/privacy' || requestedPath === '/privacy-policy') {
    requestedPath = '/privacy.html';
  }

  let filePath = path.join(__dirname, requestedPath === '/' ? 'index.html' : requestedPath);

  fs.stat(filePath, (err, stats) => {
    if (err || !stats.isFile()) {
      filePath = path.join(__dirname, 'index.html');
    }

    const ext = path.extname(filePath).toLowerCase();
    const contentType = mimeTypes[ext] || 'application/octet-stream';

    fs.readFile(filePath, (error, content) => {
      if (error) {
        res.writeHead(500, { 'Content-Type': 'text/plain' });
        res.end('Internal Server Error');
      } else {
        res.writeHead(200, { 'Content-Type': contentType });
        // Automatically inject window.API_BASE & window.GOOGLE_CLIENT_ID from .env into index.html
        if (filePath.endsWith('index.html')) {
          let html = content.toString('utf-8');
          const backendUrl = getBackendUrl();
          const googleClientId = getGoogleClientId();
          const injection = '<script>window.API_BASE = "' + backendUrl + '"; window.GOOGLE_CLIENT_ID = "' + googleClientId + '";</script></head>';
          html = html.replace('</head>', injection);
          res.end(html);
        } else {
          res.end(content);
        }
      }
    });
  });
});

server.listen(port, '0.0.0.0', () => {
  console.log('CVForge Frontend server running on port ' + port);
  console.log('Backend API URL configured from .env: ' + getBackendUrl());
  console.log('Google Client ID configured: ' + getGoogleClientId());
});
