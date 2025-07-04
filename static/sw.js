self.addEventListener('install', event => {
  console.log('✅ Service Worker instalado');
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  console.log('✅ Service Worker activado');
});

self.addEventListener('fetch', event => {
  // Puedes agregar aquí caché si lo deseas en el futuro
});

