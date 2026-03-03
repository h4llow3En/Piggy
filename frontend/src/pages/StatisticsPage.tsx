import React from 'react';
import {
    Box,
    Card,
    CardContent,
    Container,
    FormControl,
    Grid,
    InputLabel,
    LinearProgress,
    MenuItem,
    Paper,
    Select,
    Slider,
    Typography,
    Button
} from '@mui/material';
import {useTranslation} from 'react-i18next';
import {FileText} from 'lucide-react';
import {
    useGetAccountBalanceStatisticsApiV1StatisticBalanceGet,
    useGetBudgetUsageStatisticsApiV1StatisticBudgetGet,
    useGetCashflowStatisticsApiV1StatisticCashflowGet,
    useGetCategorySpendStatisticsApiV1StatisticCategoryGet,
    useReadUserMeApiV1UsersMeGet,
} from '../api/piggy';
import {format, parseISO, startOfDay} from 'date-fns';
import {
    Bar,
    BarChart,
    CartesianGrid,
    Legend,
    Line,
    LineChart,
    Pie,
    PieChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis
} from 'recharts';
import {AXIOS_INSTANCE} from "../api/axios-instance";
import {storage} from "../utils/storage";

// Helper functions
const currencyFormatter = (value: number | string) => {
    const num = typeof value === 'string' ? Number(value) : value;
    if (Number.isNaN(num)) return `${value}`;
    return new Intl.NumberFormat(undefined, {style: 'currency', currency: 'EUR', maximumFractionDigits: 2}).format(num);
};

const dateFormatter = (iso: string) => {
    const d = parseISO(iso);
    return format(d, 'dd.MM.');
};

const AccountBalanceChart: React.FC = () => {
    const {data, isLoading} = useGetAccountBalanceStatisticsApiV1StatisticBalanceGet();

    const todayStart = startOfDay(new Date());

    if (isLoading) return <LinearProgress/>;
    const stats = data ?? [];

    const allDates = Array.from(
        new Set(stats.flatMap(s => s.history.map(h => h.date))).values()
    ).sort((a, b) => parseISO(a).getTime() - parseISO(b).getTime());

    const merged = allDates.map(d => {
        const row: Record<string, string | number | null> = {date: d};
        const current = parseISO(d);
        stats.forEach(s => {
            const point = s.history.find(h => h.date === d);
            const val = point ? Number(point.balance) : null;
            const pastKey = `${s.name}__past`;
            const futureKey = `${s.name}__future`;
            if (current < todayStart) {
                row[pastKey] = val;
                row[futureKey] = null;
            } else if (current > todayStart) {
                row[pastKey] = null;
                row[futureKey] = val;
            } else {
                // Exactly today: Only in pastKey, so that the tooltip is not doubled,
                // but futureKey starts from tomorrow.
                // Wait, if futureKey starts only from tomorrow, there is a gap.
                // Better: Keep it in both, but filter the tooltip.
                row[pastKey] = val;
                row[futureKey] = val;
            }
        });
        return row;
    });

    const COLORS = [
        '#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#0088fe', '#00c49f', '#ffbb28', '#ff8042'
    ];

    return (
        <Box sx={{height: 360}}>
            <ResponsiveContainer width="100%" height="100%">
                <LineChart data={merged} margin={{top: 10, right: 20, bottom: 5, left: 0}}>
                    <CartesianGrid strokeDasharray="3 3"/>
                    <XAxis dataKey="date" tickFormatter={dateFormatter}/>
                    <YAxis tickFormatter={(v) => `${v}`}/>
                    <Tooltip
                        content={({active, payload, label}) => {
                            if (active && payload && payload.length) {
                                const filteredPayload = payload.filter((item) => {
                                    const dataKey = item.dataKey as string;
                                    if (dataKey.endsWith('__future')) {
                                        const pastKey = dataKey.replace('__future', '__past');
                                        // Check if an entry with pastKey already exists in the current payload
                                        return !payload.some(p => p.dataKey === pastKey);
                                    }
                                    return item.value !== null && item.value !== undefined;
                                });

                                if (filteredPayload.length === 0) return null;

                                return (
                                    <Paper sx={{p: 1.5, border: '1px solid', borderColor: 'divider', boxShadow: 3}}>
                                        <Typography variant="body2" sx={{mb: 1, fontWeight: 'bold'}}>
                                            {dateFormatter(String(label ?? ''))}
                                        </Typography>
                                        {filteredPayload.map((entry, index) => (
                                            <Box key={`item-${index}`}
                                                 sx={{display: 'flex', alignItems: 'center', mb: 0.5}}>
                                                <Box sx={{
                                                    width: 10,
                                                    height: 10,
                                                    bgcolor: entry.color,
                                                    mr: 1,
                                                    borderRadius: '50%'
                                                }}/>
                                                <Typography variant="body2" sx={{flexGrow: 1, mr: 2}}>
                                                    {entry.name}:
                                                </Typography>
                                                <Typography variant="body2" sx={{fontWeight: 'medium'}}>
                                                    {currencyFormatter(entry.value as number)}
                                                </Typography>
                                            </Box>
                                        ))}
                                    </Paper>
                                );
                            }
                            return null;
                        }}
                    />
                    {stats.map((s, index) => {
                        const pastKey = `${s.name}__past`;
                        const futureKey = `${s.name}__future`;
                        const color = COLORS[index % COLORS.length];
                        return (
                            <React.Fragment key={s.name}>
                                <Line
                                    type="monotone"
                                    dataKey={pastKey}
                                    name={s.name}
                                    stroke={color}
                                    dot={false}
                                    isAnimationActive={false}
                                    connectNulls
                                    strokeWidth={2}
                                />
                                <Line
                                    type="monotone"
                                    dataKey={futureKey}
                                    name={s.name}
                                    stroke={color}
                                    dot={false}
                                    isAnimationActive={false}
                                    connectNulls
                                    strokeWidth={2}
                                    strokeDasharray="4 4"
                                    legendType="none"
                                />
                            </React.Fragment>
                        );
                    })}
                </LineChart>
            </ResponsiveContainer>
        </Box>
    );
};

