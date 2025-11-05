import React from 'react';
import { useDashboard } from '../../context/DashboardContext';
import { Activity, AlertTriangle, CheckCircle } from 'lucide-react';

const HealthScore = () => {
  const { metrics } = useDashboard();
  const { health } = metrics;

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-400';
    if (score >= 60) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getScoreGradient = (score) => {
    if (score >= 80) return 'from-green-500 to-green-600';
    if (score >= 60) return 'from-yellow-500 to-yellow-600';
    return 'from-red-500 to-red-600';
  };

  const getStatusText = (score) => {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    if (score >= 40) return 'Fair';
    return 'Poor';
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Health Score</h3>
        <Activity className="w-5 h-5 text-gray-400" />
      </div>

      {/* Score Display */}
      <div className="text-center mb-6">
        <div className="relative w-24 h-24 mx-auto mb-3">
          <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 100 100">
            <circle
              cx="50"
              cy="50"
              r="40"
              stroke="currentColor"
              strokeWidth="8"
              fill="none"
              className="text-gray-700"
            />
            <circle
              cx="50"
              cy="50"
              r="40"
              stroke="url(#healthGradient)"
              strokeWidth="8"
              fill="none"
              strokeLinecap="round"
              strokeDasharray={`${2.51 * health.score} 251.2`}
              className="transition-all duration-1000 ease-out"
            />
            <defs>
              <linearGradient id="healthGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop
                  offset="0%"
                  className={`${health.score >= 80 ? 'stop-green-500' : 
                              health.score >= 60 ? 'stop-yellow-500' : 'stop-red-500'}`}
                />
                <stop
                  offset="100%"
                  className={`${health.score >= 80 ? 'stop-green-600' : 
                              health.score >= 60 ? 'stop-yellow-600' : 'stop-red-600'}`}
                />
              </linearGradient>
            </defs>
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className={`text-2xl font-bold ${getScoreColor(health.score)}`}>
              {health.score}
            </span>
          </div>
        </div>
        <div className={`text-lg font-semibold ${getScoreColor(health.score)}`}>
          {getStatusText(health.score)}
        </div>
      </div>

      {/* Issues Summary */}
      <div className="space-y-2">
        {health.issues && health.issues.length > 0 ? (
          <>
            <div className="flex items-center space-x-2 text-sm">
              <AlertTriangle className="w-4 h-4 text-red-400" />
              <span className="text-gray-300">
                {health.issues.length} active issue{health.issues.length !== 1 ? 's' : ''}
              </span>
            </div>
            <div className="max-h-20 overflow-y-auto space-y-1">
              {health.issues.slice(0, 3).map((issue, index) => (
                <div key={index} className="text-xs text-gray-400 bg-gray-700 rounded p-2">
                  {issue.message || issue}
                </div>
              ))}
            </div>
          </>
        ) : (
          <div className="flex items-center space-x-2 text-sm">
            <CheckCircle className="w-4 h-4 text-green-400" />
            <span className="text-gray-300">All systems operational</span>
          </div>
        )}
      </div>

      {/* Last Update */}
      {health.lastUpdate && (
        <div className="mt-4 pt-3 border-t border-gray-700">
          <div className="text-xs text-gray-400 text-center">
            Last updated: {new Date(health.lastUpdate).toLocaleTimeString()}
          </div>
        </div>
      )}
    </div>
  );
};

export default HealthScore;