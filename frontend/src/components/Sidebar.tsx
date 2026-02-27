import React from 'react';
import {alpha, Box, IconButton} from '@mui/material';
import {ChartColumn, Coins, LogOut, PiggyBank, Repeat, Settings, TrendingUp, Wallet} from 'lucide-react';
import {useLocation, useNavigate} from 'react-router-dom';
import {useAuth} from '../context/AuthContext';

const Sidebar: React.FC = () => {
    const {logout} = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const isActive = (path: string) => location.pathname === path;

    return (
        <Box
            component="nav"
            sx={{
                width: {sm: 80},
                flexShrink: {sm: 0},
                bgcolor: (theme) => alpha(theme.palette.background.paper, theme.palette.mode === 'light' ? 0.6 : 0.8),
                backdropFilter: 'blur(15px)',
                borderRight: (theme) => `1px solid ${alpha(theme.palette.divider, theme.palette.mode === 'light' ? 0.1 : 0.05)}`,
                display: {xs: 'none', sm: 'flex'},
                flexDirection: 'column',
                alignItems: 'center',
                py: 4,
                gap: 4,
                height: '100vh',
                position: 'sticky',
                top: 0
            }}
        >
            <PiggyBank size={32} sx={{color: 'primary.main'}}/>

            <Box sx={{display: 'flex', flexDirection: 'column', gap: 2, flexGrow: 1}}>
                <IconButton
                    onClick={() => navigate('/')}
                    sx={{color: isActive('/') ? 'primary.main' : 'text.secondary'}}
                >
                    <Coins size={24}/>
                </IconButton>
                <IconButton
                    onClick={() => navigate('/statistics')}
                    sx={{color: isActive('/statistics') ? 'primary.main' : 'text.secondary'}}
                >
                    <ChartColumn size={24}/>
                </IconButton>
                <IconButton
                    onClick={() => navigate('/accounts')}
                    sx={{color: isActive('/accounts') ? 'primary.main' : 'text.secondary'}}
                >
                    <Wallet size={24}/>
                </IconButton>
                <IconButton
                    onClick={() => navigate('/budgets')}
                    sx={{color: isActive('/budgets') ? 'primary.main' : 'text.secondary'}}
                >
                    <TrendingUp size={24}/>
                </IconButton>
                <IconButton
                    onClick={() => navigate('/recurring-payments')}
                    sx={{color: isActive('/recurring-payments') ? 'primary.main' : 'text.secondary'}}
                >
                    <Repeat size={24}/>
                </IconButton>
                <IconButton
                    onClick={() => navigate('/settings')}
                    sx={{color: isActive('/settings') ? 'primary.main' : 'text.secondary'}}
                >
                    <Settings size={24}/>
                </IconButton>
            </Box>

            <IconButton onClick={handleLogout} sx={{color: 'text.secondary'}}><LogOut size={24}/></IconButton>
        </Box>
    );
};

export default Sidebar;
