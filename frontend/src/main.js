import { createApp } from 'vue'
import 'maplibre-gl/dist/maplibre-gl.css'
import App from './App.vue'
import router from './router'

const app = createApp(App);
app.use(router);
globalThis.__beeRouter = router;

async function bootstrap() {
  const targetRoute = `${window.location.pathname}${window.location.search}${window.location.hash}`;
  if (!router.currentRoute.value.matched.length && targetRoute !== router.currentRoute.value.fullPath) {
    try {
      await router.replace(targetRoute);
    } catch (error) {
      console.error('Failed to sync initial route', error);
    }
  }

  await router.isReady();
  app.mount('#app');
}

bootstrap();
