import {createContext, type FC, type ReactNode, type SyntheticEvent, useCallback, useEffect, useState} from 'react';
import {Alert, type AlertColor, Snackbar} from '@mui/material';
import axios, {type AxiosError} from 'axios';
import type {ValidationError} from '../api/piggy';

type ApiErrorData = {
    detail?: string | ValidationError[];
};

interface NotificationContextType {
    showNotification: (message: string, severity?: AlertColor) => void;
    showError: (error: AxiosError<ApiErrorData> | string) => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export const NotificationProvider: FC<{ children: ReactNode }> = ({children}) => {
    const [open, setOpen] = useState(false);
    const [message, setMessage] = useState('');
    const [severity, setSeverity] = useState<AlertColor>('info');

    const showNotification = useCallback((msg: string, sev: AlertColor = 'info') => {
        setMessage(msg);
        setSeverity(sev);
        setOpen(true);
    }, []);

    const showError = useCallback((error: AxiosError<ApiErrorData> | string) => {
        if (typeof error !== 'string') {
            // Skip 401 errors as they are handled by AuthContext/Axios interceptor
            // BUT show them if we are on the login page (e.g. invalid credentials)
            const isLoginPage = typeof window !== 'undefined' && window.location.pathname === '/login';
            if (error.response?.status === 401 && !isLoginPage) return;

            // Skip CanceledErrors
            if (axios.isCancel(error)) return;
        }

        let errorMsg = 'An unexpected error occurred';

        if (typeof error === 'string') {
            errorMsg = error;
        } else if (error.response?.data?.detail) {
            const detail = error.response.data.detail;
            if (typeof detail === 'string') {
                errorMsg = detail;
            } else if (Array.isArray(detail) && detail.length > 0) {
                errorMsg = detail[0].msg;
            }
        } else if (error.message) {
            errorMsg = error.message;
        }

        showNotification(errorMsg, 'error');
    }, [showNotification]);

    useEffect(() => {
        const handleApiError = (event: Event) => {
            showError((event as CustomEvent<AxiosError<ApiErrorData>>).detail);
        };

        window.addEventListener('api-error', handleApiError);
        return () => {
            window.removeEventListener('api-error', handleApiError);
        };
    }, [showError]);

    const handleClose = (_?: SyntheticEvent | Event, reason?: string) => {
        if (reason === 'clickaway') {
            return;
        }
        setOpen(false);
    };

    return (
        <NotificationContext.Provider value={{showNotification, showError}}>
            {children}
            <Snackbar
                open={open}
                autoHideDuration={6000}
                onClose={handleClose}
                anchorOrigin={{vertical: 'bottom', horizontal: 'center'}}
            >
                <Alert
                    onClose={handleClose}
                    severity={severity}
                    sx={{
                        width: '100%',
                        borderRadius: 2,
                        boxShadow: (theme) => theme.shadows[3],
                        '&.MuiAlert-standardError': {
                            bgcolor: 'error.main',
                            color: 'error.contrastText',
                        },
                        '&.MuiAlert-standardSuccess': {
                            bgcolor: 'success.main',
                            color: 'success.contrastText',
                        },
                        '&.MuiAlert-standardWarning': {
                            bgcolor: 'warning.main',
                            color: 'warning.contrastText',
                        },
                        '&.MuiAlert-standardInfo': {
                            bgcolor: 'info.main',
                            color: 'info.contrastText',
                        },
                        '.MuiAlert-icon': {
                            color: 'inherit'
                        }
                    }}
                >
                    {message}
                </Alert>
            </Snackbar>
        </NotificationContext.Provider>
    );
};

// export const useNotification = () => {
//     const context = useContext(NotificationContext);
//     if (context === undefined) {
//         throw new Error('useNotification must be used within a NotificationProvider');
//     }
//     return context;
// };
