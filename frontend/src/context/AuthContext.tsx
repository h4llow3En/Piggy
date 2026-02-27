import React, {createContext, useContext, useEffect, useState} from 'react';
import type {User} from '../api/piggy';
import {readUserMeApiV1UsersMeGet, updateUserMeApiV1UsersMePut} from '../api/piggy';
import i18n from '../i18n';
import {storage} from '../utils/storage';

interface AdditionalConfig {
    language?: string;
    theme?: 'light' | 'dark' | 'auto';
    dashboardMode?: 'current' | 'prognosis';

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    [key: string]: any;
}

interface AuthContextType {
    user: User | null;
    login: (token: string, refreshToken: string, user: User, rememberMe?: boolean) => void;
    logout: () => void;
    isAuthenticated: boolean;
    isLoading: boolean;
    changeLanguage: (lng: string) => Promise<void>;
    changeTheme: (theme: 'light' | 'dark' | 'auto') => Promise<void>;
    changeDashboardMode: (mode: 'current' | 'prognosis') => Promise<void>;
    themePreference: 'light' | 'dark' | 'auto';
    dashboardMode: 'current' | 'prognosis';
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const parseConfig = (configStr?: string | null): AdditionalConfig => {
    if (!configStr) return {};
    try {
        return JSON.parse(configStr);
    } catch (e) {
        console.error("Failed to parse additional_config", e);
        return {};
    }
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({children}) => {
    const [user, setUser] = useState<User | null>(null);
    const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [config, setConfig] = useState<AdditionalConfig>({});
    const [themePreference, setThemePreference] = useState<'light' | 'dark' | 'auto'>('auto');
    const [dashboardMode, setDashboardMode] = useState<'current' | 'prognosis'>('current');

    const login = (token: string, refreshToken: string, user: User, rememberMe: boolean = false) => {
        storage.setTokens(token, refreshToken, rememberMe);
        storage.setUser(user, rememberMe);

        setUser(user);
        setIsAuthenticated(true);

        const parsedConfig = parseConfig(user.additional_config);
        setConfig(parsedConfig);

        if (parsedConfig.language) {
            i18n.changeLanguage(parsedConfig.language);
        }

        if (parsedConfig.theme) {
            setThemePreference(parsedConfig.theme);
        }

        if (parsedConfig.dashboardMode) {
            setDashboardMode(parsedConfig.dashboardMode);
        }
    };

    const logout = () => {
        storage.clear();
        setUser(null);
        setIsAuthenticated(false);
        setConfig({});
    };

    useEffect(() => {
        const checkAuth = async () => {
            const token = storage.getToken();

            if (token) {
                try {
                    const userData = await readUserMeApiV1UsersMeGet();
                    setUser(userData);
                    setIsAuthenticated(true);

                    const parsedConfig = parseConfig(userData.additional_config);
                    setConfig(parsedConfig);

                    if (parsedConfig.language) {
                        i18n.changeLanguage(parsedConfig.language);
                    }

                    if (parsedConfig.theme) {
                        setThemePreference(parsedConfig.theme);
                    }

                    if (parsedConfig.dashboardMode) {
                        setDashboardMode(parsedConfig.dashboardMode);
                    }
                } catch (error) {
                    console.error("Auth initialization failed:", error);
                    // Log out on error (e.g. token expired)
                    logout();
                }
            }
            setIsLoading(false);
        };

        checkAuth();
    }, []);


    const changeLanguage = async (lng: string) => {
        await i18n.changeLanguage(lng);
        if (user) {
            const newConfig = {...config, language: lng};
            try {
                const updatedUser = await updateUserMeApiV1UsersMePut({
                    additional_config: JSON.stringify(newConfig)
                });
                setConfig(newConfig);
                setUser(updatedUser);
            } catch (error) {
                console.error("Failed to update language on server", error);
            }
        }
    };

    const changeTheme = async (theme: 'light' | 'dark' | 'auto') => {
        setThemePreference(theme);
        if (user) {
            const newConfig = {...config, theme: theme};
            try {
                const updatedUser = await updateUserMeApiV1UsersMePut({
                    additional_config: JSON.stringify(newConfig)
                });
                setConfig(newConfig);
                setUser(updatedUser);
            } catch (error) {
                console.error("Failed to update theme on server", error);
            }
        }
    };

    const changeDashboardMode = async (mode: 'current' | 'prognosis') => {
        setDashboardMode(mode);
        if (user) {
            const newConfig = {...config, dashboardMode: mode};
            try {
                const updatedUser = await updateUserMeApiV1UsersMePut({
                    additional_config: JSON.stringify(newConfig)
                });
                setConfig(newConfig);
                setUser(updatedUser);
            } catch (error) {
                console.error("Failed to update dashboard mode on server", error);
            }
        }
    };

    return (
        <AuthContext.Provider value={{
            user,
            login,
            logout,
            isAuthenticated,
            isLoading,
            changeLanguage,
            changeTheme,
            changeDashboardMode,
            themePreference,
            dashboardMode
        }}>
            {children}
        </AuthContext.Provider>
    );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
