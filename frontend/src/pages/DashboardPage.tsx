import React from 'react';
import {useQueryClient} from '@tanstack/react-query';
import {
    Alert,
    Avatar,
    Box,
    Button,
    Card,
    CardContent,
    Checkbox,
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
    LinearProgress,
    List,
    ListItem,
    ListItemAvatar,
    ListItemText,
    MenuItem,
    Paper,
    Select,
    Switch,
    TextField,
    type Theme,
    Typography,
    useMediaQuery,
    useTheme
} from '@mui/material';
import {
    AlertCircle,
    ArrowDownRight,
    ArrowRight,
    ArrowUpRight,
    Banknote,
    Check,
    ChevronLeft,
    ChevronRight,
    Coins,
    PiggyBank,
    Plus,
    RefreshCw,
    Trash2,
    TrendingDown,
    TrendingUp,
    X
} from 'lucide-react';
import {useTranslation} from 'react-i18next';
import {useGreeting} from '../hooks/useGreeting';

import {formatCurrency, formatDate} from '../utils/format';
import {addMonths, format, isSameMonth, parseISO, startOfMonth, subMonths, subWeeks,} from 'date-fns';

import {useAuth} from '../context/AuthContext';

import type {
    BankConnection,
    BankTransactionPreview,
    Transaction,
    TransactionCreate,
    TransactionUpdate
} from '../api/piggy';
import {
    getGetDashboardSummaryApiV1DashboardSummaryGetQueryKey,
    getReadAccountsApiV1AccountsGetQueryKey,
    getReadAllUserTransactionsApiV1AccountsTransactionsGetQueryKey,
    SyncTaskStatus,
    TransactionType,
    useCreateCategoryApiV1CategoriesPost,
    useCreateTransactionApiV1AccountsAccountIdTransactionsPost,
    useCreateTransactionsBulkApiV1AccountsAccountIdTransactionsBulkPost,
    useDeleteTransactionApiV1AccountsTransactionsTransactionIdDelete,
    useGetDashboardSummaryApiV1DashboardSummaryGet,
    useGetSyncStatusApiV1BankSyncStatusTaskIdGet,
    useListBankConnectionsApiV1BankGet,
    useReadAccountsApiV1AccountsGet,
    useReadAllUserTransactionsApiV1AccountsTransactionsGet,
    useReadCategoriesApiV1CategoriesGet,
    useReadRecurringPaymentsApiV1RecurringPaymentsGet,
    useReadTransferTargetsApiV1AccountsTransferTargetsGet,
    useReadUserMeApiV1UsersMeGet,
    useReadUsersPublicApiV1UsersListGet,
    useSyncApiV1BankConnectionIdSyncPost,
    useUpdateTransactionApiV1AccountsTransactionsTransactionIdPut
} from '../api/piggy';

import TransactionForm from '../components/TransactionForm';

