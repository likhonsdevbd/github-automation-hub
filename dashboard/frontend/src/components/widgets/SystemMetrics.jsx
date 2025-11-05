import React from 'react';
import { useDashboard } from '../../context/DashboardContext';
import { Cpu, MemoryStick, HardDrive, Wifi, Clock } from 'lucide-react';

const SystemMetrics = () => {
  const { metrics } = useDashboard();
  const { system } = metrics;

  const getUsageColor = (value) => {
    if (value < 60) return 'bg-green-500';
    if (value < 80) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const formatUptime = (seconds) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${days}d ${hours}h ${minutes}m`;
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">System Metrics</h3>
        <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
      </div>

      <div className="space-y-4">
        {/* CPU Usage */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Cpu className="w-4 h-4 text-blue-400" />
            <span className="text-sm text-gray-300">CPU</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-20 h-2 bg-gray-700 rounded-full overflow-hidden">
              <div
                className={`h-full ${getUsageColor(system.cpu)} transition-all duration-300`}
                style={{ width: `${system.cpu}%` }}
              />
            </div>
            <span className="text-sm text-white font-mono">{system.cpu}%</span>
          </div>
        </div>

        {/* Memory Usage */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <MemoryStick className="w-4 h-4 text-purple-400" />
            <span className="text-sm text-gray-300">Memory</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-20 h-2 bg-gray-700 rounded-full overflow-hidden">
              <div
                className={`h-full ${getUsageColor(system.memory)} transition-all duration-300`}
                style={{ width: `${system.memory}%` }}
              />
            </div>
            <span className="text-sm text-white font-mono">{system.memory}%</span>
          </div>
        </div>

        {/* Disk Usage */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <HardDrive className="w-4 h-4 text-orange-400" />
            <span className="text-sm text-gray-300">Disk</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-20 h-2 bg-gray-700 rounded-full overflow-hidden">
              <div
                className={`h-full ${getUsageColor(system.disk)} transition-all duration-300`}
                style={{ width: `${system.disk}%` }}
              />
            </div>
            <span className="text-sm text-white font-mono">{system.disk}%</span>
          </div>
        </div>

        {/* Network Usage */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Wifi className="w-4 h-4 text-green-400" />
            <span className="text-sm text-gray-300">Network</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-20 h-2 bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-500 transition-all duration-300"
                style={{ width: `${system.network}%` }}
              />
            </div>
            <span className="text-sm text-white font-mono">{system.network} MB/s</span>
          </div>
        </div>

        {/* Uptime */}
        <div className="flex items-center justify-between pt-2 border-t border-gray-700">
          <div className="flex items-center space-x-2">
            <Clock className="w-4 h-4 text-yellow-400" />
            <span className="text-sm text-gray-300">Uptime</span>
          </div>
          <span className="text-sm text-white font-mono">
            {formatUptime(system.uptime)}
          </span>
        </div>
      </div>
    </div>
  );
};

export default SystemMetrics;