import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import react from '@astrojs/react';

export default defineConfig({
  site: 'https://buggysaharadxb.com',
  integrations: [
    tailwind(),
    react(),
  ],
  output: 'static',
  build: {
    assets: 'assets',
  },
  vite: {
    optimizeDeps: {
      include: ['three', 'gsap'],
    },
  },
});
