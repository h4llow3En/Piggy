import {useTranslation} from 'react-i18next';

export const useGreeting = () => {
    const {t} = useTranslation();
    const hour = new Date().getHours();

    if (hour >= 5 && hour < 12) {
        return t('dashboard.greetings.morning');
    } else if (hour >= 12 && hour < 18) {
        return t('dashboard.greetings.afternoon');
    } else if (hour >= 18 && hour < 22) {
        return t('dashboard.greetings.evening');
    } else {
        return t('dashboard.greetings.hello');
    }
};
