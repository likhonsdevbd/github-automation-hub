import React, { useState } from 'react';
import { useDashboard } from '../../context/DashboardContext';
import { 
  Play, 
  Pause, 
  Settings, 
  RefreshCw, 
  Bell, 
  Download, 
  Upload,
  GitBranch,
  Shield,
  Zap
} from 'lucide-react';
import toast from 'react-hot-toast';

const QuickActions = () => {
  const { updateSettings } = useDashboard();
  const [isLoading, setIsLoading] = useState(null);

  const actions = [
    {
      id: 'pause-automation',
      label: 'Pause Automation',
      icon: Pause,
      color: 'bg-yellow-600 hover:bg-yellow-700',
      action: async () => {
        setIsLoading('pause-automation');
        try {
          // Simulate API call
          await new Promise(resolve => setTimeout(resolve, 1000));
          toast.success('Automation paused');
        } catch (error) {
          toast.error('Failed to pause automation');
        } finally {
          setIsLoading(null);
        }
      }
    },
    {
      id: 'resume-automation',
      label: 'Resume Automation',
      icon: Play,
      color: 'bg-green-600 hover:bg-green-700',
      action: async () => {
        setIsLoading('resume-automation');
        try {
          await new Promise(resolve => setTimeout(resolve, 1000));
          toast.success('Automation resumed');
        } catch (error) {
          toast.error('Failed to resume automation');
        } finally {
          setIsLoading(null);
        }
      }
    },
    {
      id: 'test-connection',
      label: 'Test Connection',
      icon: Zap,
      color: 'bg-blue-600 hover:bg-blue-700',
      action: async () => {
        setIsLoading('test-connection');
        try {
          await new Promise(resolve => setTimeout(resolve, 2000));
          toast.success('All connections healthy');
        } catch (error) {
          toast.error('Connection test failed');
        } finally {
          setIsLoading(null);
        }
      }
    },
    {
      id: 'export-logs',
      label: 'Export Logs',
      icon: Download,
      color: 'bg-purple-600 hover:bg-purple-700',
      action: async () => {
        setIsLoading('export-logs');
        try {
          await new Promise(resolve => setTimeout(resolve, 1500));
          toast.success('Logs exported successfully');
        } catch (error) {
          toast.error('Failed to export logs');
        } finally {
          setIsLoading(null);
        }
      }
    },
    {
      id: 'refresh-settings',
      label: 'Refresh Settings',
      icon: RefreshCw,
      color: 'bg-gray-600 hover:bg-gray-700',
      action: async () => {
        setIsLoading('refresh-settings');
        try {
          await new Promise(resolve => setTimeout(resolve, 800));
          toast.success('Settings refreshed');
        } catch (error) {
          toast.error('Failed to refresh settings');
        } finally {
          setIsLoading(null);
        }
      }
    },
    {
      id: 'test-notifications',
      label: 'Test Notifications',
      icon: Bell,
      color: 'bg-orange-600 hover:bg-orange-700',
      action: async () => {
        setIsLoading('test-notifications');
        try {
          await new Promise(resolve => setTimeout(resolve, 1200));
          toast.success('Test notification sent');
        } catch (error) {
          toast.error('Failed to send test notification');
        } finally {
          setIsLoading(null);
        }
      }
    }
  ];

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Quick Actions</h3>
        <Settings className="w-5 h-5 text-gray-400" />
      </div>

      <div className="space-y-3">
        {actions.map((action) => {
          const Icon = action.icon;
          const loading = isLoading === action.id;
          
          return (
            <button
              key={action.id}
              onClick={action.action}
              disabled={loading}
              className={`w-full flex items-center space-x-3 p-3 rounded-lg text-white transition-all duration-200 ${action.color} ${
                loading ? 'opacity-75 cursor-not-allowed' : 'hover:transform hover:scale-105'
              }`}
            >
              {loading ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Icon className="w-4 h-4" />
              )}
              <span className="text-sm font-medium">{action.label}</span>
            </button>
          );
        })}
      </div>

      {/* System Actions */}
      <div className="mt-6 pt-4 border-t border-gray-700">
        <h4 className="text-sm font-medium text-gray-300 mb-3">System Actions</h4>
        <div className="grid grid-cols-2 gap-2">
          <button className="flex items-center justify-center space-x-2 p-2 bg-gray-700 hover:bg-gray-600 rounded text-sm text-gray-300 transition-colors">
            <GitBranch className="w-4 h-4" />
            <span>Git Sync</span>
          </button>
          <button className="flex items-center justify-center space-x-2 p-2 bg-gray-700 hover:bg-gray-600 rounded text-sm text-gray-300 transition-colors">
            <Shield className="w-4 h-4" />
            <span>Security</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default QuickActions;