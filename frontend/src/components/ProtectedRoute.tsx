import React from 'react';
import {Navigate} from 'react-router-dom';
import {useAuth} from '../context/AuthContext';
import {LinearProgress} from '@mui/material';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({children}) => {
    const {isAuthenticated, isLoading} = useAuth();

    if (isLoading) {
        return <LinearProgress/>;
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" replace/>;
    }

    return <>{children}</>;
};

export default ProtectedRoute;
