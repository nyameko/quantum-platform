import { defineConfig } from 'astro/config';

export default defineConfig({
    site: 'https://quantum.nyameko.com',

    server: {
        host: '127.0.0.1',
        port: 4323,
        strictPort: true,
    },

    vite: {
        server: {
            proxy: {
                '/_allauth': {
                    target: 'http://127.0.0.1:8000',
                    changeOrigin: true,
                },
                '/api/v1': {
                    target: 'http://127.0.0.1:8000',
                    changeOrigin: true,
                },
                '/accounts': {
                    target: 'http://127.0.0.1:8000',
                    changeOrigin: true,
                },
            },
        },
    },
});
