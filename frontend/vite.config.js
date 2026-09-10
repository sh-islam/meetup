import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// base './' keeps asset paths relative, so the same build works at
// https://sh-islam.github.io/meetup/ and at <SERVER_COPY_URL>/
export default defineConfig({
  plugins: [svelte()],
  base: './',
  server: { port: 5173 },
})
