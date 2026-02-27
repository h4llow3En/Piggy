import React, {useState} from 'react';
import {
    alpha,
    AppBar,
    Box,
    Divider,
    Drawer,
    IconButton,
    List,
    ListItem,
    ListItemIcon,
    ListItemText,
    Toolbar,
    Typography
} from '@mui/material';
import {ChartColumn, Coins, LogOut, Menu, PiggyBank, Repeat, Settings, TrendingUp, Wallet, X} from 'lucide-react';
import {useLocation, useNavigate} from 'react-router-dom';
import {useAuth} from '../context/AuthContext';
import {useTranslation} from 'react-i18next';

const MobileHeader: React.FC = () => {
    const [drawerOpen, setDrawerOpen] = useState(false);
    const {logout} = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const {t} = useTranslation();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const isActive = (path: string) => location.pathname === path;

    const navItems = [
        {label: t('dashboard.title') || 'Dashboard', icon: <Coins size={24}/>, path: '/'},
        {label: t('statistics.title'), icon: <ChartColumn size={24}/>, path: '/statistics'},
        {label: t('accounts.title'), icon: <Wallet size={24}/>, path: '/accounts'},
        {label: t('budget.title'), icon: <TrendingUp size={24}/>, path: '/budgets'},
        {label: t('dashboard.recurring.title'), icon: <Repeat size={24}/>, path: '/recurring-payments'},
        {label: t('settings.title'), icon: <Settings size={24}/>, path: '/settings'},
    ];

    const toggleDrawer = (open: boolean) => (event: React.KeyboardEvent | React.MouseEvent) => {
        if (
            event.type === 'keydown' &&
            ((event as React.KeyboardEvent).key === 'Tab' || (event as React.KeyboardEvent).key === 'Shift')
        ) {
            return;
        }
        setDrawerOpen(open);
    };

    const drawerContent = (
        <Box
            sx={{width: 280, height: '100%', display: 'flex', flexDirection: 'column'}}
            role="presentation"
            onClick={toggleDrawer(false)}
            onKeyDown={toggleDrawer(false)}
        >
            <Box sx={{p: 2, display: 'flex', alignItems: 'center', gap: 2}}>
                <PiggyBank size={32} color="var(--mui-palette-primary-main, #7DB9E8)"/>
                <Typography variant="h6" sx={{fontWeight: 'bold', color: 'primary.main'}}>
                    Piggy
                </Typography>
                <Box sx={{flexGrow: 1}}/>
                <IconButton onClick={toggleDrawer(false)}>
                    <X size={24}/>
                </IconButton>
            </Box>
            <Divider/>
            <List sx={{flexGrow: 1, pt: 2}}>
                {navItems.map((item) => (
                    <ListItem
                        button
                        key={item.label}
                        onClick={() => item.path !== '#' && navigate(item.path)}
                        sx={{
                            my: 0.5,
                            mx: 1,
                            borderRadius: 2,
                            color: isActive(item.path) ? 'primary.main' : 'text.secondary',
                            bgcolor: (theme) => isActive(item.path) ? alpha(theme.palette.primary.main, 0.1) : 'transparent',
                            '&:hover': {
                                bgcolor: (theme) => alpha(theme.palette.primary.main, 0.05),
                            }
                        }}
                    >
                        <ListItemIcon sx={{color: 'inherit', minWidth: 45}}>
                            {item.icon}
                        </ListItemIcon>
                        <ListItemText
                            primary={item.label}
                            slotProps={{
                                primary: {
                                    fontWeight: isActive(item.path) ? 'bold' : 'medium'
                                }
                            }}
                        />
                    </ListItem>
                ))}
            </List>
            <Divider/>
            <List sx={{p: 1}}>
                <ListItem
                    button
                    onClick={handleLogout}
                    sx={{
                        borderRadius: 2,
                        color: 'error.main',
                        '&:hover': {
                            bgcolor: alpha('#f44336', 0.1),
                        }
                    }}
                >
                    <ListItemIcon sx={{color: 'inherit', minWidth: 45}}>
                        <LogOut size={24}/>
                    </ListItemIcon>
                    <ListItemText primary={t('dashboard.logout')} slotProps={{
                        primary: {fontWeight: 'medium'}
                    }}/>
                </ListItem>
            </List>
        </Box>
    );

    return (
        <>
            <AppBar
                position="sticky"
                sx={{
                    display: {xs: 'block', sm: 'none'},
                    background: (theme) => alpha(theme.palette.background.paper, 0.8),
                    backdropFilter: 'blur(15px)',
                    color: 'text.primary',
                    boxShadow: 'none',
                    borderBottom: (theme) => `1px solid ${alpha(theme.palette.divider, 0.1)}`,
                    zIndex: 1100
                }}
            >
                <Toolbar>
                    <IconButton
                        edge="start"
                        color="inherit"
                        aria-label="menu"
                        onClick={toggleDrawer(true)}
                        sx={{mr: 2}}
                    >
                        <Menu size={24}/>
                    </IconButton>
                    <Box sx={{display: 'flex', alignItems: 'center', gap: 1, flexGrow: 1}}>
                        <PiggyBank size={24} color="var(--mui-palette-primary-main, #7DB9E8)"/>
                        <Typography variant="h6" component="div" sx={{fontWeight: 'bold', color: 'primary.main'}}>
                            Piggy
                        </Typography>
                    </Box>
                </Toolbar>
            </AppBar>
            <Drawer
                anchor="left"
                open={drawerOpen}
                onClose={toggleDrawer(false)}
                slotProps={{
                    paper: {
                        sx: {
                            bgcolor: (theme) => alpha(theme.palette.background.paper, 0.95),
                            backdropFilter: 'blur(10px)',
                        }
                    }
                }}
            >
                {drawerContent}
            </Drawer>
        </>
    );
};

export default MobileHeader;
