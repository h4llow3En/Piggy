import React from 'react';
import {
    Autocomplete,
    Box,
    createFilterOptions,
    Divider,
    FormControl,
    InputAdornment,
    InputLabel,
    MenuItem,
    Select,
    TextField,
    Typography
} from '@mui/material';
import { TransactionType } from '../api/piggy';
import { formatCurrency } from '../utils/format';

const filter = createFilterOptions<CategoryOption>();

interface CategoryOption {
    id?: string;
    name: string;
    inputValue?: string;
}

interface TransactionFormProps {
    data: {
        description: string;
        amount: string;
        account_id: string;
        target_account_id: string;
        category_id: string;
        type: TransactionType;
        timestamp: string;
    };
    onChange: (update: Partial<TransactionFormProps['data']>) => void;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    allAccounts?: any[];
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    categories?: any[];
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    transferTargets?: any[];
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    recurringPayments?: any[];
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    user?: any;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    t: any;
    disabledAccount?: boolean;
}

const TransactionForm: React.FC<TransactionFormProps> = ({
    data,
    onChange,
    allAccounts,
    categories,
    transferTargets,
    recurringPayments,
    user,
    t,
    disabledAccount = false
}) => {
    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <Autocomplete
                fullWidth
                freeSolo
                options={recurringPayments || []}
                getOptionLabel={(option) => {
                    if (typeof option === 'string') return option;
                    return option.name;
                }}
                value={data.description}
                onInputChange={(_, newInputValue) => {
                    onChange({ description: newInputValue });
                }}
                onChange={(_, newValue) => {
                    if (newValue && typeof newValue !== 'string') {
                        onChange({
                            description: newValue.name,
                            amount: newValue.amount.toString(),
                            type: newValue.type,
                            account_id: newValue.account_id || data.account_id,
                            target_account_id: newValue.target_account_id || data.target_account_id,
                            category_id: newValue.category_id || data.category_id
                        });
                    }
                }}
                renderInput={(params) => (
                    <TextField
                        {...params}
                        label={t('dashboard.transactions.dialog.description')}
                        slotProps={{
                            htmlInput: {
                                ...params.inputProps,
                                autoCapitalize: 'sentences'
                            }
                        }}
                    />
                )}
            />
            <TextField
                fullWidth
                type="text"
                label={t('dashboard.transactions.dialog.amount')}
                value={data.amount}
                onChange={(e) => {
                    const val = e.target.value;
                    if (/^[0-9.,]*$/.test(val)) {
                        onChange({ amount: val });
                    }
                }}
                onBlur={() => {
                    if (data.amount) {
                        const val = parseFloat(data.amount.replace(',', '.'));
                        if (!isNaN(val)) {
                            onChange({ amount: val.toFixed(2) });
                        }
                    }
                }}
                slotProps={{
                    input: {
                        endAdornment: <InputAdornment position="end">€</InputAdornment>
                    },
                    htmlInput: {
                        inputMode: 'decimal'
                    }
                }}
            />
            <FormControl fullWidth disabled={disabledAccount}>
                <InputLabel>{t('dashboard.transactions.dialog.account')}</InputLabel>
                <Select
                    value={data.account_id}
                    label={t('dashboard.transactions.dialog.account')}
                    onChange={(e) => onChange({ account_id: e.target.value as string })}
                >
                    {allAccounts?.filter(acc => acc.user_id === user?.id).map((acc) => (
                        <MenuItem key={acc.id} value={acc.id}
                                  sx={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                            <Typography variant="body1">{acc.name}</Typography>
                            <Typography variant="body2" sx={{ color: 'text.secondary', ml: 2 }}>
                                {formatCurrency(acc.balance || '0')}
                            </Typography>
                        </MenuItem>
                    ))}
                </Select>
            </FormControl>
            <FormControl fullWidth>
                <InputLabel>{t('dashboard.transactions.dialog.type')}</InputLabel>
                <Select
                    value={data.type}
                    label={t('dashboard.transactions.dialog.type')}
                    onChange={(e) => {
                        const newType = e.target.value as TransactionType;
                        onChange({
                            type: newType,
                            category_id: newType === TransactionType.Transfer ? '' : data.category_id,
                            target_account_id: newType === TransactionType.Transfer ? data.target_account_id : ''
                        });
                    }}
                >
                    <MenuItem value={TransactionType.Expense}>{t('dashboard.transactions.dialog.expense')}</MenuItem>
                    <MenuItem value={TransactionType.Income}>{t('dashboard.transactions.dialog.income')}</MenuItem>
                    <MenuItem value={TransactionType.Transfer}>{t('dashboard.transactions.dialog.transfer')}</MenuItem>
                </Select>
            </FormControl>

            {data.type === TransactionType.Transfer && (
                <FormControl fullWidth>
                    <InputLabel>{t('dashboard.transactions.dialog.targetAccount')}</InputLabel>
                    <Select
                        value={data.target_account_id}
                        label={t('dashboard.transactions.dialog.targetAccount')}
                        onChange={(e) => onChange({ target_account_id: e.target.value as string })}
                    >
                        {transferTargets?.filter(acc => acc.id !== data.account_id).map((acc) => {
                            const isOwn = acc.user_id === user?.id;
                            const displayName = isOwn ? acc.name : `${acc.name} (${acc.user_name})`;

                            return (
                                <MenuItem key={acc.id} value={acc.id} sx={{
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    width: '100%'
                                }}>
                                    <Typography variant="body1">{displayName}</Typography>
                                    <Typography variant="body2" sx={{ color: 'text.secondary', ml: 2 }}>
                                        {formatCurrency(acc.balance || '0')}
                                    </Typography>
                                </MenuItem>
                            );
                        })}
                    </Select>
                </FormControl>
            )}

            {data.type !== TransactionType.Transfer && (
                <Autocomplete
                    value={
                        categories?.find((c) => c.id === data.category_id) ||
                        (data.category_id.startsWith('new:') ? { name: data.category_id.replace('new:', '') } : null)
                    }
                    onChange={(_, newValue) => {
                        if (typeof newValue === 'string') {
                            onChange({ category_id: `new:${newValue}` });
                        } else if (newValue && newValue.inputValue) {
                            onChange({ category_id: `new:${newValue.inputValue}` });
                        } else {
                            onChange({ category_id: newValue?.id || '' });
                        }
                    }}
                    filterOptions={(options, params) => {
                        const filtered = filter(options, params);
                        const { inputValue } = params;
                        const isExisting = options.some((option) => inputValue === option.name);
                        if (inputValue !== '' && !isExisting) {
                            filtered.push({
                                inputValue,
                                name: `${t('dashboard.transactions.dialog.add')} "${inputValue}"`,
                            });
                        }
                        return filtered;
                    }}
                    selectOnFocus
                    clearOnBlur
                    handleHomeEndKeys
                    options={(categories || []) as CategoryOption[]}
                    getOptionLabel={(option) => {
                        if (typeof option === 'string') return option;
                        if (option.inputValue) return option.inputValue;
                        return option.name;
                    }}
                    renderOption={(props, option) => {
                        const { key, ...optionProps } = props;
                        return <li key={key} {...optionProps}>{option.name}</li>;
                    }}
                    freeSolo
                    onBlur={(event) => {
                        const inputValue = (event.target as HTMLInputElement).value;
                        if (inputValue && !categories?.some(c => c.name === inputValue)) {
                            onChange({ category_id: `new:${inputValue}` });
                        }
                    }}
                    renderInput={(params) => (
                        <TextField {...params} label={t('dashboard.transactions.dialog.category')} />
                    )}
                />
            )}
            <FormControl fullWidth>
                <InputLabel shrink sx={{ backgroundColor: 'background.paper', px: 0.5, ml: -0.5 }}>
                    {t('dashboard.transactions.dialog.date')}
                </InputLabel>
                <Box sx={{
                    display: 'flex',
                    alignItems: 'center',
                    width: '100%',
                    border: (theme) => theme.palette.mode === 'light'
                        ? '1px solid rgba(0, 0, 0, 0.23)'
                        : '1px solid rgba(255, 255, 255, 0.23)',
                    borderRadius: 1,
                    minHeight: '56px',
                    px: 1,
                    '&:focus-within': {
                        borderWidth: '2px',
                        borderColor: 'primary.main',
                        m: '-1px'
                    },
                    '&:hover': {
                        borderColor: (theme) => theme.palette.mode === 'light'
                            ? 'rgba(0, 0, 0, 0.87)'
                            : 'rgba(255, 255, 255, 0.87)',
                    }
                }}>
                    <TextField
                        type="date"
                        variant="standard"
                        value={data.timestamp.split('T')[0]}
                        onChange={(e) => {
                            const timePart = data.timestamp.split('T')[1] || '12:00:00';
                            onChange({ timestamp: `${e.target.value}T${timePart}` });
                        }}
                        InputProps={{
                            disableUnderline: true,
                            sx: { px: 1, fontSize: '1rem' }
                        }}
                        sx={{ flex: 1.2 }}
                    />
                    <Divider orientation="vertical" flexItem sx={{ mx: 0.5, my: 1 }} />
                    <TextField
                        type="time"
                        variant="standard"
                        value={data.timestamp.split('T')[1]?.substring(0, 5) || '12:00'}
                        onChange={(e) => {
                            const datePart = data.timestamp.split('T')[0];
                            onChange({ timestamp: `${datePart}T${e.target.value}:00` });
                        }}
                        InputProps={{
                            disableUnderline: true,
                            sx: { px: 1, fontSize: '1rem' }
                        }}
                        sx={{ flex: 1 }}
                    />
                </Box>
            </FormControl>
        </Box>
    );
};

export default TransactionForm;
