import type {User} from "../api/piggy.ts";

const TOKEN_KEY = 'piggy_token';
const REFRESH_TOKEN_KEY = 'piggy_refresh_token';
const USER_KEY = 'piggy_user';

export const storage = {
    getToken: () => localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY),
    getRefreshToken: () => localStorage.getItem(REFRESH_TOKEN_KEY) || sessionStorage.getItem(REFRESH_TOKEN_KEY),
    getUser: () => {
        const user = localStorage.getItem(USER_KEY) || sessionStorage.getItem(USER_KEY);
        try {
            return user ? JSON.parse(user) : null;
            // eslint-disable-next-line @typescript-eslint/no-unused-vars
        } catch (e) {
            return null;
        }
    },
    setTokens: (token: string, refreshToken: string, rememberMe: boolean = false) => {
        const s = rememberMe ? localStorage : sessionStorage;
        const o = rememberMe ? sessionStorage : localStorage;

        s.setItem(TOKEN_KEY, token);
        s.setItem(REFRESH_TOKEN_KEY, refreshToken);

        o.removeItem(TOKEN_KEY);
        o.removeItem(REFRESH_TOKEN_KEY);
    },
    setUser: (user: User, rememberMe: boolean = false) => {
        const s = rememberMe ? localStorage : sessionStorage;
        const o = rememberMe ? sessionStorage : localStorage;

        const userStr = JSON.stringify(user);
        s.setItem(USER_KEY, userStr);
        o.removeItem(USER_KEY);
    },
    clear: () => {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
        sessionStorage.removeItem(TOKEN_KEY);
        sessionStorage.removeItem(REFRESH_TOKEN_KEY);
        sessionStorage.removeItem(USER_KEY);
    },
    isRemembered: () => !!localStorage.getItem(TOKEN_KEY)
};
