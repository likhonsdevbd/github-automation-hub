import React from 'react';
import { useDashboard } from '../../context/DashboardContext';
import { AlertTriangle, X, Clock, TrendingUp, CheckCircle } from 'lucide-react';
import toast from 'react-hot-toast';

const AlertSummary = () => {
  const { alerts, dismissAlert } = useDashboard();

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical': return 'bg-red-500';
      case 'warning': return 'bg-yellow-500';
      case 'info': return 'bg-blue-500';
      default: return 'bg-gray-500';
    }
  };

  const getSeverityTextColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical': return 'text-red-400';
      case 'warning': return 'text-yellow-400';
      case 'info': return 'text-blue-400';
      default: return 'text-gray-400';
    }
  };

  const formatTimeAgo = (timestamp) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffInMinutes = Math.floor((now - time) / 60000);
    
    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) return `${diffInHours}h ago`;
    const diffInDays = Math.floor(diffInHours / 24);
    return `${diffInDays}d ago`;
  };

  const handleDismiss = async (alertId) => {
    try {
      await dismissAlert(alertId);
      toast.success('Alert dismissed');
    } catch (error) {
      toast.error('Failed to dismiss alert');
    }
  };

  const getUnreadCount = () => {
    return alerts.filter(alert => !alert.read).length;
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <AlertTriangle className="w-5 h-5 text-yellow-400" />
          <h3 className="text-lg font-semibold text-white">Alerts</h3>
          {getUnreadCount() > 0 && (
            <span className="bg-red-500 text-white text-xs px-2 py-1 rounded-full">
              {getUnreadCount()}
            </span>
          )}
        </div>
        <div className="flex items-center space-x-1 text-sm text-gray-400">
          <TrendingUp className="w-4 h-4" />
          <span>Last 24h</span>
        </div>
      </div>

      {alerts.length === 0 ? (
        <div className="text-center py-8">
          <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
          <p className="text-gray-400">No active alerts</p>
          <p className="text-sm text-gray-500">All systems running smoothly</p>
        </div>
      ) : (
        <div className="space-y-3 max-h-80 overflow-y-auto">
          {alerts.slice(0, 5).map((alert) => (
            <div
              key={alert.id}
              className={`p-3 rounded-lg border-l-4 ${
                alert.severity?.toLowerCase() === 'critical'
                  ? 'border-red-500 bg-red-900/20'
                  : alert.severity?.toLowerCase() === 'warning'
                  ? 'border-yellow-500 bg-yellow-900/20'
                  : 'border-blue-500 bg-blue-900/20'
              } ${!alert.read ? 'border-l-8' : ''}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-1">
                    <div className={`w-2 h-2 rounded-full ${getSeverityColor(alert.severity)}`} />
                    <span className={`text-sm font-medium ${getSeverityTextColor(alert.severity)}`}>
                      {alert.severity?.toUpperCase() || 'INFO'}
                    </span>
                    <div className="flex items-center space-x-1 text-xs text-gray-400">
                      <Clock className="w-3 h-3" />
                      <span>{formatTimeAgo(alert.timestamp)}</span>
                    </div>
                  </div>
                  <p className="text-sm text-gray-200 mb-1 line-clamp-2">
                    {alert.message}
                  </p>
                  {alert.source && (
                    <p className="text-xs text-gray-400">
                      Source: {alert.source}
                    </p>
                  )}
                </div>
                <button
                  onClick={() => handleDismiss(alert.id)}
                  className="ml-2 p-1 text-gray-400 hover:text-white transition-colors"
                  title="Dismiss alert"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {alerts.length > 5 && (
        <div className="mt-4 text-center">
          <button className="text-blue-400 hover:text-blue-300 text-sm">
            View all {alerts.length} alerts →
          </button>
        </div>
      )}
    </div>
  );
};

export default AlertSummary;