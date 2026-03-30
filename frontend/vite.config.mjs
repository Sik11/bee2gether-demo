import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import * as vueCompiler from '@vue/compiler-sfc'

export default defineConfig({
  plugins: [
    vue({ compiler: vueCompiler }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) {
            return undefined;
          }
          if (id.includes('/vue/') || id.includes('@vue/')) {
            return 'vendor-vue';
          }
          if (id.includes('maplibre-gl')) {
            return 'vendor-map';
          }
          if (id.includes('@mdi/js')) {
            return 'vendor-icons';
          }
          return 'vendor-misc';
        },
      },
    },
  },
  server: {
    proxy: {
      '/api': {
        target: process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  }
})
