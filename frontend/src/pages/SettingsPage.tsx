import React, {useState} from 'react';
import {
    Alert,
    Box,
    Button,
    Card,
    CardContent,
    CircularProgress,
    Container,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    Divider,
    FormControl,
    Grid,
    IconButton,
    InputLabel,
    List,
    ListItem,
    ListItemSecondaryAction,
    ListItemText,
    MenuItem,
    Paper,
    Select,
    Snackbar,
    TextField,
    Typography
} from '@mui/material';
import {
    Banknote,
    Languages,
    LayoutDashboard,
    Moon,
    Plus,
    Save,
    Shield,
    Trash2,
    User as UserIcon
} from 'lucide-react';
import {useAuth} from '../context/AuthContext';
import {useTranslation} from 'react-i18next';
import type {BankConnectionCreate, UserUpdate} from '../api/piggy';
import {
    BankProvider,
    useCreateBankConnectionApiV1BankPost,
    useDeleteBankConnectionApiV1BankConnectionIdDelete,
    useListBankConnectionsApiV1BankGet,
    useReadUsersApiV1UsersGet,
    UserRole,
    useUpdateUserAdminApiV1UsersUserIdPut,
    useUpdateUserMeApiV1UsersMePut
} from '../api/piggy';

const SettingsPage: React.FC = () => {
    const {user, changeLanguage, changeTheme, themePreference, changeDashboardMode, dashboardMode} = useAuth();
    const {t, i18n} = useTranslation();

    const [name, setName] = useState(user?.name || '');
    const [email, setEmail] = useState(user?.email || '');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [bankDialogOpen, setBankDialogOpen] = useState(false);
    const [bankLogin, setBankLogin] = useState('');
    const [bankProvider, setBankProvider] = useState<BankProvider>(BankProvider.DKB);

    const [snackbar, setSnackbar] = useState<{ open: boolean, message: string, severity: 'success' | 'error' }>({
        open: false,
        message: '',
        severity: 'success'
    });

    const updateMeMutation = useUpdateUserMeApiV1UsersMePut();
    const updateAdminMutation = useUpdateUserAdminApiV1UsersUserIdPut();
    const {data: allUsers, refetch: refetchUsers} = useReadUsersApiV1UsersGet({
        query: {
            enabled: user?.role === UserRole.admin
        }
    });

    const deleteBankConnectionMutation = useDeleteBankConnectionApiV1BankConnectionIdDelete();
    const createBankConnectionMutation = useCreateBankConnectionApiV1BankPost();
    const {data: bankConnections, refetch: refetchBankConnections, isLoading: isLoadingBanks} = useListBankConnectionsApiV1BankGet();

    const handleSaveProfile = async () => {
        try {
            const data: UserUpdate = {
                name,
                email
            };
            await updateMeMutation.mutateAsync({
                data
            });
            setSnackbar({open: true, message: t('settings.success'), severity: 'success'});
            // eslint-disable-next-line @typescript-eslint/no-unused-vars
        } catch (_error) {
            // Error handled globally via interceptor
        }
    };

    const handleUpdatePassword = async () => {
        if (password !== confirmPassword) {
            setSnackbar({open: true, message: t('settings.error'), severity: 'error'});
            return;
        }
        try {
            const data: UserUpdate = {
                password
            };
            await updateMeMutation.mutateAsync({
                data
            });
            setPassword('');
            setConfirmPassword('');
            setSnackbar({open: true, message: t('settings.success'), severity: 'success'});
            // eslint-disable-next-line @typescript-eslint/no-unused-vars
        } catch (_error) {
            // Error handled globally via interceptor
        }
    };

    const handleDeleteUser = async (userId: string) => {
        if (window.confirm(t('settings.admin.deleteConfirm'))) {
            try {
                console.warn(`Admin attempt to delete user ${userId}. Endpoint missing in API.`);
                setSnackbar({open: true, message: "Admin delete endpoint not implemented in API", severity: 'error'});
                // eslint-disable-next-line @typescript-eslint/no-unused-vars
            } catch (_error) {
                // Error handled globally via interceptor
            }
        }
    };

    const handleActivateUser = async (userId: string) => {
        try {
            await updateAdminMutation.mutateAsync({
                userId,
                data: {
                    is_active: true
                }
            });
            await refetchUsers();
            setSnackbar({open: true, message: t('settings.success'), severity: 'success'});
            // eslint-disable-next-line @typescript-eslint/no-unused-vars
        } catch (_error) {
            // Error handled globally via interceptor
        }
    };

    const handleLanguageChange = (lng: string) => {
        changeLanguage(lng);
    };

    const handleAddBankConnection = async () => {
        try {
            const data: BankConnectionCreate = {
                login: bankLogin,
                provider: bankProvider
            };
            await createBankConnectionMutation.mutateAsync({
                data
            });
            setBankDialogOpen(false);
            setBankLogin('');
            await refetchBankConnections();
            setSnackbar({open: true, message: t('settings.success'), severity: 'success'});
            // eslint-disable-next-line @typescript-eslint/no-unused-vars
        } catch (_error) {
            // Error handled globally
        }
    };

    const handleDeleteBankConnection = async (id: string) => {
        if (window.confirm(t('settings.bank.deleteConfirm'))) {
            try {
                await deleteBankConnectionMutation.mutateAsync({
                    connectionId: id
                });
                await refetchBankConnections();
                setSnackbar({open: true, message: t('settings.success'), severity: 'success'});
                // eslint-disable-next-line @typescript-eslint/no-unused-vars
            } catch (_error) {
                // Error handled globally
            }
        }
    };

    return (
        <Container maxWidth="lg" sx={{py: 4}}>
            <Box sx={{display: 'flex', alignItems: 'center', mb: 4}}>
                <Typography variant="h4" sx={{fontWeight: 'bold', color: 'text.primary'}}>
                    {t('settings.title')}
                </Typography>
            </Box>

            <Grid container spacing={4}>
                {/* General Settings */}
                <Grid size={{xs: 12, md: 6}}>
                    <Card sx={{height: '100%'}}>
                        <CardContent>
                            <Box sx={{display: 'flex', alignItems: 'center', gap: 1, mb: 3}}>
                                <Languages size={20}/>
                                <Typography variant="h6">{t('settings.language')}</Typography>
                            </Box>
                            <FormControl fullWidth variant="outlined" sx={{mb: 3}}>
                                <InputLabel>{t('settings.language')}</InputLabel>
                                <Select
                                    value={i18n.language.split('-')[0]}
                                    onChange={(e) => handleLanguageChange(e.target.value as string)}
                                    label={t('settings.language')}
                                >
                                    <MenuItem value="de">Deutsch</MenuItem>
                                    <MenuItem value="en">English</MenuItem>
                                </Select>
                            </FormControl>

                            <Box sx={{display: 'flex', alignItems: 'center', gap: 1, mb: 3}}>
                                <Moon size={20}/>
                                <Typography variant="h6">{t('settings.theme.title')}</Typography>
                            </Box>
                            <FormControl fullWidth variant="outlined">
                                <InputLabel>{t('settings.theme.title')}</InputLabel>
                                <Select
                                    value={themePreference}
                                    onChange={(e) => changeTheme(e.target.value as 'light' | 'dark' | 'auto')}
                                    label={t('settings.theme.title')}
                                >
                                    <MenuItem value="auto">{t('settings.theme.auto')}</MenuItem>
                                    <MenuItem value="light">{t('settings.theme.light')}</MenuItem>
                                    <MenuItem value="dark">{t('settings.theme.dark')}</MenuItem>
                                </Select>
                            </FormControl>

                            <Box sx={{display: 'flex', alignItems: 'center', gap: 1, mb: 3, mt: 3}}>
                                <LayoutDashboard size={20}/>
                                <Typography variant="h6">{t('settings.dashboardMode.title')}</Typography>
                            </Box>
                            <FormControl fullWidth variant="outlined">
                                <InputLabel>{t('settings.dashboardMode.title')}</InputLabel>
                                <Select
                                    value={dashboardMode}
                                    onChange={(e) => changeDashboardMode(e.target.value as 'current' | 'prognosis')}
                                    label={t('settings.dashboardMode.title')}
                                >
                                    <MenuItem value="current">{t('settings.dashboardMode.current')}</MenuItem>
                                    <MenuItem value="prognosis">{t('settings.dashboardMode.prognosis')}</MenuItem>
                                </Select>
                            </FormControl>
                        </CardContent>
                    </Card>
                </Grid>

                {/* Profile Settings */}
                <Grid size={{xs: 12, md: 6}}>
                    <Card sx={{height: '100%'}}>
                        <CardContent>
                            <Box sx={{display: 'flex', alignItems: 'center', gap: 1, mb: 3}}>
                                <UserIcon size={20}/>
                                <Typography variant="h6">{t('settings.profile')}</Typography>
                            </Box>
                            <TextField
                                fullWidth
                                label={t('settings.name')}
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                margin="normal"
                            />
                            <TextField
                                fullWidth
                                label={t('settings.email')}
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                margin="normal"
                            />
                            <Button
                                variant="contained"
                                startIcon={<Save size={18}/>}
                                onClick={handleSaveProfile}
                                sx={{mt: 2}}
                                disabled={updateMeMutation.isPending}
                            >
                                {t('settings.save')}
                            </Button>
                        </CardContent>
                    </Card>
                </Grid>

                {/* Password Settings */}
                <Grid size={{xs: 12, md: 6}}>
                    <Card sx={{height: '100%'}}>
                        <CardContent>
                            <Box sx={{display: 'flex', alignItems: 'center', gap: 1, mb: 3}}>
                                <Shield size={20}/>
                                <Typography variant="h6">{t('settings.password.title')}</Typography>
                            </Box>
                            <TextField
                                fullWidth
                                type="password"
                                label={t('settings.password.newPassword')}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                margin="normal"
                            />
                            <TextField
                                fullWidth
                                type="password"
                                label={t('settings.password.confirmPassword')}
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                margin="normal"
                            />
                            <Button
                                variant="outlined"
                                onClick={handleUpdatePassword}
                                sx={{mt: 2}}
                                disabled={updateMeMutation.isPending || !password}
                            >
                                {t('settings.password.update')}
                            </Button>
                        </CardContent>
                    </Card>
                </Grid>

                {/* Bank Settings */}
                <Grid size={12}>
                    <Card>
                        <CardContent>
                            <Box sx={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3}}>
                                <Box sx={{display: 'flex', alignItems: 'center', gap: 1}}>
                                    <Banknote size={20}/>
                                    <Typography variant="h6">{t('settings.bank.title')}</Typography>
                                </Box>
                                <Button
                                    variant="contained"
                                    startIcon={<Plus size={18}/>}
                                    onClick={() => setBankDialogOpen(true)}
                                >
                                    {t('settings.bank.add')}
                                </Button>
                            </Box>

                            {isLoadingBanks ? (
                                <Box sx={{display: 'flex', justifyContent: 'center', py: 4}}>
                                    <CircularProgress/>
                                </Box>
                            ) : bankConnections && bankConnections.length > 0 ? (
                                <List>
                                    {bankConnections.map((conn, index) => (
                                        <React.Fragment key={conn.id}>
                                            <ListItem sx={{px: 0}}>
                                                <ListItemText
                                                    primary={conn.bank_name || conn.login}
                                                    secondary={`${conn.login} • ${conn.bank_code} • Status: ${conn.status}`}
                                                />
                                                <ListItemSecondaryAction>
                                                    <IconButton
                                                        edge="end"
                                                        aria-label="delete"
                                                        onClick={() => handleDeleteBankConnection(conn.id)}
                                                        color="error"
                                                    >
                                                        <Trash2 size={20}/>
                                                    </IconButton>
                                                </ListItemSecondaryAction>
                                            </ListItem>
                                            {index < bankConnections.length - 1 && <Divider component="li"/>}
                                        </React.Fragment>
                                    ))}
                                </List>
                            ) : (
                                <Typography variant="body2" color="text.secondary" align="center" sx={{py: 4}}>
                                    {t('settings.bank.empty')}
                                </Typography>
                            )}
                        </CardContent>
                    </Card>
                </Grid>

                {/* Admin Section */}
                {user?.role === UserRole.admin && (
                    <Grid size={12}>
                        <Paper sx={{p: 3}}>
                            <Box sx={{display: 'flex', alignItems: 'center', gap: 1, mb: 3}}>
                                <Shield size={20} color="#D49B9B"/>
                                <Typography variant="h6">{t('settings.admin.title')}</Typography>
                            </Box>
                            <Typography variant="subtitle1" gutterBottom>
                                {t('settings.admin.userList')}
                            </Typography>
                            <List>
                                {allUsers?.map((u, index) => (
                                    <React.Fragment key={u.id}>
                                        <ListItem sx={{px: 0}}>
                                            <ListItemText
                                                primary={u.name}
                                                secondary={`${u.email} • ${u.role.toUpperCase()}`}
                                            />
                                            <ListItemSecondaryAction
                                                sx={{display: 'flex', alignItems: 'center', gap: 2}}>
                                                <Typography variant="caption"
                                                            color={u.is_active ? 'success.main' : 'error.main'}>
                                                    {u.is_active ? t('settings.admin.active') : t('settings.admin.inactive')}
                                                </Typography>
                                                {u.id !== user?.id && (
                                                    <Box sx={{display: 'flex', gap: 1}}>
                                                        {!u.is_active && (
                                                            <Button
                                                                size="small"
                                                                variant="outlined"
                                                                color="success"
                                                                onClick={() => handleActivateUser(u.id)}
                                                                disabled={updateAdminMutation.isPending}
                                                            >
                                                                {t('settings.admin.activate')}
                                                            </Button>
                                                        )}
                                                        <Button
                                                            size="small"
                                                            variant="outlined"
                                                            color="error"
                                                            onClick={() => handleDeleteUser(u.id)}
                                                        >
                                                            {t('settings.admin.delete')}
                                                        </Button>
                                                    </Box>
                                                )}
                                            </ListItemSecondaryAction>
                                        </ListItem>
                                        {index < allUsers.length - 1 && <Divider component="li"/>}
                                    </React.Fragment>
                                ))}
                            </List>
                        </Paper>
                    </Grid>
                )}
            </Grid>

            <Snackbar
                open={snackbar.open}
                autoHideDuration={6000}
                onClose={() => setSnackbar({...snackbar, open: false})}
            >
                <Alert severity={snackbar.severity} sx={{width: '100%'}}>
                    {snackbar.message}
                </Alert>
            </Snackbar>

            <Dialog open={bankDialogOpen} onClose={() => setBankDialogOpen(false)} maxWidth="xs" fullWidth>
                <DialogTitle>{t('settings.bank.add')}</DialogTitle>
                <DialogContent>
                    <Box sx={{display: 'flex', flexDirection: 'column', gap: 2, mt: 1}}>
                        <FormControl fullWidth>
                            <InputLabel>{t('settings.bank.provider')}</InputLabel>
                            <Select
                                value={bankProvider}
                                label={t('settings.bank.provider')}
                                onChange={(e) => setBankProvider(e.target.value as BankProvider)}
                            >
                                {Object.values(BankProvider).map((p) => (
                                    <MenuItem key={p} value={p}>{p}</MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                        <TextField
                            fullWidth
                            label={t('settings.bank.username')}
                            value={bankLogin}
                            onChange={(e) => setBankLogin(e.target.value)}
                        />
                        <Typography variant="caption" color="text.secondary">
                            {t('settings.bank.pinHint')}
                        </Typography>
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setBankDialogOpen(false)}>{t('common.cancel')}</Button>
                    <Button
                        variant="contained"
                        onClick={handleAddBankConnection}
                        disabled={!bankLogin || createBankConnectionMutation.isPending}
                    >
                        {t('common.save')}
                    </Button>
                </DialogActions>
            </Dialog>
        </Container>
    );
};

export default SettingsPage;
