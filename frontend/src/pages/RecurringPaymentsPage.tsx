import React, {useState} from 'react';
import {useQueryClient} from '@tanstack/react-query';
import {
    Box,
    Button,
    Chip,
    Container,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    FormControl,
    FormControlLabel,
    Grid,
    IconButton,
    InputLabel,
    LinearProgress,
    MenuItem,
    Paper,
    Select,
    Switch,
    TextField,
    Typography
} from '@mui/material';
import {Calendar, Edit2, Plus, Repeat, Trash2} from 'lucide-react';
import {useTranslation} from 'react-i18next';
import {formatCurrency} from '../utils/format';
import type {
    RecurringPayment,
    RecurringPaymentCreate,
    RecurringPaymentUpdate,
    SubscriptionCandidateResponse
} from '../api/piggy';
import {
    getReadRecurringPaymentsApiV1RecurringPaymentsGetQueryKey,
    RecurringInterval,
    TransactionType,
    useCreateRecurringPaymentApiV1RecurringPaymentsPost,
    useDeleteRecurringPaymentApiV1RecurringPaymentsRecurringPaymentIdDelete,
    useReadAccountsApiV1AccountsGet,
    useReadCategoriesApiV1CategoriesGet,
    useReadRecurringPaymentsApiV1RecurringPaymentsGet,
    useReadTransferTargetsApiV1AccountsTransferTargetsGet,
    useUpdateRecurringPaymentApiV1RecurringPaymentsRecurringPaymentIdPut,
    useGetCachedRecurringPaymentsApiV1RecurringPaymentsDetectGet,
    useAddRecurringPaymentIgnoreApiV1RecurringPaymentsDetectIgnorePost,
    getGetCachedRecurringPaymentsApiV1RecurringPaymentsDetectGetQueryKey,
} from '../api/piggy';
import {addDays, addMonths, addWeeks, addYears, format, isAfter, isBefore, parseISO, startOfDay} from 'date-fns';
import {Check, X} from 'lucide-react';

interface RecurringFormData {
    name: string;
    amount: string;
    type: TransactionType;
    interval: RecurringInterval;
    interval_x_days: number;
    start_date: string;
    is_subscription: boolean;
    account_id: string;
    target_account_id: string;
    category_id: string;
}

