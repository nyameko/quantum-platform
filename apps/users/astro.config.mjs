import { defineConfig } from 'astro/config';

export default defineConfig({
    site: 'https://users.quantum.nyameko.com',

    server: {
        host: '127.0.0.1',
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
            },
        },
    },
});
