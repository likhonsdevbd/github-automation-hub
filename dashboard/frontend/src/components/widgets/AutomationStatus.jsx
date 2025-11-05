import React from 'react';
import { useDashboard } from '../../context/DashboardContext';
import { Play, Pause, CheckCircle, XCircle, TrendingUp } from 'lucide-react';

const AutomationStatus = () => {
  const { metrics } = useDashboard();
  const { automation } = metrics;

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'text-green-400';
      case 'queued': return 'text-yellow-400';
      case 'completed': return 'text-blue-400';
      case 'failed': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active': return <Play className="w-4 h-4" />;
      case 'queued': return <Pause className="w-4 h-4" />;
      case 'completed': return <CheckCircle className="w-4 h-4" />;
      case 'failed': return <XCircle className="w-4 h-4" />;
      default: return <TrendingUp className="w-4 h-4" />;
    }
  };

  const getSuccessRate = () => {
    const total = automation.completed + automation.failed;
    return total > 0 ? ((automation.completed / total) * 100).toFixed(1) : 0;
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Automation Status</h3>
        <div className="flex items-center space-x-1">
          <TrendingUp className="w-4 h-4 text-green-400" />
          <span className="text-sm text-green-400">{automation.rate}/hr</span>
        </div>
      </div>

      <div className="space-y-3">
        {/* Active */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className={`${getStatusColor('active')}`}>
              {getStatusIcon('active')}
            </div>
            <span className="text-sm text-gray-300">Active</span>
          </div>
          <div className="text-right">
            <div className="text-lg font-semibold text-white">
              {automation.active}
            </div>
          </div>
        </div>

        {/* Queued */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className={`${getStatusColor('queued')}`}>
              {getStatusIcon('queued')}
            </div>
            <span className="text-sm text-gray-300">Queued</span>
          </div>
          <div className="text-right">
            <div className="text-lg font-semibold text-white">
              {automation.queued}
            </div>
          </div>
        </div>

        {/* Completed */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className={`${getStatusColor('completed')}`}>
              {getStatusIcon('completed')}
            </div>
            <span className="text-sm text-gray-300">Completed</span>
          </div>
          <div className="text-right">
            <div className="text-lg font-semibold text-white">
              {automation.completed}
            </div>
          </div>
        </div>

        {/* Failed */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className={`${getStatusColor('failed')}`}>
              {getStatusIcon('failed')}
            </div>
            <span className="text-sm text-gray-300">Failed</span>
          </div>
          <div className="text-right">
            <div className="text-lg font-semibold text-white">
              {automation.failed}
            </div>
          </div>
        </div>
      </div>

      {/* Success Rate */}
      <div className="mt-4 pt-3 border-t border-gray-700">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-300">Success Rate</span>
          <span className="text-lg font-semibold text-green-400">
            {getSuccessRate()}%
          </span>
        </div>
        <div className="mt-2 w-full h-2 bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-green-500 transition-all duration-500"
            style={{ width: `${getSuccessRate()}%` }}
          />
        </div>
      </div>
    </div>
  );
};

export default AutomationStatus;