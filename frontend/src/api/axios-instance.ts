import axios, {type AxiosRequestConfig} from 'axios';
import {storage} from '../utils/storage';

export const AXIOS_INSTANCE = axios.create({
    baseURL: import.meta.env.VITE_API_URL || '',
});

// Request interceptor to add the auth token
AXIOS_INSTANCE.interceptors.request.use(
    (config) => {
        const token = storage.getToken();
        if (token) {
            config.headers = config.headers || {};
            if (!config.headers.Authorization) {
                config.headers.Authorization = `Bearer ${token}`;
            }
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor to handle token refresh
AXIOS_INSTANCE.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        // Dispatch a custom event for global error handling
        // Skip CanceledError as it is usually intentional (e.g. component unmount)
        if (typeof window !== 'undefined' && !originalRequest?._retry && !axios.isCancel(error)) {
            window.dispatchEvent(new CustomEvent('api-error', {detail: error}));
        }

        // If the error is 401 and we haven't tried refreshing the token yet
        if (error.response?.status === 401 && !originalRequest?._retry) {
            originalRequest._retry = true;

            const refreshToken = storage.getRefreshToken();

            if (refreshToken) {
                try {
                    // We use a separate axios object for the refresh to avoid interceptor loops
                    const response = await axios.post(`${AXIOS_INSTANCE.defaults.baseURL || ''}/api/v1/users/refresh-token`, {
                        refresh_token: refreshToken
                    });

                    const {access_token, refresh_token: newRefreshToken} = response.data;

                    // Store the new tokens
                    storage.setTokens(access_token, newRefreshToken, storage.isRemembered());

                    // Update the header for the original request
                    originalRequest.headers.Authorization = `Bearer ${access_token}`;

                    // Repeat the original request
                    return AXIOS_INSTANCE(originalRequest);
                } catch (refreshError) {
                    // If the refresh fails, log out the user
                    storage.clear();
                    window.location.href = '/login';
                    return Promise.reject(refreshError);
                }
            }
        }

        return Promise.reject(error);
    }
);

export const customInstance = <T>(
    config: AxiosRequestConfig,
    options?: AxiosRequestConfig,
): Promise<T> => {
    const promise = AXIOS_INSTANCE({
        ...config,
        ...options,
    }).then(({data}) => data);

    return promise;
};
