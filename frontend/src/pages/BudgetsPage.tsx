import React, {useState} from 'react';
import {useQueryClient} from '@tanstack/react-query';
import {
    Alert,
    Box,
    Button,
    CircularProgress,
    Container,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    Divider,
    FormControl,
    FormHelperText,
    Grid,
    IconButton,
    InputLabel,
    MenuItem,
    Paper,
    Select,
    TextField,
    Tooltip,
    Typography
} from '@mui/material';
import {Edit2, Globe, Info, Plus, Trash2, User} from 'lucide-react';
import {useTranslation} from 'react-i18next';
import type {Budget, BudgetCreate, BudgetUpdate} from '../api/piggy';
import {
    type CategoryRead,
    type CategoryWithBudgets,
    getReadBudgetsApiV1CategoriesBudgetsGetQueryKey,
    getReadCategoriesApiV1CategoriesGetQueryKey,
    useCreateBudgetApiV1CategoriesBudgetsPost,
    useCreateCategoryApiV1CategoriesPost,
    useDeleteBudgetApiV1CategoriesBudgetsBudgetIdDelete,
    useGetDashboardSummaryApiV1DashboardSummaryGet,
    useReadBudgetsApiV1CategoriesBudgetsGet,
    useReadCategoriesApiV1CategoriesGet,
    useUpdateBudgetApiV1CategoriesBudgetsBudgetIdPut
} from '../api/piggy';
import {useAuth} from '../context/AuthContext';
import {formatCurrency} from '../utils/format';

