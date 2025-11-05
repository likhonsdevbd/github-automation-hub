import React from 'react';
import { useDashboard } from '../../context/DashboardContext';
import { Github, GitBranch, Star, TrendingUp } from 'lucide-react';

const GithubMetrics = () => {
  const { metrics } = useDashboard();
  const { github } = metrics;

  const getUsagePercentage = (used, limit) => {
    return Math.round((used / limit) * 100);
  };

  const getUsageColor = (percentage) => {
    if (percentage < 70) return 'bg-green-500';
    if (percentage < 90) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">GitHub API</h3>
        <Github className="w-5 h-5 text-gray-400" />
      </div>

      <div className="space-y-4">
        {/* Rate Requests */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center space-x-1">
              <TrendingUp className="w-4 h-4 text-blue-400" />
              <span className="text-sm text-gray-300">Rate Requests</span>
            </div>
            <span className="text-sm text-white font-mono">
              {github.requests}/hr
            </span>
          </div>
        </div>

        {/* Core API Usage */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-1">
              <GitBranch className="w-4 h-4 text-green-400" />
              <span className="text-sm text-gray-300">Core API</span>
            </div>
            <span className="text-sm text-white font-mono">
              {github.limits.core.used}/{github.limits.core.limit}
            </span>
          </div>
          <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
            <div
              className={`h-full ${getUsageColor(getUsagePercentage(github.limits.core.used, github.limits.core.limit))} transition-all duration-300`}
              style={{ 
                width: `${getUsagePercentage(github.limits.core.used, github.limits.core.limit)}%` 
              }}
            />
          </div>
          <div className="mt-1 text-xs text-gray-400">
            {getUsagePercentage(github.limits.core.used, github.limits.core.limit)}% used
          </div>
        </div>

        {/* Search API Usage */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-1">
              <Star className="w-4 h-4 text-purple-400" />
              <span className="text-sm text-gray-300">Search API</span>
            </div>
            <span className="text-sm text-white font-mono">
              {github.limits.search.used}/{github.limits.search.limit}
            </span>
          </div>
          <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
            <div
              className={`h-full ${getUsageColor(getUsagePercentage(github.limits.search.used, github.limits.search.limit))} transition-all duration-300`}
              style={{ 
                width: `${getUsagePercentage(github.limits.search.used, github.limits.search.limit)}%` 
              }}
            />
          </div>
          <div className="mt-1 text-xs text-gray-400">
            {getUsagePercentage(github.limits.search.used, github.limits.search.limit)}% used
          </div>
        </div>

        {/* Status Summary */}
        <div className="pt-3 border-t border-gray-700">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-300">Status</span>
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${
                Math.max(
                  getUsagePercentage(github.limits.core.used, github.limits.core.limit),
                  getUsagePercentage(github.limits.search.used, github.limits.search.limit)
                ) < 90 ? 'bg-green-500' : 'bg-red-500'
              } rounded-full animate-pulse`}></div>
              <span className="text-sm text-white">
                {Math.max(
                  getUsagePercentage(github.limits.core.used, github.limits.core.limit),
                  getUsagePercentage(github.limits.search.used, github.limits.search.limit)
                ) < 90 ? 'Healthy' : 'Near Limit'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GithubMetrics;