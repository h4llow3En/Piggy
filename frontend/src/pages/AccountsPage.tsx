import {useQueryClient} from '@tanstack/react-query';
import {type FC, type ReactNode, useState} from 'react';
import {
    Box,
    Button,
    Container,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    FormControl,
    Grid,
    IconButton,
    InputAdornment,
    InputLabel,
    LinearProgress,
    MenuItem,
    Paper,
    Select,
    TextField,
    Typography
} from '@mui/material';
import {CreditCard, Edit2, GripVertical, Landmark, PiggyBank, Plus, Trash2} from 'lucide-react';
import {useTranslation} from 'react-i18next';
import {useAuth} from '../context/AuthContext';
import {formatCurrency} from '../utils/format';
import type {Account, AccountCreate, AccountUpdate} from '../api/piggy';
import {
    AccountType,
    getReadAccountsApiV1AccountsGetQueryKey,
    useCreateAccountApiV1AccountsPost,
    useDeleteAccountApiV1AccountsAccountIdDelete,
    useReadAccountsApiV1AccountsGet,
    useUpdateAccountApiV1AccountsAccountIdPut,
    useUpdateAccountsSortApiV1AccountsSortPut
} from '../api/piggy';

import type {DragEndEvent} from '@dnd-kit/core';
import {closestCenter, DndContext, KeyboardSensor, PointerSensor, useSensor, useSensors} from '@dnd-kit/core';
import {
    arrayMove,
    SortableContext,
    sortableKeyboardCoordinates,
    useSortable,
    verticalListSortingStrategy
} from '@dnd-kit/sortable';
import {CSS} from '@dnd-kit/utilities';

interface SortableAccountItemProps {
    account: Account;
    getAccountIcon: (type: AccountType) => ReactNode;
    handleOpen: (account: Account) => void;
    handleDelete: (accountId: string) => void;
    t: (key: string) => string;
}

const SortableAccountItem: FC<SortableAccountItemProps> = ({
                                                               account,
                                                               getAccountIcon,
                                                               handleOpen,
                                                               handleDelete,
                                                               t
                                                           }) => {
    const {
        attributes,
        listeners,
        setNodeRef,
        transform,
        transition,
        isDragging
    } = useSortable({id: account.id});

    const style = {
        transform: CSS.Transform.toString(transform),
        transition,
        zIndex: isDragging ? 1 : 0,
        opacity: isDragging ? 0.5 : 1,
    };

    return (
        <Grid size={{xs: 12}} ref={setNodeRef} style={style}>
            <Paper sx={{p: 2, width: '100%'}}>
                <Box sx={{
                    display: 'flex',
                    alignItems: 'center',
                    width: '100%',
                    gap: {xs: 1, sm: 2},
                }}>
                    <Box {...attributes} {...listeners}
                         sx={{
                             cursor: 'grab',
                             display: 'flex',
                             color: 'text.secondary',
                             flexShrink: 0,
                             alignItems: 'center',
                             justifyContent: 'center'
                         }}>
                        <GripVertical size={20}/>
                    </Box>

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
                        {getAccountIcon(account.type)}
                    </Box>

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
                            <Typography variant="h6" sx={{fontWeight: 'bold'}}>
                                {account.name}
                            </Typography>
                            <Typography variant="body2" color="text.secondary" sx={{
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap',
                                maxWidth: {xs: '60vw', sm: '100%'}
                            }}>
                                {t(`accounts.types.${account.type.toLowerCase().replace(' ', '_')}`)} {account.iban ? `• ${account.iban}` : ''}
                            </Typography>
                        </Box>

                        <Box sx={{
                            textAlign: {xs: 'left', sm: 'right'},
                            display: 'flex',
                            alignItems: 'center',
                            flexShrink: 0,
                            width: {xs: '100%', sm: 'auto'},
                        }}>
                            <Typography variant="h6" sx={{fontWeight: 'bold', whiteSpace: 'nowrap'}}>
                                {formatCurrency(account.balance || '0')}
                            </Typography>
                        </Box>
                    </Box>

                    <Box sx={{
                        display: 'flex',
                        alignItems: 'center',
                        flexShrink: 0,
                        gap: 0.5
                    }}>
                        <IconButton size="small" onClick={() => handleOpen(account)}>
                            <Edit2 size={18}/>
                        </IconButton>
                        <IconButton size="small" color="error" onClick={() => handleDelete(account.id)}>
                            <Trash2 size={18}/>
                        </IconButton>
                    </Box>
                </Box>
            </Paper>
        </Grid>
    );
};

