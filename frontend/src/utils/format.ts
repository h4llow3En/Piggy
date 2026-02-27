import i18n from '../i18n';
import {format as dateFnsFormat, isSameYear, isToday, isTomorrow, isYesterday, parseISO} from 'date-fns';
import {de, enUS} from 'date-fns/locale';

export const formatCurrency = (amount: number | string) => {
    const value = typeof amount === 'string' ? parseFloat(amount) : amount;
    const locale = i18n.language.startsWith('de') ? 'de-DE' : 'en-US';
    return new Intl.NumberFormat(locale, {
        style: 'currency',
        currency: 'EUR'
    }).format(value || 0);
};

export const formatDate = (dateStr: string, t: (key: string) => string) => {
    const date = parseISO(dateStr);
    const locale = i18n.language.startsWith('de') ? de : enUS;

    if (isToday(date)) {
        return t('dashboard.transactions.today');
    }
    if (isYesterday(date)) {
        return t('dashboard.transactions.yesterday');
    }
    if (isTomorrow(date)) {
        return t('dashboard.transactions.tomorrow');
    }
    if (!isSameYear(date, new Date())) {
        return dateFnsFormat(date, 'dd.MM.yyyy', {locale});
    }
    return dateFnsFormat(date, i18n.language.startsWith('de') ? 'dd.MM.' : 'MM/dd', {locale});
};
