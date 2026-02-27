import React, {useEffect, useState} from 'react';
import {
    Alert,
    Box,
    Button,
    Card,
    CardContent,
    Checkbox,
    Container,
    FormControlLabel,
    IconButton,
    InputAdornment,
    LinearProgress,
    TextField,
    Typography
} from '@mui/material';
import {Eye, EyeOff, Lock, Mail, PiggyBank, User} from 'lucide-react';
import {useAuth} from '../context/AuthContext';
import {useNavigate, useSearchParams} from 'react-router-dom';
import {readUserMeApiV1UsersMeGet, useLoginApiV1UsersLoginPost, useRegisterApiV1UsersRegisterPost} from '../api/piggy';
import {useTranslation} from 'react-i18next';

const LoginPage: React.FC = () => {
    const {t} = useTranslation();
    const [isLogin, setIsLogin] = useState(true);
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [repeatPassword, setRepeatPassword] = useState('');
    const [rememberMe, setRememberMe] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    const {login, isAuthenticated, isLoading} = useAuth();
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();

    useEffect(() => {
        if (!isLoading && isAuthenticated) {
            navigate('/');
        }
    }, [isAuthenticated, isLoading, navigate]);

    useEffect(() => {
        const verified = searchParams.get('verified');
        const token = searchParams.get('token');
        const errorParam = searchParams.get('error');

        if (verified === 'true') {
            // eslint-disable-next-line react-hooks/set-state-in-effect
            setSuccess(t('login.verificationSuccess'));
            if (token) {
                setError(null);
            }
        } else if (verified === 'false') {
            if (errorParam === 'invalid_token') {
                setError(t('errors.invalid_verification_token'));
            } else {
                setError(t('login.verificationError'));
            }
        }
    }, [searchParams, t]);

    const loginMutation = useLoginApiV1UsersLoginPost();
    const registerMutation = useRegisterApiV1UsersRegisterPost();

    const handleLogin = async (emailToUse: string, passwordToUse: string) => {
        try {
            const response = await loginMutation.mutateAsync({
                data: {
                    username: emailToUse,
                    password: passwordToUse,
                    grant_type: 'password'
                }
            });

            if (response.access_token && response.refresh_token) {
                const storage = rememberMe ? localStorage : sessionStorage;
                storage.setItem('piggy_token', response.access_token);
                storage.setItem('piggy_refresh_token', response.refresh_token);

                try {
                    const userData = await readUserMeApiV1UsersMeGet();
                    login(response.access_token, response.refresh_token, userData, rememberMe);
                    navigate('/');
                    // eslint-disable-next-line @typescript-eslint/no-unused-vars
                } catch (_error) {
                    // Error handled globally via interceptor
                    storage.removeItem('piggy_token');
                    storage.removeItem('piggy_refresh_token');
                }
            }
            // eslint-disable-next-line @typescript-eslint/no-unused-vars
        } catch (_error) {
            // Error handled globally via interceptor
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setSuccess(null);

        if (isLogin) {
            await handleLogin(email, password);
        } else {
            if (password !== repeatPassword) {
                setError(t('login.passwordsDoNotMatch'));
                return;
            }
            try {
                const registeredUser = await registerMutation.mutateAsync({
                    data: {
                        name: name,
                        email: email,
                        password: password
                    }
                });

                if (registeredUser.is_active && registeredUser.email_verified) {
                    setSuccess(t('login.registerSuccessFirstUser'));
                    await handleLogin(email, password);
                } else {
                    setSuccess(t('login.registerSuccess'));
                    setIsLogin(true);
                    setName('');
                    setPassword('');
                    setRepeatPassword('');
                }
                // eslint-disable-next-line @typescript-eslint/no-unused-vars
            } catch (_error) {
                // Error handled globally via interceptor
            }
        }
    };

    const toggleMode = () => {
        setIsLogin(!isLogin);
        setError(null);
        setSuccess(null);
    };

    if (isLoading) {
        return <LinearProgress/>;
    }

    return (
        <Box
            sx={{
                minHeight: '100vh',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                py: 4,
                background: (theme) => theme.palette.mode === 'light'
                    ? 'linear-gradient(135deg, #E3F2FD 0%, #FCE4EC 100%)'
                    : 'linear-gradient(135deg, #121212 0%, #2D2D2D 100%)'
            }}
        >
            <Container maxWidth="xs">
                <Card sx={{p: 2}}>
                    <CardContent sx={{textAlign: 'center'}}>
                        <PiggyBank size={64} strokeWidth={1.5}/>
                        <Typography variant="h4" gutterBottom sx={{color: 'text.primary', fontWeight: 'bold'}}>
                            {isLogin ? t('login.title') : t('login.registerTitle')}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{mb: 4}}>
                            {isLogin ? t('login.welcome') : t('login.registerWelcome')}
                        </Typography>

                        <form onSubmit={handleSubmit}>
                            {error && <Alert severity="error" sx={{mb: 2}}>{error}</Alert>}
                            {success && <Alert severity="success" sx={{mb: 2}}>{success}</Alert>}

                            {!isLogin && (
                                <TextField
                                    fullWidth
                                    label={t('login.name')}
                                    variant="outlined"
                                    margin="dense"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    autoComplete="name"
                                    required
                                    slotProps={{
                                        input: {
                                            startAdornment: (
                                                <InputAdornment position="start">
                                                    <User size={20}/>
                                                </InputAdornment>
                                            ),
                                        }
                                    }}
                                />
                            )}
                            <TextField
                                fullWidth
                                label={t('login.email')}
                                variant="outlined"
                                type="email"
                                margin="dense"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                autoComplete="email"
                                required
                                slotProps={{
                                    htmlInput: {
                                        autoCapitalize: 'none',
                                        autoCorrect: 'off',
                                        spellCheck: 'false'
                                    },

                                    input: {
                                        startAdornment: (
                                            <InputAdornment position="start">
                                                <Mail size={20}/>
                                            </InputAdornment>
                                        ),
                                    }
                                }}/>
                            <TextField
                                fullWidth
                                label={t('login.password')}
                                type={showPassword ? 'text' : 'password'}
                                variant="outlined"
                                margin="dense"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                autoComplete={isLogin ? "current-password" : "new-password"}
                                required
                                slotProps={{
                                    input: {
                                        startAdornment: (
                                            <InputAdornment position="start">
                                                <Lock size={20}/>
                                            </InputAdornment>
                                        ),
                                        endAdornment: (
                                            <InputAdornment position="end">
                                                <IconButton onClick={() => setShowPassword(!showPassword)} edge="end">
                                                    {showPassword ? <EyeOff size={20}/> : <Eye size={20}/>}
                                                </IconButton>
                                            </InputAdornment>
                                        ),
                                    }
                                }}
                            />

                            {!isLogin && (
                                <TextField
                                    fullWidth
                                    label={t('login.repeatPassword')}
                                    type="password"
                                    variant="outlined"
                                    margin="dense"
                                    value={repeatPassword}
                                    onChange={(e) => setRepeatPassword(e.target.value)}
                                    autoComplete="new-password"
                                    required
                                    sx={{mt: 1}}
                                    slotProps={{
                                        input: {
                                            startAdornment: (
                                                <InputAdornment position="start">
                                                    <Lock size={20}/>
                                                </InputAdornment>
                                            ),
                                        }
                                    }}
                                />
                            )}

                            {isLogin && (
                                <Box sx={{textAlign: 'left', mt: 1}}>
                                    <FormControlLabel
                                        control={
                                            <Checkbox
                                                checked={rememberMe}
                                                onChange={(e) => setRememberMe(e.target.checked)}
                                                color="primary"
                                            />
                                        }
                                        label={<Typography variant="body2">{t('login.rememberMe')}</Typography>}
                                    />
                                </Box>
                            )}

                            <Button
                                fullWidth
                                variant="contained"
                                size="large"
                                type="submit"
                                disabled={loginMutation.isPending || registerMutation.isPending}
                                sx={{mt: 3, py: 1.5, fontSize: '1.1rem'}}
                            >
                                {isLogin
                                    ? (loginMutation.isPending ? t('login.submitting') : t('login.submit'))
                                    : (registerMutation.isPending ? t('login.registerSubmitting') : t('login.registerSubmit'))
                                }
                            </Button>

                            <Button
                                fullWidth
                                variant="text"
                                onClick={toggleMode}
                                sx={{mt: 2}}
                            >
                                {isLogin ? t('login.noAccount') : t('login.hasAccount')}
                            </Button>
                        </form>
                    </CardContent>
                </Card>
            </Container>
        </Box>
    );
};

export default LoginPage;
