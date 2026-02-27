import {alpha, createTheme} from '@mui/material/styles';

const getDesignTokens = (mode: 'light' | 'dark') => ({
    palette: {
        mode,
        ...(mode === 'light'
            ? {
                // Light Mode
                primary: {
                    main: '#7DB9E8',
                    contrastText: '#FFFFFF',
                },
                secondary: {
                    main: '#FFCCF9',
                    contrastText: '#5A5A5A',
                },
                error: {
                    main: '#FFABAB',
                    contrastText: '#4A4A4A',
                },
                warning: {
                    main: '#FFF5BA',
                    contrastText: '#4A4A4A',
                },
                info: {
                    main: '#C2F0C2',
                    contrastText: '#4A4A4A',
                },
                success: {
                    main: '#C2F0C2',
                    contrastText: '#4A4A4A',
                },
                background: {
                    default: '#FDFDFD',
                    paper: '#FFFFFF',
                },
                text: {
                    primary: '#4A4A4A',
                    secondary: '#7A7A7A',
                },
            }
            : {
                // Dark Mode - Pastel/Chalky tones
                primary: {
                    main: '#9BC4E2', // Slightly softer pastel blue
                    contrastText: '#2D2D2D',
                },
                secondary: {
                    main: '#E2B8DE', // Softer pastel pink
                    contrastText: '#2D2D2D',
                },
                error: {
                    main: '#D49B9B', // Softer pastel red
                    contrastText: '#1E1E1E',
                },
                warning: {
                    main: '#E2D9A3', // Softer pastel yellow
                    contrastText: '#1E1E1E',
                },
                info: {
                    main: '#A3C4A3', // Softer pastel green
                    contrastText: '#1E1E1E',
                },
                success: {
                    main: '#A3C4A3',
                    contrastText: '#1E1E1E',
                },
                background: {
                    default: '#1E1E1E', // Dark grey but not pitch black
                    paper: '#2D2D2D',
                },
                text: {
                    primary: '#E0E0E0',
                    secondary: '#B0B0B0',
                },
            }),
    },
    typography: {
        fontFamily: '"Raleway", "Inter", "Roboto", "Helvetica", "Arial", sans-serif',
        h1: {fontWeight: 600},
        h2: {fontWeight: 600},
        h3: {fontWeight: 600},
        h4: {fontWeight: 600},
        h5: {fontWeight: 600},
        h6: {fontWeight: 600},
    },
    shape: {
        borderRadius: 12,
    },
    components: {
        MuiButton: {
            styleOverrides: {
                root: {
                    textTransform: 'none',
                    borderRadius: 20,
                    boxShadow: 'none',
                    '&:hover': {
                        boxShadow: (mode === 'light'
                            ? `0px 2px 4px ${alpha('#000000', 0.05)}`
                            : `0px 2px 4px ${alpha('#000000', 0.3)}`),
                    },
                },
            },
        },
        MuiCard: {
            styleOverrides: {
                root: {
                    boxShadow: mode === 'light'
                        ? `0px 4px 20px ${alpha('#000000', 0.03)}`
                        : `0px 4px 20px ${alpha('#000000', 0.2)}`,
                    border: mode === 'light'
                        ? '1px solid #F0F0F0'
                        : '1px solid #3D3D3D',
                },
            },
        },
    },
});

export const createAppTheme = (mode: 'light' | 'dark') => createTheme(getDesignTokens(mode));

// Fallback for existing references
export const theme = createAppTheme('light');
