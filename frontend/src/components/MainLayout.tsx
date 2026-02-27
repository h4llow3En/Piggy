import React, {useCallback, useRef, useState} from 'react';
import {Box, CircularProgress} from '@mui/material';
import Sidebar from './Sidebar';
import MobileHeader from './MobileHeader';

interface MainLayoutProps {
    children: React.ReactNode;
}

const PULL_THRESHOLD = 150;

const MainLayout: React.FC<MainLayoutProps> = ({children}) => {
    const [pullDistance, setPullDistance] = useState(0);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const startY = useRef<number | null>(null);
    const mainContainerRef = useRef<HTMLDivElement>(null);

    const handleTouchStart = useCallback((e: React.TouchEvent) => {
        // Only if we are at the very top
        if (mainContainerRef.current && mainContainerRef.current.scrollTop === 0) {
            startY.current = e.touches[0].clientY;
        }
    }, []);

    const handleTouchMove = useCallback((e: React.TouchEvent) => {
        if (startY.current === null || isRefreshing) return;

        const currentY = e.touches[0].clientY;
        const diff = currentY - startY.current;

        if (diff > 0 && mainContainerRef.current && mainContainerRef.current.scrollTop === 0) {
            // Add resistance while pulling (logarithmic or simple factor)
            const newDistance = Math.min(diff * 0.5, PULL_THRESHOLD + 20);
            setPullDistance(newDistance);

            // Prevent default scrolling when "pulling"
            if (newDistance > 10) {
                if (e.cancelable) e.preventDefault();
            }
        } else {
            setPullDistance(0);
        }
    }, [isRefreshing]);

    const handleTouchEnd = useCallback(() => {
        if (pullDistance >= PULL_THRESHOLD && !isRefreshing) {
            setIsRefreshing(true);
            setPullDistance(PULL_THRESHOLD);

            // Small delay for the UI, then reload
            setTimeout(() => {
                window.location.reload();
            }, 500);
        } else {
            setPullDistance(0);
        }
        startY.current = null;
    }, [pullDistance, isRefreshing]);

    return (
        <Box sx={{
            display: 'flex',
            minHeight: '100vh',
            flexDirection: {xs: 'column', sm: 'row'},
            background: (theme) => theme.palette.mode === 'light'
                ? 'linear-gradient(135deg, #E3F2FD 0%, #FCE4EC 100%)'
                : 'linear-gradient(135deg, #121212 0%, #2D2D2D 100%)',
            backgroundAttachment: 'fixed',
            // Prevent native pull-to-refresh in some browsers, 
            // so our implementation takes precedence
            overscrollBehaviorY: 'contain'
        }}>
            <Sidebar/>
            <MobileHeader/>

            {/* Pull-to-refresh Indicator */}
            <Box sx={{
                position: 'fixed',
                top: pullDistance > 0 ? (pullDistance / 3) : -50,
                left: '50%',
                transform: 'translateX(-50%)',
                zIndex: 2000,
                opacity: Math.min(pullDistance / PULL_THRESHOLD, 1),
                transition: pullDistance === 0 ? 'top 0.3s ease-out, opacity 0.3s ease-out' : 'none',
                bgcolor: 'background.paper',
                borderRadius: '50%',
                p: 1,
                display: 'flex',
                boxShadow: 3
            }}>
                <CircularProgress
                    variant={isRefreshing ? "indeterminate" : "determinate"}
                    value={isRefreshing ? undefined : Math.min((pullDistance / PULL_THRESHOLD) * 100, 100)}
                    size={24}
                />
            </Box>

            <Box
                component="main"
                ref={mainContainerRef}
                onTouchStart={handleTouchStart}
                onTouchMove={handleTouchMove}
                onTouchEnd={handleTouchEnd}
                sx={{
                    flexGrow: 1,
                    p: {xs: 2, md: 4},
                    overflow: 'auto',
                    height: '100vh',
                    position: 'relative'
                }}
            >
                {children}
            </Box>
        </Box>
    );
};

export default MainLayout;
