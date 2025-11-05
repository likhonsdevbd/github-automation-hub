import React, { useState, useEffect } from 'react';
import { useDashboard } from '../context/DashboardContext';
import SystemMetrics from '../components/widgets/SystemMetrics';
import AutomationStatus from '../components/widgets/AutomationStatus';
import GithubMetrics from '../components/widgets/GithubMetrics';
import HealthScore from '../components/widgets/HealthScore';
import RecentActivity from '../components/widgets/RecentActivity';
import AlertSummary from '../components/widgets/AlertSummary';
import QuickActions from '../components/widgets/QuickActions';
import { RefreshCw, Settings, Plus } from 'lucide-react';
import toast from 'react-hot-toast';

const Dashboard = () => {
  const { metrics, loading, fetchMetrics } = useDashboard();
  const [lastUpdate, setLastUpdate] = useState(new Date());

  const handleRefresh = async () => {
    const loadingToast = toast.loading('Refreshing dashboard...');
    await fetchMetrics();
    setLastUpdate(new Date());
    toast.dismiss(loadingToast);
    toast.success('Dashboard refreshed');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Dashboard</h1>
          <p className="text-gray-400 mt-1">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => {/* Open settings modal */}}
            className="p-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
          >
            <Settings className="w-5 h-5" />
          </button>
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Key Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <SystemMetrics />
        <AutomationStatus />
        <GithubMetrics />
        <HealthScore />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Activity */}
        <div className="lg:col-span-2 space-y-6">
          <RecentActivity />
          
          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">System Performance</h3>
              <div className="h-64">
                {/* Performance chart will go here */}
                <div className="flex items-center justify-center h-full text-gray-400">
                  Performance Chart
                </div>
              </div>
            </div>
            
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">Automation Trends</h3>
              <div className="h-64">
                {/* Trends chart will go here */}
                <div className="flex items-center justify-center h-full text-gray-400">
                  Trends Chart
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column - Alerts & Actions */}
        <div className="space-y-6">
          <AlertSummary />
          <QuickActions />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;