const RecurringPaymentsPage: React.FC = () => {
    const {t} = useTranslation();
    const queryClient = useQueryClient();

    const getNextOccurrence = (startDateStr: string, interval: RecurringInterval, intervalXDays: number | null) => {
        const today = startOfDay(new Date());
        let nextDate = startOfDay(parseISO(startDateStr));

        // If the start date is in the future, that is the next execution
        if (isAfter(nextDate, today) || nextDate.getTime() === today.getTime()) {
            return nextDate;
        }

        // Otherwise we calculate the next date based on the interval
        while (isBefore(nextDate, today)) {
            switch (interval) {
                case RecurringInterval.Daily:
                    nextDate = addDays(nextDate, 1);
                    break;
                case RecurringInterval.Weekly:
                    nextDate = addWeeks(nextDate, 1);
                    break;
                case RecurringInterval.Monthly:
                    nextDate = addMonths(nextDate, 1);
                    break;
                case RecurringInterval.Yearly:
                    nextDate = addYears(nextDate, 1);
                    break;
                case RecurringInterval.Every_X_Days:
                    nextDate = addDays(nextDate, intervalXDays || 30);
                    break;
                default:
                    return nextDate;
            }
        }

        return nextDate;
    };

    const {data: payments, isLoading} = useReadRecurringPaymentsApiV1RecurringPaymentsGet();
    const {data: suggestions} = useGetCachedRecurringPaymentsApiV1RecurringPaymentsDetectGet();
    const {data: accounts} = useReadAccountsApiV1AccountsGet();
    const {data: categories} = useReadCategoriesApiV1CategoriesGet();
    const {data: transferTargets} = useReadTransferTargetsApiV1AccountsTransferTargetsGet();

    const invalidatePayments = () => {
        queryClient.invalidateQueries({
            queryKey: getReadRecurringPaymentsApiV1RecurringPaymentsGetQueryKey()
        });
    };

    const invalidateSuggestions = () => {
        queryClient.invalidateQueries({
            queryKey: getGetCachedRecurringPaymentsApiV1RecurringPaymentsDetectGetQueryKey()
        });
    };

    const createMutation = useCreateRecurringPaymentApiV1RecurringPaymentsPost({
        mutation: {
            onSuccess: () => {
                invalidatePayments();
                invalidateSuggestions();
            }
        }
    });

    const ignoreMutation = useAddRecurringPaymentIgnoreApiV1RecurringPaymentsDetectIgnorePost({
        mutation: {
            onSuccess: invalidateSuggestions
        }
    });
    const updateMutation = useUpdateRecurringPaymentApiV1RecurringPaymentsRecurringPaymentIdPut({
        mutation: {
            onSuccess: invalidatePayments
        }
    });
    const deleteMutation = useDeleteRecurringPaymentApiV1RecurringPaymentsRecurringPaymentIdDelete({
        mutation: {
            onSuccess: invalidatePayments
        }
    });

    const [open, setOpen] = useState(false);
    const [editingPayment, setEditingPayment] = useState<RecurringPayment | null>(null);
    const [formData, setFormData] = useState<RecurringFormData>({
        name: '',
        amount: '',
        type: TransactionType.Expense,
        interval: RecurringInterval.Every_X_Days,
        interval_x_days: 30,
        start_date: format(new Date(), 'yyyy-MM-dd'),
        is_subscription: false,
        account_id: '',
        target_account_id: '',
        category_id: ''
    });

    const handleOpen = (payment?: RecurringPayment | SubscriptionCandidateResponse) => {
        if (payment) {
            const isSuggestion = !('id' in payment);
            if (isSuggestion) {
                setEditingPayment(null);
                setFormData({
                    name: payment.name,
                    amount: Math.abs(parseFloat(payment.amount)).toFixed(2),
                    type: parseFloat(payment.amount) > 0 ? TransactionType.Income : TransactionType.Expense,
                    interval: payment.interval,
                    interval_x_days: 30, // Default for suggestions as backend doesn't provide interval_x_days yet
                    start_date: payment.last_date,
                    is_subscription: true,
                    account_id: '',
                    target_account_id: '',
                    category_id: ''
                });
            } else {
                setEditingPayment(payment);
                setFormData({
                    name: payment.name,
                    amount: payment.amount.toString(),
                    type: payment.type ?? TransactionType.Expense,
                    interval: payment.interval ?? RecurringInterval.Every_X_Days,
                    interval_x_days: payment.interval_x_days || 30,
                    start_date: payment.start_date,
                    is_subscription: payment.is_subscription ?? false,
                    account_id: payment.account_id || '',
                    target_account_id: payment.target_account_id || '',
                    category_id: payment.category_id || ''
                });
            }
        } else {
            setEditingPayment(null);
            setFormData({
                name: '',
                amount: '',
                type: TransactionType.Expense,
                interval: RecurringInterval.Every_X_Days,
                interval_x_days: 30,
                start_date: format(new Date(), 'yyyy-MM-dd'),
                is_subscription: false,
                account_id: '',
                target_account_id: '',
                category_id: ''
            });
        }
        setOpen(true);
    };

    const handleClose = () => {
        setOpen(false);
        setEditingPayment(null);
    };

    const handleSave = async () => {
        if (!formData.name || !formData.amount) return;

        try {
            if (editingPayment) {
                const data: RecurringPaymentUpdate = {
                    name: formData.name,
                    amount: parseFloat(formData.amount.replace(',', '.')),
                    type: formData.type,
                    interval: formData.interval,
                    interval_x_days: formData.interval === RecurringInterval.Every_X_Days ? formData.interval_x_days : null,
                    start_date: formData.start_date,
                    is_subscription: formData.is_subscription,
                    account_id: formData.account_id || null,
                    target_account_id: formData.type === TransactionType.Transfer ? (formData.target_account_id || null) : null,
                    category_id: formData.type !== TransactionType.Transfer ? (formData.category_id || null) : null
                };
                await updateMutation.mutateAsync({
                    recurringPaymentId: editingPayment.id,
                    data
                });
            } else {
                const data: RecurringPaymentCreate = {
                    name: formData.name,
                    amount: parseFloat(formData.amount.replace(',', '.')),
                    type: formData.type,
                    interval: formData.interval,
                    interval_x_days: formData.interval === RecurringInterval.Every_X_Days ? formData.interval_x_days : null,
                    start_date: formData.start_date,
                    is_subscription: formData.is_subscription,
                    account_id: formData.account_id || null,
                    target_account_id: formData.type === TransactionType.Transfer ? (formData.target_account_id || null) : null,
                    category_id: formData.type !== TransactionType.Transfer ? (formData.category_id || null) : null
                };
                await createMutation.mutateAsync({
                    data
                });
            }
            handleClose();
            // eslint-disable-next-line @typescript-eslint/no-unused-vars
        } catch (_error) {
            // Error handled globally via interceptor
        }
    };

    const handleDelete = async (id: string) => {
        if (window.confirm(t('dashboard.recurring.deleteConfirm'))) {
            try {
                await deleteMutation.mutateAsync({recurringPaymentId: id});
                // eslint-disable-next-line @typescript-eslint/no-unused-vars
            } catch (_error) {
                // Error handled globally via interceptor
            }
        }
    };

    const handleIgnore = async (suggestion: SubscriptionCandidateResponse) => {
        try {
            await ignoreMutation.mutateAsync({
                params: {
                    name: suggestion.name,
                    amount: suggestion.amount
                }
            });
            // eslint-disable-next-line @typescript-eslint/no-unused-vars
        } catch (_error) {
            // Error handled globally via interceptor
        }
    };

    if (isLoading) return <LinearProgress/>;

    return (
        <Container maxWidth="lg" sx={{py: 4}}>
            <Box sx={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4}}>
                <Typography variant="h4" sx={{fontWeight: 'bold', color: 'text.primary'}}>
                    {t('dashboard.recurring.title')}
                </Typography>
                <Button
                    variant="contained"
                    startIcon={<Plus size={18}/>}
                    onClick={() => handleOpen()}
                >
                    {t('dashboard.recurring.new')}
                </Button>
            </Box>

            {suggestions && suggestions.length > 0 && (
                <Box sx={{mb: 6}}>
                    <Typography variant="h5" sx={{fontWeight: 'bold', mb: 1}}>
                        {t('dashboard.recurring.suggested.title')}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{mb: 3}}>
                        {t('dashboard.recurring.suggested.description')}
                    </Typography>
                    <Grid container spacing={2}>
                        {suggestions.map((suggestion, index) => (
                            <Grid key={index} size={{xs: 12, md: 6}}>
                                <Paper sx={{
                                    p: 2,
                                    border: '1px solid',
                                    borderColor: 'divider',
                                    bgcolor: (theme) => theme.palette.mode === 'light' ? 'primary.50' : 'rgba(25, 118, 210, 0.08)'
                                }}>
                                    <Box sx={{display: 'flex', alignItems: 'center', gap: 2}}>
                                        <Box sx={{
                                            p: 1,
                                            borderRadius: 2,
                                            bgcolor: 'primary.main',
                                            color: 'primary.contrastText',
                                            display: 'flex'
                                        }}>
                                            <Repeat size={20}/>
                                        </Box>
                                        <Box sx={{flexGrow: 1, minWidth: 0}}>
                                            <Typography variant="subtitle1" sx={{
                                                fontWeight: 'bold',
                                                whiteSpace: 'nowrap',
                                                overflow: 'hidden',
                                                textOverflow: 'ellipsis'
                                            }}>
                                                {suggestion.name}
                                            </Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                {t(`dashboard.recurring.intervals.${suggestion.interval}`)} • {t('dashboard.recurring.suggested.count')}: {suggestion.count}
                                            </Typography>
                                        </Box>
                                        <Box sx={{textAlign: 'right', mr: 1}}>
                                            <Typography variant="subtitle1" sx={{
                                                fontWeight: 'bold',
                                                color: parseFloat(suggestion.amount) > 0 ? 'success.main' : 'text.primary'
                                            }}>
                                                {parseFloat(suggestion.amount) > 0 ? '+' : ''}{formatCurrency(suggestion.amount)}
                                            </Typography>
                                            <Typography variant="caption" color="text.secondary">
                                                {t('dashboard.recurring.suggested.lastDate')}: {format(parseISO(suggestion.last_date), 'dd.MM.yy')}
                                            </Typography>
                                        </Box>
                                        <Box sx={{display: 'flex', gap: 0.5}}>
                                            <IconButton
                                                size="small"
                                                color="primary"
                                                onClick={() => handleOpen(suggestion)}
                                                title={t('dashboard.recurring.suggested.accept')}
                                            >
                                                <Check size={20}/>
                                            </IconButton>
                                            <IconButton
                                                size="small"
                                                color="error"
                                                onClick={() => handleIgnore(suggestion)}
                                                title={t('dashboard.recurring.suggested.ignore')}
                                            >
                                                <X size={20}/>
                                            </IconButton>
                                        </Box>
                                    </Box>
                                </Paper>
                            </Grid>
                        ))}
                    </Grid>
                </Box>
            )}

            <Grid container spacing={3}>
                {payments?.map((payment) => (
                    <Grid key={payment.id} size={{xs: 12}}>
                        <Paper sx={{p: 2}}>
                            <Box sx={{
                                display: 'flex',
                                alignItems: 'center',
                                width: '100%',
                                gap: {xs: 1, sm: 2},
                            }}>
                                {/* Icon (anchored left) */}
                                <Box sx={{
                                    p: 1.5,
                                    borderRadius: 3,
                                    bgcolor: 'primary.main',
                                    color: 'primary.contrastText',
                                    display: 'flex',
                                    flexShrink: 0,
                                    alignItems: 'center',
                                    justifyContent: 'center'
                                }}>
                                    <Repeat size={20}/>
                                </Box>

                                {/* Wrappable middle part */}
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
                                    {/* Left info column */}
                                    <Box sx={{minWidth: 0, flex: 1}}>
                                        <Box sx={{display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap'}}>
                                            <Typography variant="h6" sx={{
                                                fontWeight: 'bold',
                                                whiteSpace: 'nowrap',
                                                overflow: 'hidden',
                                                textOverflow: 'ellipsis',
                                                maxWidth: {xs: '100%', sm: 'auto'}
                                            }}>
                                                {payment.name}
                                            </Typography>
                                            {payment.is_subscription && (
                                                <Chip label="Abo" size="small" color="secondary" variant="outlined" sx={{height: 20}}/>
                                            )}
                                        </Box>
                                        <Typography variant="body2" color="text.secondary"
                                                    sx={{display: 'flex', alignItems: 'center', gap: 0.5}}>
                                            <Calendar size={14}/>
                                            {payment.interval === RecurringInterval.Every_X_Days
                                                ? `${t('dashboard.recurring.intervals.Every X Days').replace('X', payment.interval_x_days?.toString() || 'X')}`
                                                : t(`dashboard.recurring.intervals.${payment.interval}`)}{' '}
                                            • {t('dashboard.recurring.nextDate')}: {format(getNextOccurrence(payment.start_date, payment.interval ?? RecurringInterval.Every_X_Days, payment.interval_x_days ?? null), 'dd.MM.yyyy')}
                                        </Typography>
                                    </Box>

                                    {/* Amount (right in the wrap container, may wrap on xs) */}
                                    <Box sx={{
                                        textAlign: {xs: 'left', sm: 'right'},
                                        display: 'flex',
                                        alignItems: 'center',
                                        flexShrink: 0,
                                        width: {xs: '100%', sm: 'auto'},
                                    }}>
                                        <Typography variant="h6" sx={{
                                            fontWeight: 'bold',
                                            whiteSpace: 'nowrap',
                                            color: payment.type === TransactionType.Income ? 'success.main' : 'text.primary'
                                        }}>
                                            {payment.type === TransactionType.Income ? '+' : payment.type === TransactionType.Expense ? '-' : ''}
                                            {formatCurrency(payment.amount)}
                                        </Typography>
                                    </Box>
                                </Box>

                                {/* Actions (anchored right) */}
                                <Box sx={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    flexShrink: 0,
                                    gap: 0.5
                                }}>
                                    <IconButton size="small" onClick={() => handleOpen(payment)}>
                                        <Edit2 size={18}/>
                                    </IconButton>
                                    <IconButton size="small" color="error" onClick={() => handleDelete(payment.id)}>
                                        <Trash2 size={18}/>
                                    </IconButton>
                                </Box>
                            </Box>
                        </Paper>
                    </Grid>
                ))}

                {(!payments || payments.length === 0) && (
                    <Grid size={{xs: 12}}>
                        <Paper sx={{p: 4, textAlign: 'center', opacity: 0.6}}>
                            <Typography variant="body1">
                                {t('dashboard.recurring.empty')}
                            </Typography>
                        </Paper>
                    </Grid>
                )}
            </Grid>
            <Dialog open={open} onClose={handleClose} fullWidth maxWidth="xs">
                <DialogTitle>
                    {editingPayment ? t('dashboard.recurring.edit') : t('dashboard.recurring.new')}
                </DialogTitle>
                <DialogContent dividers>
                    <Box sx={{display: 'flex', flexDirection: 'column', gap: 2.5, pt: 1}}>
                        <TextField
                            fullWidth
                            label={t('dashboard.recurring.name')}
                            value={formData.name}
                            onChange={(e) => setFormData({...formData, name: e.target.value})}
                            placeholder="e.g. Rent, Netflix..."
                        />

                        <Grid container spacing={2}>
                            <Grid size={{xs: 8}}>
                                <TextField
                                    fullWidth
                                    label={t('dashboard.recurring.amount')}
                                    value={formData.amount}
                                    onChange={(e) => {
                                        const val = e.target.value;
                                        if (/^[0-9.,]*$/.test(val)) {
                                            setFormData({...formData, amount: val});
                                        }
                                    }}
                                    onBlur={() => {
                                        if (formData.amount) {
                                            const val = parseFloat(formData.amount.replace(',', '.'));
                                            if (!isNaN(val)) {
                                                setFormData({...formData, amount: val.toFixed(2)});
                                            }
                                        }
                                    }}
                                    slotProps={{
                                        input: {
                                            startAdornment: <Typography sx={{mr: 1}}>€</Typography>,
                                        },
                                        htmlInput: {
                                            inputMode: 'decimal'
                                        }
                                    }}
                                />
                            </Grid>
                            <Grid size={{xs: 4}}>
                                <FormControl fullWidth>
                                    <InputLabel>{t('dashboard.transactions.dialog.type')}</InputLabel>
                                    <Select
                                        value={formData.type}
                                        label={t('dashboard.transactions.dialog.type')}
                                        onChange={(e) => setFormData({
                                            ...formData,
                                            type: e.target.value as TransactionType
                                        })}
                                    >
                                        <MenuItem
                                            value={TransactionType.Income}>{t('dashboard.transactions.dialog.income')}</MenuItem>
                                        <MenuItem
                                            value={TransactionType.Expense}>{t('dashboard.transactions.dialog.expense')}</MenuItem>
                                        <MenuItem
                                            value={TransactionType.Transfer}>{t('dashboard.transactions.dialog.transfer')}</MenuItem>
                                    </Select>
                                </FormControl>
                            </Grid>
                        </Grid>

                        <Box sx={{
                            p: 2,
                            bgcolor: (theme) => theme.palette.mode === 'light' ? 'grey.50' : 'grey.900',
                            borderRadius: 1,
                            border: '1px solid',
                            borderColor: 'divider'
                        }}>
                            <Typography variant="subtitle2" gutterBottom sx={{fontWeight: 'bold'}}>
                                {t('dashboard.recurring.interval')}
                            </Typography>
                            <Grid container spacing={2} alignItems="center">
                                <Grid size={{xs: formData.interval === RecurringInterval.Every_X_Days ? 6 : 12}}>
                                    <FormControl fullWidth size="small">
                                        <Select
                                            value={formData.interval}
                                            onChange={(e) => setFormData({
                                                ...formData,
                                                interval: e.target.value as RecurringInterval
                                            })}
                                        >
                                            {Object.values(RecurringInterval).map((interval) => (
                                                <MenuItem key={interval} value={interval}>
                                                    {t(`dashboard.recurring.intervals.${interval}`)}
                                                </MenuItem>
                                            ))}
                                        </Select>
                                    </FormControl>
                                </Grid>
                                {formData.interval === RecurringInterval.Every_X_Days && (
                                    <Grid size={{xs: 6}}>
                                        <TextField
                                            fullWidth
                                            size="small"
                                            type="number"
                                            label={t('dashboard.recurring.everyXDays')}
                                            value={formData.interval_x_days}
                                            onChange={(e) => setFormData({
                                                ...formData,
                                                interval_x_days: parseInt(e.target.value) || 0
                                            })}
                                            slotProps={{
                                                input: {
                                                    endAdornment: <Typography variant="caption"
                                                                              sx={{ml: 1}}>{t('dashboard.recurring.days')}</Typography>,
                                                }
                                            }}
                                        />
                                    </Grid>
                                )}
                            </Grid>
                        </Box>

                        <TextField
                            fullWidth
                            type="date"
                            label={t('dashboard.recurring.startDate')}
                            value={formData.start_date}
                            onChange={(e) => setFormData({...formData, start_date: e.target.value})}
                            slotProps={{
                                inputLabel: {shrink: true}
                            }}
                        />

                        <Grid container spacing={2}>
                            <Grid size={{xs: formData.type === TransactionType.Transfer ? 6 : 12}}>
                                <FormControl fullWidth>
                                    <InputLabel>{t('dashboard.recurring.account')}</InputLabel>
                                    <Select
                                        value={formData.account_id}
                                        label={t('dashboard.recurring.account')}
                                        onChange={(e) => setFormData({...formData, account_id: e.target.value})}
                                    >
                                        <MenuItem value=""><em>None</em></MenuItem>
                                        {accounts?.map((acc) => (
                                            <MenuItem key={acc.id} value={acc.id}>{acc.name}</MenuItem>
                                        ))}
                                    </Select>
                                </FormControl>
                            </Grid>
                            {formData.type === TransactionType.Transfer && (
                                <Grid size={{xs: 6}}>
                                    <FormControl fullWidth>
                                        <InputLabel>{t('dashboard.recurring.targetAccount')}</InputLabel>
                                        <Select
                                            value={formData.target_account_id}
                                            label={t('dashboard.recurring.targetAccount')}
                                            onChange={(e) => setFormData({
                                                ...formData,
                                                target_account_id: e.target.value
                                            })}
                                        >
                                            <MenuItem value=""><em>None</em></MenuItem>
                                            {transferTargets?.map((acc) => (
                                                <MenuItem key={acc.id} value={acc.id}>
                                                    {acc.user_id === accounts?.[0]?.user_id ? acc.name : `${acc.name} (${acc.user_name})`}
                                                </MenuItem>
                                            ))}
                                        </Select>
                                    </FormControl>
                                </Grid>
                            )}
                        </Grid>

                        {formData.type !== TransactionType.Transfer && (
                            <FormControl fullWidth>
                                <InputLabel>{t('dashboard.recurring.category')}</InputLabel>
                                <Select
                                    value={formData.category_id}
                                    label={t('dashboard.recurring.category')}
                                    onChange={(e) => setFormData({...formData, category_id: e.target.value})}
                                >
                                    <MenuItem value=""><em>None</em></MenuItem>
                                    {categories?.map((cat) => (
                                        <MenuItem key={cat.id} value={cat.id}>{cat.name}</MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                        )}

                        <FormControlLabel
                            control={
                                <Switch
                                    checked={formData.is_subscription}
                                    onChange={(e) => setFormData({...formData, is_subscription: e.target.checked})}
                                />
                            }
                            label={t('dashboard.recurring.isSubscription')}
                        />
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleClose}>{t('common.cancel')}</Button>
                    <Button onClick={handleSave} variant="contained" color="primary">
                        {t('common.save')}
                    </Button>
                </DialogActions>
            </Dialog>
        </Container>
    );
};

export default RecurringPaymentsPage;
