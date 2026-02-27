import {BrowserRouter, Route, Routes} from 'react-router-dom';
import {CssBaseline, ThemeProvider, useMediaQuery} from '@mui/material';
import {LocalizationProvider} from '@mui/x-date-pickers';
import {AdapterDayjs} from '@mui/x-date-pickers/AdapterDayjs';
import {QueryClient, QueryClientProvider} from '@tanstack/react-query';
import {createAppTheme} from './theme/theme';
import {AuthProvider, useAuth} from './context/AuthContext';
import {NotificationProvider} from './context/NotificationContext';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import SettingsPage from './pages/SettingsPage';
import AccountsPage from './pages/AccountsPage';
import BudgetsPage from './pages/BudgetsPage';
import RecurringPaymentsPage from './pages/RecurringPaymentsPage';
import ProtectedRoute from './components/ProtectedRoute';
import MainLayout from './components/MainLayout';
import './App.css';
import {useMemo} from "react";
import StatisticsPage from "./pages/StatisticsPage.tsx";

const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: 1000 * 60 * 5, // 5 minutes
            gcTime: 1000 * 60 * 30, // 30 minutes
            refetchOnWindowFocus: false,
            retry: 1,
        },
    },
});

function AppContent() {
    const {themePreference} = useAuth();
    const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');

    const theme = useMemo(() => {
        let mode: 'light' | 'dark';
        if (themePreference === 'auto') {
            mode = prefersDarkMode ? 'dark' : 'light';
        } else {
            mode = themePreference;
        }
        return createAppTheme(mode);
    }, [themePreference, prefersDarkMode]);

    return (
        <ThemeProvider theme={theme}>
            <LocalizationProvider dateAdapter={AdapterDayjs}>
                <CssBaseline/>
                <BrowserRouter>
                    <Routes>
                        <Route path="/login" element={<LoginPage/>}/>
                        <Route
                            path="/"
                            element={
                                <ProtectedRoute>
                                    <MainLayout>
                                        <DashboardPage/>
                                    </MainLayout>
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/statistics"
                            element={
                                <ProtectedRoute>
                                    <MainLayout>
                                        <StatisticsPage/>
                                    </MainLayout>
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/accounts"
                            element={
                                <ProtectedRoute>
                                    <MainLayout>
                                        <AccountsPage/>
                                    </MainLayout>
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/budgets"
                            element={
                                <ProtectedRoute>
                                    <MainLayout>
                                        <BudgetsPage/>
                                    </MainLayout>
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/recurring-payments"
                            element={
                                <ProtectedRoute>
                                    <MainLayout>
                                        <RecurringPaymentsPage/>
                                    </MainLayout>
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/settings"
                            element={
                                <ProtectedRoute>
                                    <MainLayout>
                                        <SettingsPage/>
                                    </MainLayout>
                                </ProtectedRoute>
                            }
                        />
                    </Routes>
                </BrowserRouter>
            </LocalizationProvider>
        </ThemeProvider>
    );
}

function App() {
    return (
        <QueryClientProvider client={queryClient}>
            <NotificationProvider>
                <AuthProvider>
                    <AppContent/>
                </AuthProvider>
            </NotificationProvider>
        </QueryClientProvider>
    );
}

export default App;