const CategorySpendChart: React.FC = () => {
    const {t} = useTranslation();
    const {data: me, isLoading: userLoading} = useReadUserMeApiV1UsersMeGet();
    const currentUserName = me?.name || t('statistics.budget_me');
    const totalLabel = t('statistics.total');

    const {data, isLoading: statsLoading} = useGetCategorySpendStatisticsApiV1StatisticCategoryGet();

    if (userLoading || statsLoading) return <LinearProgress/>;
    const stats = data ?? [];

    const rows = stats.map((c) => {
        const total = c.items.reduce((acc, it) => acc + Number(it.amount || 0), 0);
        const user = c.items.reduce((acc, it) => acc + Number(it.amount_user || 0), 0);
        return {name: c.name, diff: total - user, user, total_orig: total};
    });

    return (
        <Box sx={{height: 600}}>
            <ResponsiveContainer width="100%" height="100%">
                <BarChart data={rows} layout="vertical" margin={{top: 10, right: 30, bottom: 5, left: 40}}>
                    <defs>
                        <pattern id="diagonalHatch" patternUnits="userSpaceOnUse" width="6" height="6"
                                 patternTransform="rotate(45)">
                            <rect width="6" height="6" fill="#7ec0f7" fillOpacity={0.5}/>
                            <line x1="0" y1="0" x2="0" y2="6" stroke="#8884d8" strokeWidth="2"/>
                        </pattern>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3"/>
                    <XAxis type="number" tickFormatter={(v) => `${v}`}/>
                    <YAxis dataKey="name" type="category" width={100}/>
                    <Tooltip formatter={(v, n, props) => {
                        const isTotal = props?.dataKey === 'diff' || n === 'diff' || n === totalLabel;
                        if (isTotal) return [currencyFormatter((props?.payload as { total_orig?: number })?.total_orig ?? 0), totalLabel];
                        return [currencyFormatter(v as number), currentUserName];
                    }}/>
                    <Legend/>
                    <Bar dataKey="user" name={currentUserName} stackId="a" fill="url(#diagonalHatch)"/>
                    <Bar dataKey="diff" name={totalLabel} stackId="a" fill="#7ec0f7" fillOpacity={0.5}/>
                </BarChart>
            </ResponsiveContainer>
        </Box>
    );
};

