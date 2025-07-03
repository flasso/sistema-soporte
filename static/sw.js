self.addEventListener('install', event => {
  console.log('Service Worker instalado');
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  console.log('Service Worker activo');
});

self.addEventListener('fetch', event => {
  // Aquí podrías cachear respuestas si quieres
});
