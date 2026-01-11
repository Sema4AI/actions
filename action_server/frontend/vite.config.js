/* eslint-disable import/no-extraneous-dependencies */
import { defineConfig } from 'vite';
import { viteSingleFile } from 'vite-plugin-singlefile';
import path from 'path';
import react from '@vitejs/plugin-react';

// Get tier from environment variable (set by build task)
const tier = process.env.TIER || 'community';
const isCommunity = tier === 'community';

// Custom plugin to enforce tier separation
function tierSeparationPlugin() {
  return {
    name: 'tier-separation',
    enforce: 'pre',
    resolveId(source, importer) {
      // Block enterprise imports in community builds
      if (isCommunity) {
        if (source.includes('@sema4ai/') || 
            source.includes('@/enterprise') || 
            source.includes('../enterprise')) {
          console.error(`❌ Enterprise import detected in community build: ${source}`);
          console.error(`   From: ${importer}`);
          throw new Error(
            `Enterprise imports not allowed in community tier: ${source}\n` +
            `This violates tier separation. Move shared code to @/shared or create a community alternative.`
          );
        }
      }
      return null;
    }
  };
}

export default defineConfig({
  define: {
    // Global __TIER__ variable for runtime checks
    __TIER__: JSON.stringify(tier),
  },
  server: {
    port: 8085,
    proxy: {
      '/api': 'http://localhost:8080',
      '/openapi.json': 'http://localhost:8080',
      '/config': 'http://localhost:8080',
      '/api/ws': {
        target: 'ws://localhost:8080',
        ws: true,
      },
    },
  },
  resolve: {
    alias: {
      '~': path.join(__dirname, 'src'),
      '@/core': path.join(__dirname, 'src/core'),
      '@/enterprise': path.join(__dirname, 'src/enterprise'),
      '@/shared': path.join(__dirname, 'src/shared'),
      '@/queries': path.join(__dirname, 'src/queries'),
    },
    mainFields: ['module', 'main', 'browser'],
  },
  plugins: [react(), tierSeparationPlugin(), viteSingleFile()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './__tests__/a11y/setup.ts',
  include: ['**/__tests__/**/*.test.*', '**/__tests__/**/*.spec.*'],
  // Visual tests using Playwright live under __tests__/visual and must be
  // executed by Playwright, not Vitest. Exclude them from Vitest's collector.
  exclude: ['**/__tests__/visual/**'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov'],
    },
  },
  build: {
    rollupOptions: {
      // Tree-shake enterprise code in community builds
      external: isCommunity ? [
        /@sema4ai\/.*/,
        /@\/enterprise\/.*/,
      ] : [],
      output: {
        // Deterministic bundle naming
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]',
      },
    },
  },
});
