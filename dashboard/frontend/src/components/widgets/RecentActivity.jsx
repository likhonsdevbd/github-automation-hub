import React, { useState, useEffect } from 'react';
import { useDashboard } from '../../context/DashboardContext';
import { Activity, Clock, User, GitCommit, AlertCircle } from 'lucide-react';

const RecentActivity = () => {
  const { metrics } = useDashboard();
  const [activities, setActivities] = useState([]);

  useEffect(() => {
    // Mock activity data - in real app this would come from API
    const mockActivities = [
      {
        id: 1,
        type: 'automation',
        title: 'Daily health check completed',
        description: 'System health monitoring completed successfully',
        timestamp: new Date(Date.now() - 5 * 60000).toISOString(),
        status: 'success',
        user: 'System'
      },
      {
        id: 2,
        type: 'github',
        title: 'Repository scan completed',
        description: 'Analyzed 15 repositories for updates',
        timestamp: new Date(Date.now() - 15 * 60000).toISOString(),
        status: 'success',
        user: 'Automation Bot'
      },
      {
        id: 3,
        type: 'alert',
        title: 'High CPU usage detected',
        description: 'CPU usage exceeded 85% threshold',
        timestamp: new Date(Date.now() - 30 * 60000).toISOString(),
        status: 'warning',
        user: 'Monitoring System'
      },
      {
        id: 4,
        type: 'user',
        title: 'Settings updated',
        description: 'Dashboard refresh interval changed to 5s',
        timestamp: new Date(Date.now() - 45 * 60000).toISOString(),
        status: 'info',
        user: 'Admin User'
      },
      {
        id: 5,
        type: 'automation',
        title: 'Daily contribution tracker started',
        description: 'Automated contribution tracking initiated',
        timestamp: new Date(Date.now() - 60 * 60000).toISOString(),
        status: 'success',
        user: 'System'
      }
    ];

    setActivities(mockActivities);
  }, []);

  const getActivityIcon = (type) => {
    switch (type) {
      case 'automation': return <Activity className="w-4 h-4 text-blue-400" />;
      case 'github': return <GitCommit className="w-4 h-4 text-green-400" />;
      case 'alert': return <AlertCircle className="w-4 h-4 text-red-400" />;
      case 'user': return <User className="w-4 h-4 text-purple-400" />;
      default: return <Activity className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'success': return 'text-green-400';
      case 'warning': return 'text-yellow-400';
      case 'error': return 'text-red-400';
      default: return 'text-blue-400';
    }
  };

  const formatTimeAgo = (timestamp) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffInMinutes = Math.floor((now - time) / 60000);
    
    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    const diffInHours = Math.floor(diffInMinutes / 60);
    return `${diffInHours}h ago`;
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Recent Activity</h3>
        <div className="flex items-center space-x-2 text-sm text-gray-400">
          <Clock className="w-4 h-4" />
          <span>Last 1 hour</span>
        </div>
      </div>

      <div className="space-y-3 max-h-96 overflow-y-auto">
        {activities.map((activity) => (
          <div key={activity.id} className="flex items-start space-x-3 p-3 bg-gray-700/50 rounded-lg">
            <div className="flex-shrink-0 mt-0.5">
              {getActivityIcon(activity.type)}
            </div>
            
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between mb-1">
                <h4 className="text-sm font-medium text-white truncate">
                  {activity.title}
                </h4>
                <span className={`text-xs ${getStatusColor(activity.status)}`}>
                  {activity.status.toUpperCase()}
                </span>
              </div>
              
              <p className="text-sm text-gray-300 mb-2">
                {activity.description}
              </p>
              
              <div className="flex items-center justify-between text-xs text-gray-400">
                <div className="flex items-center space-x-1">
                  <User className="w-3 h-3" />
                  <span>{activity.user}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Clock className="w-3 h-3" />
                  <span>{formatTimeAgo(activity.timestamp)}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {activities.length === 0 && (
        <div className="text-center py-8">
          <Activity className="w-12 h-12 text-gray-500 mx-auto mb-3" />
          <p className="text-gray-400">No recent activity</p>
        </div>
      )}

      <div className="mt-4 pt-4 border-t border-gray-700">
        <button className="w-full text-center text-blue-400 hover:text-blue-300 text-sm">
          View all activity →
        </button>
      </div>
    </div>
  );
};

export default RecentActivity;