const BudgetsPage: React.FC = () => {
    const {t} = useTranslation();
    const {user} = useAuth();
    const queryClient = useQueryClient();

    // API Hooks
    const {
        data: categories,
        isLoading: categoriesLoading
    } = useReadCategoriesApiV1CategoriesGet();
    const {
        data: budgets,
        isLoading: budgetsLoading
    } = useReadBudgetsApiV1CategoriesBudgetsGet();
    const {data: dashboardData, isLoading: dashboardLoading} = useGetDashboardSummaryApiV1DashboardSummaryGet({
        month: new Date().getMonth() + 1,
        year: new Date().getFullYear(),
        all_users: true
    });

    const invalidateBudgets = () => {
        queryClient.invalidateQueries({
            queryKey: getReadBudgetsApiV1CategoriesBudgetsGetQueryKey()
        });
        // Dashboard summary contains budget status
        queryClient.invalidateQueries({
            queryKey: ['/api/v1/dashboard/summary']
        });
    };

    const invalidateCategories = () => {
        queryClient.invalidateQueries({
            queryKey: getReadCategoriesApiV1CategoriesGetQueryKey()
        });
    };

    const createCategoryMutation = useCreateCategoryApiV1CategoriesPost({
        mutation: {
            onSuccess: invalidateCategories
        }
    });
    const createBudgetMutation = useCreateBudgetApiV1CategoriesBudgetsPost({
        mutation: {
            onSuccess: invalidateBudgets
        }
    });
    const updateBudgetMutation = useUpdateBudgetApiV1CategoriesBudgetsBudgetIdPut({
        mutation: {
            onSuccess: invalidateBudgets
        }
    });
    const deleteBudgetMutation = useDeleteBudgetApiV1CategoriesBudgetsBudgetIdDelete({
        mutation: {
            onSuccess: invalidateBudgets
        }
    });

    const getSpentAmount = (categoryId: string, budgetOwnerId?: string | null) => {
        if (!dashboardData?.budgets) return 0;
        const bStatus = dashboardData.budgets.find(b =>
            b.category_id === categoryId &&
            b.user_id === (budgetOwnerId || null)
        );
        return bStatus ? Number(bStatus.spent_amount) : 0;
    };

    // State for Dialogs
    const [categoryDialogOpen, setCategoryDialogOpen] = useState(false);
    const [budgetDialogOpen, setBudgetDialogOpen] = useState(false);
    const [editingBudget, setEditingBudget] = useState<Budget | null>(null);
    const [selectedCategoryId, setSelectedCategoryId] = useState<string>('');

    // Form State
    const [categoryName, setCategoryName] = useState('');
    const [budgetAmount, setBudgetAmount] = useState('');
    const [budgetType, setBudgetType] = useState<'global' | 'personal'>('global');
    const [error, setError] = useState<string | null>(null);

    const handleOpenCategoryDialog = () => {
        setCategoryName('');
        setCategoryDialogOpen(true);
        setError(null);
    };

    const handleOpenBudgetDialog = (categoryId: string, budget?: Budget) => {
        setSelectedCategoryId(categoryId);
        if (budget) {
            setEditingBudget(budget);
            setBudgetAmount(budget.amount.toString());
            setBudgetType(budget.user_id ? 'personal' : 'global');
        } else {
            setEditingBudget(null);
            setBudgetAmount('');

            // Default check: if category already has a personal budget by someone else, 
            // only personal is allowed. Otherwise, global is the preferred default.
            const categoryBudgets = budgets?.filter(b => b.category_id === categoryId) || [];
            const hasAnyPersonal = categoryBudgets.some(b => b.user_id !== null);

            setBudgetType(hasAnyPersonal ? 'personal' : 'global');
        }
        setBudgetDialogOpen(true);
        setError(null);
    };

    const handleSaveCategory = async () => {
        try {
            await createCategoryMutation.mutateAsync({
                data: {name: categoryName}
            });
            setCategoryDialogOpen(false);
            // eslint-disable-next-line @typescript-eslint/no-unused-vars
        } catch (_error) {
            // Error handled globally via interceptor
        }
    };

    const handleSaveBudget = async () => {
        try {
            const amount = parseFloat(budgetAmount);
            if (isNaN(amount)) {
                setError(t('dashboard.transactions.dialog.amount') + ' invalid');
                return;
            }

            if (editingBudget) {
                const updateData: BudgetUpdate = {
                    amount: amount
                };
                await updateBudgetMutation.mutateAsync({
                    budgetId: editingBudget.id,
                    data: updateData
                });
            } else {
                const createData: BudgetCreate = {
                    category_id: selectedCategoryId,
                    amount: amount,
                    user_id: budgetType === 'personal' ? user?.id : null
                };
                await createBudgetMutation.mutateAsync({
                    data: createData
                });
            }
            setBudgetDialogOpen(false);
            // eslint-disable-next-line @typescript-eslint/no-unused-vars
        } catch (_error) {
            // Error handled globally via interceptor
        }
    };

    const handleDeleteBudget = async (budgetId: string) => {
        if (window.confirm(t('budget.deleteBudgetConfirm'))) {
            try {
                await deleteBudgetMutation.mutateAsync({budgetId});
                // eslint-disable-next-line @typescript-eslint/no-unused-vars
            } catch (_error) {
                // Error handled globally via interceptor
            }
        }
    };

    const groupedCategories = React.useMemo(() => {
        if (!categories || !budgets) return {withBudget: [], withoutBudget: []};

        const withBudget: CategoryWithBudgets[] = [];
        const withoutBudget: CategoryRead[] = [];

        [...categories]
            .sort((a, b) => a.name.localeCompare(b.name))
            .forEach(category => {
                const categoryBudgets = budgets.filter(b => b.category_id === category.id);
                const hasActiveBudget = categoryBudgets.some(b => b.user_id === null || b.user_id === user?.id);

                if (hasActiveBudget) {
                    withBudget.push({
                        ...category,
                        budgets: categoryBudgets
                    });
                } else {
                    withoutBudget.push(category);
                }
            });

        return {withBudget, withoutBudget};
    }, [categories, budgets, user]);

    if (categoriesLoading || budgetsLoading || dashboardLoading) {
        return (
            <Box sx={{display: 'flex', justifyContent: 'center', py: 8}}>
                <CircularProgress/>
            </Box>
        );
    }

    return (
        <Container maxWidth="lg" sx={{py: 4}}>
            <Box sx={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4}}>
                <Typography variant="h4" sx={{fontWeight: 'bold', color: 'text.primary'}}>
                    {t('budget.title')}
                </Typography>
                <Button
                    variant="contained"
                    startIcon={<Plus size={18}/>}
                    onClick={() => handleOpenCategoryDialog()}
                >
                    {t('budget.newCategory')}
                </Button>
            </Box>
            <Grid container spacing={3}>
                {groupedCategories.withBudget.map((category) => {
                    const categoryBudgets = category.budgets;
                    const globalBudget = categoryBudgets.find(b => b.user_id === null);
                    const myBudget = categoryBudgets.find(b => b.user_id === user?.id);
                    const otherPersonalBudgets = categoryBudgets.filter(b => b.user_id !== null && b.user_id !== user?.id);

                    const activeBudget = globalBudget || myBudget;
                    const budgetAmount = activeBudget ? parseFloat(activeBudget.amount) : 0;
                    const spentAmount = getSpentAmount(category.id, activeBudget?.user_id);

                    const isOverspent = budgetAmount > 0 && spentAmount > budgetAmount;
                    const bluePercent = isOverspent
                        ? (budgetAmount / spentAmount) * 100
                        : (budgetAmount > 0 ? (spentAmount / budgetAmount) * 100 : 0);
                    const redPercent = isOverspent ? 100 - bluePercent : 0;

                    return (
                        <Grid key={category.id} size={{xs: 12}}>
                            <Paper sx={{p: 2}}>
                                <Box sx={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    width: '100%',
                                    gap: {xs: 1, sm: 2},
                                }}>
                                    <Box sx={{
                                        display: 'flex',
                                        flexDirection: {xs: 'row', sm: 'row'},
                                        flexWrap: {xs: 'wrap', sm: 'nowrap'},
                                        alignItems: {xs: 'flex-start', sm: 'center'},
                                        justifyContent: 'space-between',
                                        flexGrow: 1,
                                        minWidth: 0,
                                        gap: {xs: 1, sm: 2}
                                    }}>
                                        <Box sx={{minWidth: 0, flex: 1}}>
                                            <Box sx={{display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap'}}>
                                                <Typography variant="h6" sx={{
                                                    fontWeight: 'bold',
                                                    whiteSpace: 'nowrap',
                                                    overflow: 'hidden',
                                                    textOverflow: 'ellipsis',
                                                    maxWidth: {xs: '100%', sm: 'auto'}
                                                }}>
                                                    {category.name}
                                                </Typography>
                                                <Box sx={{display: 'flex', gap: 1, alignItems: 'center'}}>
                                                    {globalBudget && (
                                                        <Tooltip title={t('budget.global')}>
                                                            <Globe size={16} color="var(--mui-palette-info-main)"/>
                                                        </Tooltip>
                                                    )}
                                                    {myBudget && (
                                                        <Tooltip title={t('budget.personal')}>
                                                            <User size={16} color="var(--mui-palette-primary-main)"/>
                                                        </Tooltip>
                                                    )}
                                                    {otherPersonalBudgets.length > 0 && !globalBudget && (
                                                        <Tooltip
                                                            title={`${otherPersonalBudgets.length} ${t('budget.personal').toLowerCase()} of other users`}>
                                                            <Info size={16} color="gray"/>
                                                        </Tooltip>
                                                    )}
                                                </Box>
                                            </Box>
                                            {activeBudget && (
                                                <Box sx={{mt: 1, width: '100%', maxWidth: {sm: '400px', md: '500px'}}}>
                                                    <Box sx={{
                                                        height: 8,
                                                        width: '100%',
                                                        bgcolor: (theme) => theme.palette.mode === 'light' ? '#C2F0C2' : '#A3C4A3',
                                                        borderRadius: 4,
                                                        position: 'relative',
                                                        overflow: 'hidden',
                                                        mb: 0.5
                                                    }}>
                                                        <Box sx={{
                                                            position: 'absolute',
                                                            left: 0,
                                                            top: 0,
                                                            height: '100%',
                                                            width: `${bluePercent}%`,
                                                            bgcolor: 'primary.main',
                                                            borderRadius: isOverspent ? 0 : 4,
                                                            transition: 'width 0.5s ease-out',
                                                            zIndex: 1
                                                        }}/>
                                                        {isOverspent && (
                                                            <Box sx={{
                                                                position: 'absolute',
                                                                left: `${bluePercent}%`,
                                                                top: 0,
                                                                height: '100%',
                                                                width: `${redPercent}%`,
                                                                bgcolor: (theme) => theme.palette.mode === 'light' ? '#FFABAB' : '#D49B9B',
                                                                zIndex: 1
                                                            }}/>
                                                        )}
                                                    </Box>
                                                    <Typography variant="caption" color="text.secondary">
                                                        {formatCurrency(spentAmount)} {t('budgets.used').toLowerCase()}
                                                    </Typography>
                                                </Box>
                                            )}
                                        </Box>

                                        <Box sx={{
                                            textAlign: {xs: 'left', sm: 'right'},
                                            display: 'flex',
                                            alignItems: 'center',
                                            flexShrink: 0,
                                            width: {xs: '100%', sm: 'auto'},
                                        }}>
                                            {activeBudget && (
                                                <Typography variant="h6"
                                                            sx={{fontWeight: 'bold', whiteSpace: 'nowrap'}}>
                                                    {formatCurrency(budgetAmount)}
                                                </Typography>
                                            )}
                                        </Box>
                                    </Box>

                                    <Box sx={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        flexShrink: 0,
                                        gap: 0.5
                                    }}>
                                        {activeBudget ? (
                                            <>
                                                <IconButton size="small"
                                                            onClick={() => handleOpenBudgetDialog(category.id, activeBudget)}>
                                                    <Edit2 size={18}/>
                                                </IconButton>
                                                <IconButton size="small" color="error"
                                                            onClick={() => handleDeleteBudget(activeBudget.id)}>
                                                    <Trash2 size={18}/>
                                                </IconButton>
                                            </>
                                        ) : (
                                            <IconButton size="small" color="primary"
                                                        onClick={() => handleOpenBudgetDialog(category.id)}>
                                                <Plus size={18}/>
                                            </IconButton>
                                        )}
                                    </Box>
                                </Box>
                            </Paper>
                        </Grid>
                    );
                })}

                {groupedCategories.withoutBudget.length > 0 && (
                    <Grid size={{xs: 12}} sx={{mt: 2, mb: 1}}>
                        <Divider/>
                    </Grid>
                )}

                {groupedCategories.withoutBudget.map((category) => {
                    const categoryBudgets = budgets?.filter(b => b.category_id === category.id) || [];
                    const otherPersonalBudgets = categoryBudgets.filter(b => b.user_id !== null && b.user_id !== user?.id);

                    return (
                        <Grid key={category.id} size={{xs: 12}}>
                            <Paper sx={{p: 2, opacity: 0.8}}>
                                <Box sx={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    width: '100%',
                                    gap: {xs: 1, sm: 2},
                                }}>
                                    <Box sx={{
                                        display: 'flex',
                                        flexDirection: {xs: 'row', sm: 'row'},
                                        flexWrap: {xs: 'wrap', sm: 'nowrap'},
                                        alignItems: {xs: 'flex-start', sm: 'center'},
                                        justifyContent: 'space-between',
                                        flexGrow: 1,
                                        minWidth: 0,
                                        gap: {xs: 1, sm: 2}
                                    }}>
                                        <Box sx={{minWidth: 0, flex: 1}}>
                                            <Box sx={{display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap'}}>
                                                <Typography variant="h6" sx={{
                                                    fontWeight: 'bold',
                                                    whiteSpace: 'nowrap',
                                                    overflow: 'hidden',
                                                    textOverflow: 'ellipsis',
                                                    maxWidth: {xs: '100%', sm: 'auto'}
                                                }}>
                                                    {category.name}
                                                </Typography>
                                                {otherPersonalBudgets.length > 0 && (
                                                    <Tooltip
                                                        title={`${otherPersonalBudgets.length} ${t('budget.personal').toLowerCase()} of other users`}>
                                                        <Info size={16} color="gray"/>
                                                    </Tooltip>
                                                )}
                                            </Box>
                                            <Typography variant="body2" color="text.secondary"
                                                        sx={{fontStyle: 'italic'}}>
                                                {t('budget.noBudget')}
                                            </Typography>
                                        </Box>
                                    </Box>

                                    <Box sx={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        flexShrink: 0,
                                        gap: 0.5
                                    }}>
                                        <IconButton size="small" color="primary"
                                                    onClick={() => handleOpenBudgetDialog(category.id)}>
                                            <Plus size={18}/>
                                        </IconButton>
                                    </Box>
                                </Box>
                            </Paper>
                        </Grid>
                    );
                })}
            </Grid>
            {/* Category Dialog */}
            <Dialog open={categoryDialogOpen} onClose={() => setCategoryDialogOpen(false)} maxWidth="xs" fullWidth>
                <DialogTitle>{t('budget.newCategory')}</DialogTitle>
                <DialogContent>
                    <Box sx={{mt: 1, display: 'flex', flexDirection: 'column', gap: 2}}>
                        {error && <Alert severity="error">{error}</Alert>}
                        <TextField
                            fullWidth
                            label={t('budget.categoryName')}
                            value={categoryName}
                            onChange={(e) => setCategoryName(e.target.value)}
                            required
                        />
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setCategoryDialogOpen(false)}>{t('common.cancel')}</Button>
                    <Button onClick={handleSaveCategory} variant="contained" disabled={!categoryName}>
                        {t('common.save')}
                    </Button>
                </DialogActions>
            </Dialog>
            {/* Budget Dialog */}
            <Dialog open={budgetDialogOpen} onClose={() => setBudgetDialogOpen(false)} maxWidth="xs" fullWidth>
                <DialogTitle>{editingBudget ? t('budget.editBudget') : t('budget.setBudget')}</DialogTitle>
                <DialogContent>
                    <Box sx={{mt: 1, display: 'flex', flexDirection: 'column', gap: 2}}>
                        {error && <Alert severity="error">{error}</Alert>}

                        <FormControl fullWidth>
                            <InputLabel>{t('budget.type')}</InputLabel>
                            <Select
                                value={budgetType}
                                label={t('budget.type')}
                                onChange={(e) => setBudgetType(e.target.value as 'global' | 'personal')}
                                disabled={!!editingBudget} // Don't change type after creation
                            >
                                <MenuItem value="personal">
                                    <Box sx={{display: 'flex', alignItems: 'center', gap: 1}}>
                                        <User size={18}/> {t('budget.personal')}
                                    </Box>
                                </MenuItem>
                                <MenuItem
                                    value="global"
                                    disabled={budgets?.some(b => b.category_id === selectedCategoryId && b.user_id !== null)}
                                >
                                    <Box sx={{display: 'flex', alignItems: 'center', gap: 1}}>
                                        <Globe size={18}/> {t('budget.global')}
                                    </Box>
                                </MenuItem>
                            </Select>
                            <FormHelperText>
                                {budgetType === 'global' ? t('budget.globalHint') : t('budget.personalHint')}
                                {budgetType === 'global' && budgets?.some(b => b.category_id === selectedCategoryId && b.user_id !== null) &&
                                    " (Not possible because personal budgets already exist)"}
                            </FormHelperText>
                        </FormControl>

                        <TextField
                            fullWidth
                            label={t('budget.amount')}
                            type="number"
                            value={budgetAmount}
                            onChange={(e) => setBudgetAmount(e.target.value)}
                            required
                            slotProps={{
                                input: {
                                    startAdornment: <Typography sx={{mr: 1}}>€</Typography>,
                                }
                            }}
                        />
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setBudgetDialogOpen(false)}>{t('common.cancel')}</Button>
                    <Button onClick={handleSaveBudget} variant="contained" disabled={!budgetAmount}>
                        {t('common.save')}
                    </Button>
                </DialogActions>
            </Dialog>
        </Container>
    );
};

export default BudgetsPage;
