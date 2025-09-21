import { useSelector } from 'react-redux';
import { RootState } from '../store/store';

export const useNotifications = () => {
  const { notifications, unreadCount } = useSelector(
    (state: RootState) => state.notifications
  );

  return {
    notifications,
    unreadCount,
  };
};