const DashboardPage: React.FC = () => {
    const {t} = useTranslation();
    const {dashboardMode, isLoading: authLoading} = useAuth();
    const greetingTemplate = useGreeting();
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

    const [showAllUsers, setShowAllUsers] = React.useState(false);
    const [selectedMonth, setSelectedMonth] = React.useState<Date>(startOfMonth(new Date()));
    const queryClient = useQueryClient();

    const {data: user, isLoading: userLoading} = useReadUserMeApiV1UsersMeGet();
    const {data: allUsers} = useReadUsersPublicApiV1UsersListGet();
    const {data: allAccounts, isLoading: accountsLoading} = useReadAccountsApiV1AccountsGet({
        all_users: true
    });

    const {data: transferTargets} = useReadTransferTargetsApiV1AccountsTransferTargetsGet();

    const {
        data: dashboardData,
        isLoading: dashboardLoading
    } = useGetDashboardSummaryApiV1DashboardSummaryGet({
        month: selectedMonth.getMonth() + 1,
        year: selectedMonth.getFullYear(),
        all_users: showAllUsers
    });

    const {
        data: transactions,
        isLoading: transactionsLoading
    } = useReadAllUserTransactionsApiV1AccountsTransactionsGet({
        all_users: showAllUsers,
        month: selectedMonth.getMonth() + 1,
        year: selectedMonth.getFullYear(),
        limit: 100
    });

    const sortedTransactions = React.useMemo(() => {
        if (!transactions) return [];
        return [...transactions]
            .sort((a, b) => {
                return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
            });
    }, [transactions]);

    const [visibleCount, setVisibleCount] = React.useState(10);
    const observerTarget = React.useRef(null);

    React.useEffect(() => {
        const observer = new IntersectionObserver(
            entries => {
                if (entries[0].isIntersecting && sortedTransactions.length > visibleCount) {
                    setVisibleCount(prev => prev + 10);
                }
            },
            {threshold: 1.0}
        );

        if (observerTarget.current) {
            observer.observe(observerTarget.current);
        }

        return () => {
            if (observerTarget.current) {
                // eslint-disable-next-line react-hooks/exhaustive-deps
                observer.unobserve(observerTarget.current);
            }
        };
    }, [sortedTransactions.length, visibleCount]);

    React.useEffect(() => {
        setVisibleCount(10);
    }, [showAllUsers, selectedMonth]);

    const {data: categories, refetch: refetchCategories} = useReadCategoriesApiV1CategoriesGet();
    const {data: recurringPayments} = useReadRecurringPaymentsApiV1RecurringPaymentsGet();

    const invalidateDashboard = () => {
        queryClient.invalidateQueries({
            queryKey: getGetDashboardSummaryApiV1DashboardSummaryGetQueryKey({
                month: selectedMonth.getMonth() + 1,
                year: selectedMonth.getFullYear(),
                all_users: showAllUsers
            })
        });
        queryClient.invalidateQueries({
            queryKey: getReadAllUserTransactionsApiV1AccountsTransactionsGetQueryKey({
                all_users: showAllUsers,
                month: selectedMonth.getMonth() + 1,
                year: selectedMonth.getFullYear(),
                limit: 100
            })
        });
        queryClient.invalidateQueries({
            queryKey: getReadAccountsApiV1AccountsGetQueryKey({all_users: true})
        });
    };

    const [open, setOpen] = React.useState(false);
    const [importOpen, setImportOpen] = React.useState(false);
    const [importStep, setImportStep] = React.useState(0); // 0: PIN/Date, 1: Loading, 2: Selection
    const [importPin, setImportPin] = React.useState('');
    const [importSince, setImportSince] = React.useState(format(subWeeks(new Date(), 1), 'dd.MM.yyyy'));
    const [importConnection, setImportConnection] = React.useState<string>('');
    const [bankPreviews, setBankPreviews] = React.useState<(BankTransactionPreview & { selected: boolean })[]>([]);
    const [currentImportIndex, setCurrentImportIndex] = React.useState(0);
    const [syncError, setSyncError] = React.useState(false);
    const [syncTaskId, setSyncTaskId] = React.useState<string | null>(null);

    const {data: syncStatusData, refetch: refetchSyncStatus} = useGetSyncStatusApiV1BankSyncStatusTaskIdGet(
        syncTaskId || '',
        {
            query: {
                enabled: !!syncTaskId,
                refetchInterval: (data) => {
                    const status = data?.status;
                    if (status === SyncTaskStatus.COMPLETED || status === SyncTaskStatus.FAILED) {
                        return false;
                    }
                    return 2000;
                }
            }
        }
    );

    const handleUpdatePreview = React.useCallback((index: number, update: Partial<BankTransactionPreview & {
        selected: boolean
    }>) => {
        setBankPreviews(prev => {
            const next = [...prev];
            next[index] = {...next[index], ...update};
            return next;
        });
    }, []);

    const {data: bankConnections} = useListBankConnectionsApiV1BankGet();
    const syncMutation = useSyncApiV1BankConnectionIdSyncPost();
    const bulkCreateMutation = useCreateTransactionsBulkApiV1AccountsAccountIdTransactionsBulkPost({
        mutation: {
            onSuccess: invalidateDashboard
        }
    });

    React.useEffect(() => {
        if (bankConnections && bankConnections.length > 0 && !importConnection) {
            setImportConnection(bankConnections[0].id);
        }
    }, [bankConnections, importConnection]);

    React.useEffect(() => {
        const handleVisibilityChange = () => {
            if (document.visibilityState === 'visible' && syncTaskId) {
                refetchSyncStatus();
            }
        };
        document.addEventListener('visibilitychange', handleVisibilityChange);
        return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
    }, [syncTaskId, refetchSyncStatus]);

    React.useEffect(() => {
        if (syncStatusData) {
            if (syncStatusData.status === SyncTaskStatus.COMPLETED && syncStatusData.result) {
                setBankPreviews(syncStatusData.result.map(r => ({...r, selected: !r.is_potential_duplicate})));
                setImportStep(2);
                setSyncTaskId(null);
            } else if (syncStatusData.status === SyncTaskStatus.FAILED) {
                setSyncError(true);
                setSyncTaskId(null);
            }
        }
    }, [syncStatusData]);

    const handleStartImport = async () => {
        if (!importConnection || !importPin || !importSince) return;
        setImportStep(1);
        setSyncError(false);
        setSyncTaskId(null);
        try {
            const response = await syncMutation.mutateAsync({
                connectionId: importConnection,
                data: {
                    pin: importPin,
                    since: importSince
                }
            });
            setSyncTaskId(response.task_id);
            // eslint-disable-next-line @typescript-eslint/no-unused-vars
        } catch (error) {
            setSyncError(true);
        }
    };

    const handleBulkAdd = async () => {
        const selected = bankPreviews.filter(p => p.selected);
        if (selected.length === 0) {
            setImportOpen(false);
            return;
        }

        // Group by account
        const byAccount: Record<string, BankTransactionPreview[]> = {};
        selected.forEach(p => {
            if (!byAccount[p.account_id]) byAccount[p.account_id] = [];
            byAccount[p.account_id].push(p);
        });

        try {
            const requests = Object.keys(byAccount).map(accountId =>
                bulkCreateMutation.mutateAsync({
                    accountId,
                    data: byAccount[accountId].map(p => {
                        const ts = p.timestamp ? (p.timestamp.length === 16 ? `${p.timestamp}:00` : p.timestamp) : undefined;
                        return {
                            description: p.description,
                            amount: parseFloat(p.amount.toString().replace(',', '.')),
                            type: p.type || TransactionType.Expense,
                            category_id: p.category_id || undefined,
                            target_account_id: p.type === TransactionType.Transfer ? (p.target_account_id || undefined) : undefined,
                            timestamp: ts
                        };
                    })
                })
            );
            await Promise.all(requests);

            setImportOpen(false);
            setImportStep(0);
            setImportPin('');
            setBankPreviews([]);
            // eslint-disable-next-line @typescript-eslint/no-unused-vars
        } catch (error) {
            // Error handled globally
        }
    };

    const [editingTransaction, setEditingTransaction] = React.useState<Transaction | null>(null);
    const [newTx, setNewTx] = React.useState<{
        description: string;
        amount: string;
        account_id: string;
        target_account_id: string;
        category_id: string;
        type: TransactionType;
        timestamp: string;
    }>({
        description: '',
        amount: '',
        account_id: '',
        target_account_id: '',
        category_id: '',
        type: TransactionType.Expense,
        timestamp: format(new Date(), "yyyy-MM-dd'T'HH:mm:ss")
    });

    const createTxMutation = useCreateTransactionApiV1AccountsAccountIdTransactionsPost({
        mutation: {
            onSuccess: invalidateDashboard
        }
    });
    const updateTxMutation = useUpdateTransactionApiV1AccountsTransactionsTransactionIdPut({
        mutation: {
            onSuccess: invalidateDashboard
        }
    });
    const deleteTxMutation = useDeleteTransactionApiV1AccountsTransactionsTransactionIdDelete({
        mutation: {
            onSuccess: invalidateDashboard
        }
    });
    const createCategoryMutation = useCreateCategoryApiV1CategoriesPost({
        mutation: {
            onSuccess: () => {
                queryClient.invalidateQueries({
                    queryKey: ['/api/v1/categories']
                });
            }
        }
    });

    const handleClose = () => {
        setOpen(false);
        setEditingTransaction(null);
    };

    const resetNewTx = React.useCallback(() => {
        const now = new Date();
        const ts = format(now, "yyyy-MM-dd'T'HH:mm:ss");
        setNewTx({
            description: '',
            amount: '',
            account_id: '',
            target_account_id: '',
            category_id: '',
            type: TransactionType.Expense,
            timestamp: ts
        });
    }, []);

    const handleOpen = (tx?: Transaction) => {
        if (tx) {
            setEditingTransaction(tx);
            const ts = format(parseISO(tx.timestamp), "yyyy-MM-dd'T'HH:mm:ss");
            setNewTx({
                description: tx.description,
                amount: tx.amount.toString(),
                account_id: tx.account_id,
                target_account_id: tx.target_account_id || '',
                category_id: tx.category_id || '',
                type: tx.type || TransactionType.Expense,
                timestamp: ts
            });
        } else {
            resetNewTx();
            setEditingTransaction(null);
        }
        setOpen(true);
    };

    React.useEffect(() => {
        if (!open) {
            resetNewTx();
        }
    }, [open, resetNewTx]);

    const handleCreateTransaction = async () => {
        if (!newTx.account_id || !newTx.amount || !newTx.description) return;

        try {
            let categoryId = newTx.category_id;

            if (newTx.type !== TransactionType.Transfer && newTx.category_id && newTx.category_id.startsWith('new:')) {
                const newCategoryName = newTx.category_id.replace('new:', '');
                try {
                    const createdCategory = await createCategoryMutation.mutateAsync({
                        data: {name: newCategoryName}
                    });
                    categoryId = createdCategory.id;
                    await refetchCategories();
                    // eslint-disable-next-line @typescript-eslint/no-unused-vars
                } catch (_error) {
                    return;
                }
            }

            const txData: TransactionCreate | TransactionUpdate = {
                description: newTx.description,
                amount: parseFloat(newTx.amount.replace(',', '.')),
                category_id: newTx.type === TransactionType.Transfer ? undefined : (categoryId || undefined),
                target_account_id: newTx.type === TransactionType.Transfer ? newTx.target_account_id : undefined,
                type: newTx.type,
                timestamp: format(parseISO(newTx.timestamp), "yyyy-MM-dd'T'HH:mm:ss")
            };

            if (editingTransaction) {
                await updateTxMutation.mutateAsync({
                    transactionId: editingTransaction.id,
                    data: txData as TransactionUpdate
                });
            } else {
                await createTxMutation.mutateAsync({
                    accountId: newTx.account_id,
                    data: txData as TransactionCreate
                });
            }

            handleClose();
            // eslint-disable-next-line @typescript-eslint/no-unused-vars
        } catch (_error) {
            // Error handled globally via interceptor
        }
    };

    const handleDeleteTransaction = async () => {
        if (!editingTransaction) return;

        if (window.confirm(t('dashboard.transactions.dialog.deleteConfirm'))) {
            try {
                await deleteTxMutation.mutateAsync({
                    transactionId: editingTransaction.id
                });
                handleClose();
                // eslint-disable-next-line @typescript-eslint/no-unused-vars
            } catch (_error) {
                // Error handled globally via interceptor
            }
        }
    };

    const isCurrentMonth = React.useMemo(() => {
        const now = new Date();
        return selectedMonth.getMonth() === now.getMonth() &&
            selectedMonth.getFullYear() === now.getFullYear();
    }, [selectedMonth]);

    const stats = React.useMemo(() => {
        if (!dashboardData) return [];
        const {summary} = dashboardData;

        const isPrognosisModeActive = dashboardMode === 'prognosis' && isCurrentMonth && !showAllUsers;
        const showPrognosisValue = isPrognosisModeActive && summary.prognosis_balance !== null && summary.prognosis_balance !== undefined;

        const displayMonthlyBalance = showPrognosisValue ? summary.prognosis_balance : summary.monthly_balance;

        return [
            {
                id: 'balance',
                title: t('dashboard.stats.balance'),
                value: formatCurrency(summary.total_balance),
                icon: <Banknote size={24}/>,
                color: 'info.main'
            },
            {
                id: 'income',
                title: t('dashboard.stats.income'),
                value: formatCurrency(summary.monthly_income),
                icon: <TrendingUp size={24}/>,
                color: 'success.main'
            },
            {
                id: 'expenses',
                title: t('dashboard.stats.expenses'),
                value: formatCurrency(summary.monthly_expenses),
                icon: <TrendingDown size={24}/>,
                color: 'error.main'
            },
            {
                id: 'monthlyBalance-' + (isPrognosisModeActive ? 'prognosis' : 'current'),
                title: isPrognosisModeActive
                    ? t('settings.dashboardMode.prognosis')
                    : t('dashboard.stats.monthlyBalance'),
                value: formatCurrency(displayMonthlyBalance!),
                icon: Number(displayMonthlyBalance) >= 0 ? <TrendingUp size={24}/> : <TrendingDown size={24}/>,
                color: Number(displayMonthlyBalance) >= 0 ? 'success.main' : 'error.main'
            },
        ];
    }, [isCurrentMonth, dashboardMode, dashboardData, showAllUsers, t]);

    if (authLoading || userLoading || accountsLoading || transactionsLoading || dashboardLoading || !recurringPayments) {
        return <LinearProgress/>;
    }

    console.debug('Loaded budgets:', dashboardData?.budgets);

    const formatTxDate = (dateStr: string) => formatDate(dateStr, t);

    return (
        <Container maxWidth="lg" sx={{py: 4}}>
            <Box sx={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4}}>
                <Box>
                    <Typography variant="h4" sx={{color: 'text.primary', fontWeight: 'bold'}}>
                        {greetingTemplate.replace('{{name}}', user?.name || t('dashboard.greetings.defaultName'))}
                    </Typography>
                </Box>
                <Box sx={{display: 'flex', alignItems: 'center', gap: 1}}>
                    <Typography variant="body2" color="text.secondary">
                        {t('dashboard.stats.showAll')}
                    </Typography>
                    <Switch
                        checked={showAllUsers}
                        onChange={(e) => setShowAllUsers(e.target.checked)}
                        size="small"
                    />
                </Box>
            </Box>
            <Grid container spacing={3} sx={{mb: 4}}>
                {stats.map((stat) => (
                    <Grid key={stat.id} size={{xs: 12, sm: 6, md: 3}} sx={{display: 'flex'}}>
                        <Card sx={{flexGrow: 1, display: 'flex', flexDirection: 'column'}}>
                            <CardContent sx={{display: 'flex', alignItems: 'center', gap: 2, flexGrow: 1}}>
                                <Box sx={{
                                    p: 1.5,
                                    borderRadius: 3,
                                    bgcolor: stat.color,
                                    display: 'flex',
                                    color: (theme) => {
                                        const colorParts = stat.color.split('.');
                                        const mainColor = colorParts.length > 1
                                            // eslint-disable-next-line @typescript-eslint/no-explicit-any
                                            ? (theme.palette as any)[colorParts[0]]?.main
                                            // eslint-disable-next-line @typescript-eslint/no-explicit-any
                                            : (theme.palette as any)[colorParts[0]] || theme.palette.primary.main;
                                        return theme.palette.getContrastText(mainColor || theme.palette.primary.main);
                                    }
                                }}>
                                    {stat.icon}
                                </Box>
                                <Box sx={{flexGrow: 1}}>
                                    <Box sx={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
                                        <Typography variant="body2" color="text.secondary">{stat.title}</Typography>
                                    </Box>
                                    <Typography variant="h6" sx={{fontWeight: 'bold', transition: 'all 0.3s'}}>
                                        {stat.value}
                                    </Typography>
                                </Box>
                            </CardContent>
                        </Card>
                    </Grid>
                ))}
            </Grid>
            <Grid container spacing={3}>
                {/* Recent Transactions */}
                <Grid size={{xs: 12, md: 8}}>
                    <Paper sx={{p: 3, height: '100%'}}>
                        <Box sx={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            mb: 2
                        }}>
                            <Typography variant="h6"
                                        sx={{fontWeight: 'bold'}}>{t('dashboard.transactions.title')}</Typography>
                            <Box sx={{display: 'flex', gap: 1}}>
                                <Button
                                    startIcon={<Plus size={18}/>}
                                    variant="text"
                                    onClick={() => handleOpen()}
                                >
                                    {t('dashboard.transactions.new')}
                                </Button>
                                <Button
                                    startIcon={<Coins size={18}/>}
                                    variant="text"
                                    onClick={() => {
                                        setImportOpen(true);
                                        setImportStep(0);
                                        setImportPin('');
                                        setBankPreviews([]);
                                        setCurrentImportIndex(0);
                                    }}
                                    disabled={!bankConnections || bankConnections.length === 0}
                                >
                                    {t('settings.bank.import')}
                                </Button>
                            </Box>
                        </Box>
                        <List sx={{
                            height: {
                                xs: '400px',
                                sm: 'calc(100vh - 420px)'
                            },
                            overflow: 'auto'
                        }}>
                            {sortedTransactions && sortedTransactions.length > 0 ? (
                                sortedTransactions.slice(0, visibleCount).map((tx, index) => {
                                    const txAccount = allAccounts?.find(acc => acc.id === tx.account_id);
                                    const targetAccount = tx.target_account_id ? allAccounts?.find(acc => acc.id === tx.target_account_id) : null;

                                    const isOwnTransaction = txAccount?.user_id === user?.id;
                                    const isTargetOwnAccount = targetAccount?.user_id === user?.id;
                                    const shouldHighlight = isOwnTransaction || (tx.type === TransactionType.Transfer && isTargetOwnAccount);

                                    const amountFormatted = formatCurrency(tx.amount);

                                    const txColor = tx.type === TransactionType.Income ? 'success.main' :
                                        tx.type === TransactionType.Expense ? 'error.main' :
                                            (!showAllUsers && tx.type === TransactionType.Transfer) ? (
                                                txAccount?.user_id === user?.id && targetAccount?.user_id !== user?.id ? 'error.main' :
                                                    targetAccount?.user_id === user?.id && txAccount?.user_id !== user?.id ? 'success.main' : 'text.primary'
                                            ) : 'text.primary';

                                    const TxIcon = tx.type === TransactionType.Income ? ArrowUpRight :
                                        tx.type === TransactionType.Transfer ? ArrowRight :
                                            ArrowDownRight;

                                    const iconColorKey = tx.type === TransactionType.Income ? 'success' :
                                        tx.type === TransactionType.Transfer ? 'info' : 'error';

                                    return (
                                        <React.Fragment key={tx.id}>
                                            <ListItem
                                                sx={{
                                                    px: 0,
                                                    cursor: isOwnTransaction ? 'pointer' : 'default',
                                                    '&:hover': {bgcolor: isOwnTransaction ? 'action.hover' : 'transparent'},
                                                    opacity: shouldHighlight ? 1 : 0.5
                                                }}
                                                onClick={() => isOwnTransaction && handleOpen(tx)}
                                            >
                                                <ListItemAvatar>
                                                    <Avatar sx={{
                                                        bgcolor: (theme: Theme) => theme.palette[iconColorKey].main,
                                                        color: (theme: Theme) => theme.palette.getContrastText(theme.palette[iconColorKey].main)
                                                    }}>
                                                        <TxIcon size={20}/>
                                                    </Avatar>
                                                </ListItemAvatar>
                                                <ListItemText
                                                    primary={tx.description}
                                                    secondary={tx.timestamp ? (
                                                        <Box component="span"
                                                             sx={{display: 'flex', alignItems: 'center', gap: 1}}>
                                                            <Typography component="span" variant="body2"
                                                                        color="text.secondary">
                                                                {formatTxDate(tx.timestamp)}
                                                            </Typography>
                                                        </Box>
                                                    ) : ''}
                                                    slotProps={{
                                                        primary: {fontWeight: 500},
                                                        secondary: {component: 'span'}
                                                    }}
                                                />
                                                <Box sx={{textAlign: 'right'}}>
                                                    <Typography variant="body1" sx={{
                                                        fontWeight: 'bold',
                                                        color: txColor
                                                    }}>
                                                        {amountFormatted}
                                                    </Typography>
                                                </Box>
                                            </ListItem>
                                            {index < Math.min(sortedTransactions.length, visibleCount) - 1 &&
                                                <Divider component="li"/>}
                                        </React.Fragment>
                                    );
                                })
                            ) : (
                                <Box sx={{
                                    py: 8,
                                    display: 'flex',
                                    flexDirection: 'column',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    opacity: 0.5
                                }}>
                                    <TrendingUp size={48} strokeWidth={1}/>
                                    <Typography variant="body1" sx={{mt: 2, textAlign: 'center', px: 3}}>
                                        {isSameMonth(selectedMonth, new Date())
                                            ? t('dashboard.transactions.emptyCurrent')
                                            : t('dashboard.transactions.emptyPast', {
                                                month: `${t(`common.months.${format(selectedMonth, 'MMM').toLowerCase()}`)} ${format(selectedMonth, 'yyyy')}`
                                            })
                                        }
                                    </Typography>
                                </Box>
                            )}
                            <div ref={observerTarget} style={{height: '10px'}}/>
                        </List>

                        <Box sx={{
                            mt: 2,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: 2
                        }}>
                            <IconButton
                                size="small"
                                onClick={() => setSelectedMonth(prev => addMonths(prev, 1))}
                                disabled={isCurrentMonth}
                            >
                                <ChevronLeft size={20}/>
                            </IconButton>

                            <Typography variant="body2" sx={{fontWeight: 'bold', minWidth: 120, textAlign: 'center'}}>
                                {`${t(`common.months.${format(selectedMonth, 'MMM').toLowerCase()}`)} ${format(selectedMonth, 'yy')}`}
                            </Typography>

                            <IconButton
                                size="small"
                                onClick={() => setSelectedMonth(prev => subMonths(prev, 1))}
                            >
                                <ChevronRight size={20}/>
                            </IconButton>
                        </Box>
                    </Paper>
                </Grid>

                <Grid size={{xs: 12, md: 4}}>
                    <Paper sx={{p: 3, height: '100%'}}>
                        <Typography variant="h6" sx={{fontWeight: 'bold', mb: 3}}>{t('budget.title')}</Typography>

                        {dashboardData?.budgets && dashboardData.budgets.length > 0 ? (
                            dashboardData.budgets
                                .map((budget) => {
                                    const spentAmount = Number(budget.spent_amount);
                                    const budgetAmount = Number(budget.budget_amount);
                                    const isOverspent = spentAmount > budgetAmount;
                                    const bluePercent = isOverspent
                                        ? (budgetAmount / spentAmount) * 100
                                        : (budgetAmount > 0 ? (spentAmount / budgetAmount) * 100 : 0);
                                    const redPercent = isOverspent ? 100 - bluePercent : 0;

                                    const owner = budget.user_id ? allUsers?.find(u => u.id === budget.user_id) : null;
                                    const categoryNameWithUser = budget.user_id && showAllUsers && owner
                                        ? `${budget.category_name} (${owner.name})`
                                        : budget.category_name;

                                    return (
                                        <Box key={budget.category_id + (budget.user_id || 'global')} sx={{mb: 2}}>
                                            <Box sx={{display: 'flex', justifyContent: 'space-between', mb: 0.5}}>
                                                <Typography variant="body2" sx={{fontWeight: 'medium'}}>
                                                    {categoryNameWithUser}
                                                </Typography>
                                                <Typography variant="body2" color="text.secondary">
                                                    {formatCurrency(spentAmount)} / {formatCurrency(budgetAmount)}
                                                </Typography>
                                            </Box>
                                            <Box sx={{
                                                height: 6,
                                                width: '100%',
                                                bgcolor: (theme) => theme.palette.mode === 'light' ? '#C2F0C2' : '#A3C4A3',
                                                borderRadius: 3,
                                                position: 'relative',
                                                overflow: 'hidden'
                                            }}>
                                                <Box sx={{
                                                    position: 'absolute',
                                                    left: 0,
                                                    top: 0,
                                                    height: '100%',
                                                    width: `${bluePercent}%`,
                                                    bgcolor: 'primary.main',
                                                    borderRadius: isOverspent ? 0 : 3
                                                }}/>
                                                {isOverspent && (
                                                    <Box sx={{
                                                        position: 'absolute',
                                                        left: `${bluePercent}%`,
                                                        top: 0,
                                                        height: '100%',
                                                        width: `${redPercent}%`,
                                                        bgcolor: (theme) => theme.palette.mode === 'light' ? '#FFABAB' : '#D49B9B'
                                                    }}/>
                                                )}
                                            </Box>
                                        </Box>
                                    );
                                })
                        ) : (
                            <Box sx={{
                                py: 4,
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                justifyContent: 'center',
                                opacity: 0.5,
                                textAlign: 'center'
                            }}>
                                <PiggyBank size={48} strokeWidth={1}/>
                                <Typography variant="body2" sx={{mt: 2}}>
                                    {t('budget.empty')}
                                </Typography>
                            </Box>
                        )}

                    </Paper>
                </Grid>
            </Grid>
            <Dialog open={open} onClose={handleClose} fullWidth maxWidth="xs">
                <DialogTitle>
                    {editingTransaction ? t('dashboard.transactions.dialog.editTitle') : t('dashboard.transactions.dialog.title')}
                </DialogTitle>
                <DialogContent>
                    <TransactionForm
                        data={{
                            ...newTx,
                            category_id: newTx.category_id || '',
                            target_account_id: newTx.target_account_id || ''
                        }}
                        onChange={(update) => setNewTx(prev => ({...prev, ...update}))}
                        allAccounts={allAccounts}
                        categories={categories}
                        transferTargets={transferTargets}
                        recurringPayments={recurringPayments}
                        user={user}
                        t={t}
                        disabledAccount={!!editingTransaction}
                    />
                </DialogContent>
                <DialogActions sx={{px: 3, pb: 3, justifyContent: 'space-between'}}>
                    <Box>
                        {editingTransaction && (
                            <Button
                                onClick={handleDeleteTransaction}
                                color="error"
                                startIcon={<Trash2 size={18}/>}
                                disabled={deleteTxMutation.isPending}
                            >
                                {t('dashboard.transactions.dialog.delete')}
                            </Button>
                        )}
                    </Box>
                    <Box sx={{display: 'flex', gap: 1}}>
                        <Button onClick={handleClose} color="inherit">
                            {t('dashboard.transactions.dialog.cancel')}
                        </Button>
                        <Button
                            onClick={handleCreateTransaction}
                            variant="contained"
                            disabled={
                                !newTx.description ||
                                !newTx.amount ||
                                !newTx.account_id ||
                                (newTx.type === TransactionType.Transfer && !newTx.target_account_id) ||
                                createTxMutation.isPending ||
                                updateTxMutation.isPending ||
                                createCategoryMutation.isPending ||
                                deleteTxMutation.isPending
                            }
                        >
                            {t('dashboard.transactions.dialog.submit')}
                        </Button>
                    </Box>
                </DialogActions>
            </Dialog>

            <Dialog
                open={importOpen}
                onClose={() => setImportOpen(false)}
                maxWidth="lg"
                fullWidth
                fullScreen={isMobile}
            >
                <DialogTitle>
                    {t('settings.bank.importTitle')}
                </DialogTitle>
                <DialogContent>
                    {importStep === 0 && (
                        <Box sx={{display: 'flex', flexDirection: 'column', gap: 2, mt: 1}}>
                            <FormControl fullWidth>
                                <InputLabel>{t('settings.bank.title')}</InputLabel>
                                <Select
                                    value={importConnection}
                                    label={t('settings.bank.title')}
                                    onChange={(e) => setImportConnection(e.target.value as string)}
                                >
                                    {bankConnections?.map((conn: BankConnection) => (
                                        <MenuItem key={conn.id} value={conn.id}>
                                            {conn.bank_name || conn.login}
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                            <TextField
                                type="password"
                                label={t('settings.bank.pin')}
                                value={importPin}
                                onChange={(e) => setImportPin(e.target.value)}
                                fullWidth
                            />
                            <TextField
                                type="date"
                                label={t('settings.bank.since')}
                                value={importSince}
                                onChange={(e) => setImportSince(e.target.value)}
                                fullWidth
                                InputLabelProps={{shrink: true}}
                            />
                            <Typography variant="caption" color="text.secondary">
                                {t('settings.bank.pinHint')}
                            </Typography>
                            <Alert severity="info" sx={{mt: 1}}>
                                {t('settings.bank.appSwitchHint')}
                            </Alert>
                        </Box>
                    )}

                    {importStep === 1 && (
                        <Box sx={{display: 'flex', flexDirection: 'column', alignItems: 'center', py: 6, gap: 2}}>
                            {!syncError ? (
                                <>
                                    <Box sx={{position: 'relative'}}>
                                        <PiggyBank size={128}/>
                                    </Box>
                                    <CircularProgress/>
                                    <Typography>
                                        {syncStatusData?.status === SyncTaskStatus.AWAITING_AUTHENTICATION
                                            ? t('settings.bank.status.AWAITING_AUTHENTICATION')
                                            : t('settings.bank.syncing')}
                                    </Typography>
                                    {syncStatusData?.status && syncStatusData.status !== SyncTaskStatus.AWAITING_AUTHENTICATION && (
                                        <Typography variant="body2" color="text.secondary">
                                            {t(`settings.bank.status.${syncStatusData.status}`)}
                                        </Typography>
                                    )}
                                    {syncStatusData?.status === SyncTaskStatus.AWAITING_AUTHENTICATION && (
                                        <Typography variant="body2" color="text.secondary" align="center">
                                            {t('settings.bank.appSwitchHint')}
                                        </Typography>
                                    )}
                                </>
                            ) : (
                                <>
                                    <AlertCircle size={48} color="#d32f2f"/>
                                    <Typography color="error" align="center">{t('settings.bank.syncError')}</Typography>
                                    <Box sx={{mt: 2, display: 'flex', gap: 2}}>
                                        <Button variant="outlined" onClick={() => setImportStep(0)}>
                                            {t('common.cancel')}
                                        </Button>
                                        <Button variant="contained" onClick={handleStartImport}>
                                            {t('settings.bank.retry')}
                                        </Button>
                                    </Box>
                                </>
                            )}
                        </Box>
                    )}

                    {importStep === 2 && (
                        <Box sx={{mt: 1}}>
                            <Box sx={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3}}>
                                <Box sx={{display: 'flex', alignItems: 'center', gap: 1}}>
                                    <IconButton
                                        onClick={() => setCurrentImportIndex(prev => Math.max(0, prev - 1))}
                                        disabled={currentImportIndex === 0}
                                        color="primary"
                                    >
                                        <ChevronLeft/>
                                    </IconButton>
                                    <Typography variant="h6" sx={{minWidth: '80px', textAlign: 'center'}}>
                                        {currentImportIndex + 1} / {bankPreviews.length}
                                    </Typography>
                                    <IconButton
                                        onClick={() => setCurrentImportIndex(prev => Math.min(bankPreviews.length - 1, prev + 1))}
                                        disabled={currentImportIndex === bankPreviews.length - 1}
                                        color="primary"
                                    >
                                        <ChevronRight/>
                                    </IconButton>
                                </Box>
                                <Box sx={{display: 'flex', alignItems: 'center', gap: 1}}>
                                    <Typography variant="body1" sx={{fontWeight: 'medium'}}>
                                        {t('settings.bank.import')}
                                    </Typography>
                                    <Checkbox
                                        checked={bankPreviews[currentImportIndex]?.selected || false}
                                        onChange={(e) => handleUpdatePreview(currentImportIndex, {selected: e.target.checked})}
                                        size="large"
                                    />
                                </Box>
                            </Box>

                            {bankPreviews.length === 0 ? (
                                <Typography variant="body2" color="text.secondary" align="center" sx={{py: 4}}>
                                    {t('settings.bank.noTransactions')}
                                </Typography>
                            ) : (
                                <Box sx={{maxWidth: '600px', mx: 'auto'}}>
                                    {bankPreviews[currentImportIndex]?.is_potential_duplicate && (
                                        <Alert severity="warning" icon={<AlertCircle size={20}/>} sx={{mb: 3}}>
                                            {t('settings.bank.potentialDuplicate')}
                                        </Alert>
                                    )}

                                    <TransactionForm
                                        data={{
                                            description: bankPreviews[currentImportIndex].description,
                                            amount: bankPreviews[currentImportIndex].amount.toString(),
                                            account_id: bankPreviews[currentImportIndex].account_id,
                                            target_account_id: bankPreviews[currentImportIndex].target_account_id || '',
                                            category_id: bankPreviews[currentImportIndex].category_id || '',
                                            type: bankPreviews[currentImportIndex].type || TransactionType.Expense,
                                            timestamp: bankPreviews[currentImportIndex].timestamp || format(new Date(), "yyyy-MM-dd'T'HH:mm")
                                        }}
                                        onChange={(update) => handleUpdatePreview(currentImportIndex, update)}
                                        allAccounts={allAccounts}
                                        categories={categories}
                                        transferTargets={transferTargets}
                                        recurringPayments={recurringPayments}
                                        user={user}
                                        t={t}
                                    />
                                </Box>
                            )}
                        </Box>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setImportOpen(false)}
                            startIcon={<X size={16}/>}>{t('common.cancel')}</Button>
                    {importStep === 0 && (
                        <Button onClick={handleStartImport} variant="contained" startIcon={<RefreshCw size={16}/>}
                                disabled={syncMutation.isPending || !importPin || !importSince || !importConnection}>
                            {t('settings.bank.sync')}
                        </Button>
                    )}
                    {importStep === 2 && (
                        <Button onClick={handleBulkAdd} variant="contained" startIcon={<Check size={16}/>}
                                disabled={bulkCreateMutation.isPending}>
                            {t('settings.bank.import')}
                        </Button>
                    )}
                </DialogActions>
            </Dialog>
        </Container>
    );
};

export default DashboardPage;