const AccountsPage: FC = () => {
    const {t} = useTranslation();
    const queryClient = useQueryClient();
    useAuth();

    const {data: accountsData, isLoading} = useReadAccountsApiV1AccountsGet({
        all_users: false
    });

    const accounts = accountsData || [];

    const invalidateAccounts = () => {
        queryClient.invalidateQueries({
            queryKey: getReadAccountsApiV1AccountsGetQueryKey({all_users: false})
        });
        // Invalidate transfer targets as they depend on accounts
        queryClient.invalidateQueries({
            queryKey: ['/api/v1/accounts/transfer-targets']
        });
    };

    const createAccountMutation = useCreateAccountApiV1AccountsPost({
        mutation: {
            onSuccess: invalidateAccounts
        }
    });
    const updateAccountMutation = useUpdateAccountApiV1AccountsAccountIdPut({
        mutation: {
            onSuccess: invalidateAccounts
        }
    });
    const deleteAccountMutation = useDeleteAccountApiV1AccountsAccountIdDelete({
        mutation: {
            onSuccess: invalidateAccounts
        }
    });
    const updateSortMutation = useUpdateAccountsSortApiV1AccountsSortPut({
        mutation: {
            onSuccess: invalidateAccounts
        }
    });

    const [open, setOpen] = useState(false);
    const [editingAccount, setEditingAccount] = useState<Account | null>(null);
    const [newAccount, setNewAccount] = useState<{
        name: string;
        type: AccountType;
        iban: string;
        balance: string;
    }>({
        name: '',
        type: AccountType.Giro,
        iban: '',
        balance: '0'
    });

    const sensors = useSensors(
        useSensor(PointerSensor, {
            activationConstraint: {
                distance: 8,
            },
        }),
        useSensor(KeyboardSensor, {
            coordinateGetter: sortableKeyboardCoordinates,
        })
    );

    const handleDragEnd = async (event: DragEndEvent) => {
        const {active, over} = event;

        if (over && active.id !== over.id) {
            const oldIndex = accounts.findIndex((i) => i.id === active.id);
            const newIndex = accounts.findIndex((i) => i.id === over.id);
            const newArray = arrayMove(accounts, oldIndex, newIndex);

            // Push update to backend
            const sortData = newArray.map((acc, index) => ({
                account_id: acc.id,
                sort_order: index
            }));

            updateSortMutation.mutate({data: sortData});
        }
    };

    const handleOpen = (account?: Account) => {
        if (account) {
            setEditingAccount(account);
            setNewAccount({
                name: account.name,
                type: account.type,
                iban: account.iban || '',
                balance: account.balance || '0'
            });
        } else {
            setEditingAccount(null);
            setNewAccount({
                name: '',
                type: AccountType.Giro,
                iban: '',
                balance: '0'
            });
        }
        setOpen(true);
    };

    const handleClose = () => {
        setOpen(false);
        setEditingAccount(null);
    };

    const handleSave = async () => {
        try {
            if (editingAccount) {
                const payload: AccountUpdate = {
                    name: newAccount.name,
                    iban: newAccount.iban || null,
                    balance: newAccount.balance
                };
                await updateAccountMutation.mutateAsync({
                    accountId: editingAccount.id,
                    data: payload
                });
            } else {
                const payload: AccountCreate = {
                    name: newAccount.name,
                    type: newAccount.type,
                    iban: newAccount.iban || null,
                    balance: newAccount.balance
                };
                await createAccountMutation.mutateAsync({
                    data: payload
                });
            }
            handleClose();
            // eslint-disable-next-line @typescript-eslint/no-unused-vars
        } catch (_error) {
            // Error handled globally via interceptor
        }
    };

    const handleDelete = async (accountId: string) => {
        if (window.confirm(t('accounts.deleteConfirm'))) {
            try {
                await deleteAccountMutation.mutateAsync({accountId});
                // eslint-disable-next-line @typescript-eslint/no-unused-vars
            } catch (_error) {
                // Error handled globally via interceptor
            }
        }
    };

    const getAccountIcon = (type: AccountType) => {
        switch (type) {
            case AccountType.Credit_Card:
                return <CreditCard size={24}/>;
            case AccountType.Savings:
                return <PiggyBank size={24}/>;
            default:
                return <Landmark size={24}/>;
        }
    };

    if (isLoading) return <LinearProgress/>;

    return (
        <Container maxWidth="lg" sx={{py: 4}}>
            <Box sx={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2}}>
                <Typography variant="h4" sx={{fontWeight: 'bold', color: 'text.primary'}}>
                    {t('accounts.title')}
                </Typography>
                <Button
                    variant="contained"
                    startIcon={<Plus size={18}/>}
                    onClick={() => handleOpen()}
                >
                    {t('accounts.new')}
                </Button>
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{mb: 4}}>
                {t('accounts.sortingHint')}
            </Typography>
            <DndContext
                sensors={sensors}
                collisionDetection={closestCenter}
                onDragEnd={handleDragEnd}
            >
                <SortableContext
                    items={accounts.map(a => a.id)}
                    strategy={verticalListSortingStrategy}
                >
                    <Grid container spacing={3}>
                        {accounts.map((account) => (
                            <SortableAccountItem
                                key={account.id}
                                account={account}
                                getAccountIcon={getAccountIcon}
                                handleOpen={handleOpen}
                                handleDelete={handleDelete}
                                t={t}
                            />
                        ))}
                    </Grid>
                </SortableContext>
            </DndContext>
            <Dialog open={open} onClose={handleClose} fullWidth maxWidth="xs">
                <DialogTitle>
                    {editingAccount ? t('accounts.editTitle') : t('accounts.newTitle')}
                </DialogTitle>
                <DialogContent>
                    <Box sx={{display: 'flex', flexDirection: 'column', gap: 2, pt: 1}}>
                        <TextField
                            fullWidth
                            label={t('accounts.name')}
                            value={newAccount.name}
                            onChange={(e) => setNewAccount({...newAccount, name: e.target.value})}
                        />
                        <FormControl fullWidth disabled={!!editingAccount}>
                            <InputLabel>{t('accounts.type')}</InputLabel>
                            <Select
                                value={newAccount.type}
                                label={t('accounts.type')}
                                onChange={(e) => {
                                    const newType = e.target.value as AccountType;
                                    setNewAccount({
                                        ...newAccount,
                                        type: newType,
                                    });
                                }}
                            >
                                {Object.values(AccountType).map((type) => (
                                    <MenuItem key={type} value={type}>
                                        {t(`accounts.types.${type.toLowerCase()}`)}
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                        <TextField
                            fullWidth
                            label={t('accounts.iban')}
                            value={newAccount.iban}
                            onChange={(e) => setNewAccount({...newAccount, iban: e.target.value})}
                            disabled={!!editingAccount}
                        />
                        <TextField
                            fullWidth
                            label={t('accounts.balance')}
                            value={newAccount.balance}
                            onChange={(e) => {
                                const val = e.target.value;
                                if (/^-?[0-9.,]*$/.test(val)) {
                                    setNewAccount({...newAccount, balance: val});
                                }
                            }}
                            onBlur={() => {
                                const val = parseFloat(newAccount.balance.replace(',', '.'));
                                if (!isNaN(val)) {
                                    setNewAccount({...newAccount, balance: val.toFixed(2)});
                                }
                            }}
                            slotProps={{
                                input: {
                                    endAdornment: <InputAdornment position="end">€</InputAdornment>
                                }
                            }}
                        />
                    </Box>
                </DialogContent>
                <DialogActions sx={{px: 3, pb: 3}}>
                    <Button onClick={handleClose} color="inherit">
                        {t('common.cancel')}
                    </Button>
                    <Button
                        onClick={handleSave}
                        variant="contained"
                        disabled={!newAccount.name || createAccountMutation.isPending || updateAccountMutation.isPending}
                    >
                        {t('common.save')}
                    </Button>
                </DialogActions>
            </Dialog>
        </Container>
    );
};

export default AccountsPage;