const CashflowChart: React.FC = () => {
    const {t} = useTranslation();
    const {data, isLoading} = useGetCashflowStatisticsApiV1StatisticCashflowGet();

    if (isLoading) return <LinearProgress/>;
    const stats = data?.items ?? [];

    const rows = stats.map((c) => ({
        name: `${c.month}/${c.year}`,
        income: Number(c.income),
        expenses: Number(c.expenses),
        balance: Number(c.income) - Number(c.expenses)
    }));

    return (
        <Box sx={{height: 400}}>
            <ResponsiveContainer width="100%" height="100%">
                <BarChart data={rows} margin={{top: 10, right: 30, bottom: 5, left: 0}}>
                    <CartesianGrid strokeDasharray="3 3"/>
                    <XAxis dataKey="name"/>
                    <YAxis tickFormatter={(v) => `${v}€`}/>
                    <Tooltip formatter={(v) => currencyFormatter(v as number)}/>
                    <Legend/>
                    <Bar dataKey="income" name={t('statistics.cashflowIncome')} fill="#82ca9d"/>
                    <Bar dataKey="expenses" name={t('statistics.cashflowExpenses')} fill="#f44336"/>
                </BarChart>
            </ResponsiveContainer>
        </Box>
    );
};

const BudgetUsageChart: React.FC = () => {
    const {t} = useTranslation();
    const {data: me, isLoading: userLoading} = useReadUserMeApiV1UsersMeGet();

    const now = new Date();
    const [selectedBudget, setSelectedBudget] = React.useState<string>('all');
    const [desiredPercentage, setDesiredPercentage] = React.useState<number>(50);

    const {data, isLoading: statsLoading} = useGetBudgetUsageStatisticsApiV1StatisticBudgetGet({
        year: now.getFullYear(),
        month: now.getMonth() + 1
    });

    if (userLoading || statsLoading) return <LinearProgress/>;

    const currentUserName = me?.name ?? t('statistics.budget_me');
    const stats = data?.budgets ?? [];

    let userSpentTotal = 0;
    let totalSpentTotal = 0;

    if (selectedBudget === 'all') {
        stats.forEach(b => {
            userSpentTotal += Number(b.user_spent);
            totalSpentTotal += Number(b.total_spent);
        });
    } else {
        const b = stats.find(s => s.category_id === selectedBudget);
        if (b) {
            userSpentTotal = Number(b.user_spent);
            totalSpentTotal = Number(b.total_spent);
        }
    }

    const othersSpentTotal = Math.max(0, totalSpentTotal - userSpentTotal);
    const actualPercentage = totalSpentTotal > 0 ? (userSpentTotal / totalSpentTotal) * 100 : 0;

    const COLORS = ['#8884d8', '#82ca9d'];

    const chartData = [
        {name: currentUserName, value: userSpentTotal, fill: COLORS[0]},
        {name: t('statistics.budget_other'), value: othersSpentTotal, fill: COLORS[1]}
    ];

    const expectedUserSpent = totalSpentTotal * (desiredPercentage / 100);
    const difference = expectedUserSpent - userSpentTotal;

    return (
        <Box>
            <Grid container spacing={3} sx={{mb: 3}}>
                <Grid size={{xs: 12, md: 6}}>
                    <FormControl fullWidth>
                        <InputLabel>Budget</InputLabel>
                        <Select
                            value={selectedBudget}
                            label="Budget"
                            onChange={(e) => setSelectedBudget(e.target.value)}
                        >
                            <MenuItem value="all">{t('statistics.all_budgets')}</MenuItem>
                            {stats.map(b => (
                                <MenuItem key={b.category_id} value={b.category_id}>
                                    {b.category_name}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>
                </Grid>
                <Grid size={{xs: 12, md: 6}}>
                    <Typography gutterBottom>
                        {t('statistics.budget_wanted_share')}: {desiredPercentage}% ({t('statistics.budget_me')}) / {100 - desiredPercentage}% ({t('statistics.budget_other')})
                    </Typography>
                    <Slider
                        value={desiredPercentage}
                        onChange={(_, newValue) => setDesiredPercentage(newValue as number)}
                        valueLabelDisplay="auto"
                        min={0}
                        max={100}
                    />
                </Grid>
            </Grid>

            <Box sx={{display: 'flex', flexDirection: {xs: 'column', md: 'row'}, alignItems: 'center', gap: 4, minHeight: 300}}>
                <Box sx={{height: 300, width: {xs: '100%', md: '50%'}}}>
                    <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                            <Pie
                                data={chartData}
                                cx="50%"
                                cy="50%"
                                innerRadius={60}
                                outerRadius={80}
                                paddingAngle={5}
                                dataKey="value"
                                label={({name, percent}) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
                            />
                            <Tooltip formatter={(v) => currencyFormatter(v as number)}/>
                            <Legend/>
                        </PieChart>
                    </ResponsiveContainer>
                </Box>

                <Box sx={{flex: 1, textAlign: 'center'}}>
                    <Typography variant="h6">{t('statistics.budget_current_share')}</Typography>
                    <Typography variant="h4" color="primary" sx={{fontWeight: 'bold'}}>
                        {actualPercentage.toFixed(1)}%
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{mb: 2}}>
                        {t('statistics.budget_current_from')}{" "}{currencyFormatter(totalSpentTotal)}
                    </Typography>

                    <Typography variant="h6">{t('statistics.budget_current_diff')}</Typography>
                    <Typography variant="h4" color={Math.abs(difference) < 0.01 ? "text.primary" : (difference >= 0 ? "success.main" : "error.main")} sx={{fontWeight: 'bold'}}>
                        {difference > 0 ? '+' : ''}{currencyFormatter(difference)}
                    </Typography>
                </Box>
            </Box>
        </Box>
    );
};

const StatisticsPage: React.FC = () => {
    const {t} = useTranslation();

    const handleExportPdf = async () => {
        const now = new Date();
        const year = now.getFullYear();
        const month = now.getMonth() + 1;

        try {
            const response = await AXIOS_INSTANCE.get(`/api/v1/exports/monthly-report.pdf`, {
                params: { year, month },
                responseType: 'blob',
                headers: {
                    Authorization: `Bearer ${storage.getToken()}`
                }
            });

            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `report-${year}-${month.toString().padStart(2, '0')}.pdf`);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (error) {
            console.error('Export failed', error);
        }
    };

    return (
        <Container maxWidth="lg" sx={{py: 2}}>
            <Box sx={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4}}>
                <Typography variant="h4" sx={{fontWeight: 'bold', color: 'text.primary'}}>
                    {t('statistics.title')}
                </Typography>
                <Button
                    variant="outlined"
                    startIcon={<FileText size={18} />}
                    onClick={handleExportPdf}
                >
                    {t('statistics.export_pdf')}
                </Button>
            </Box>

            <Grid container spacing={3} sx={{mb: 4}}>
                <Grid size={{xs: 12, md: 12}}>
                    <Card variant="outlined">
                        <CardContent>
                            <Typography variant="h6" sx={{mb: 2}}>{t('statistics.budget_usage')}</Typography>
                            <BudgetUsageChart/>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid size={{xs: 12, md: 12}}>
                    <Card variant="outlined">
                        <CardContent>
                            <Typography variant="h6" sx={{mb: 2}}>{t('statistics.cashflow')}</Typography>
                            <CashflowChart/>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid size={{xs: 12, md: 12}}>
                    <Card variant="outlined">
                        <CardContent>
                            <Typography variant="h6" sx={{mb: 2}}>{t('statistics.account_balance')}</Typography>
                            <AccountBalanceChart/>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid size={{xs: 12, md: 12}}>
                    <Card variant="outlined">
                        <CardContent>
                            <Typography variant="h6" sx={{mb: 2}}>{t('statistics.category_spend')}</Typography>
                            <CategorySpendChart/>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>
        </Container>
    );
};

export default StatisticsPage;
