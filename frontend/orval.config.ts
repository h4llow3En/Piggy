import { defineConfig } from 'orval';

export default defineConfig({
    piggy: {
        input: './openapi.json',
        output: {
            target: 'src/api/piggy.ts',
            tsconfig: './tsconfig.app.json',
            client: 'react-query',
            httpClient: 'axios',
            mock: false,
            override: {
                mutator: {
                    path: 'src/api/axios-instance.ts',
                    name: 'customInstance',
                },
                useTypeOverInterfaces: true,
                operations: {
                    login_api_v1_users_login_post: {
                        mutator: {
                            path: 'src/api/axios-instance.ts',
                            name: 'customInstance',
                        },
                    },
                },
            },
        },
    },
});
