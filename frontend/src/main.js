import { createApp } from 'vue'
import 'maplibre-gl/dist/maplibre-gl.css'
import App from './App.vue'
import router from './router'

const app = createApp(App);
app.use(router);
globalThis.__beeRouter = router;
app.mount('#app');
