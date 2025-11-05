// Dashboard Components Index
export { default as Header } from './Header';
export { default as Sidebar } from './Sidebar';

// Widget Components
export { default as SystemMetrics } from './widgets/SystemMetrics';
export { default as AutomationStatus } from './widgets/AutomationStatus';
export { default as GithubMetrics } from './widgets/GithubMetrics';
export { default as HealthScore } from './widgets/HealthScore';
export { default as RecentActivity } from './widgets/RecentActivity';
export { default as AlertSummary } from './widgets/AlertSummary';
export { default as QuickActions } from './widgets/QuickActions';

// Page Components
export { default as Dashboard } from '../pages/Dashboard';
export { default as Metrics } from '../pages/Metrics';
export { default as Alerts } from '../pages/Alerts';
export { default as Notifications } from '../pages/Notifications';
export { default as Settings } from '../pages/Settings';

// Context
export { DashboardProvider, useDashboard } from '../context/DashboardContext';