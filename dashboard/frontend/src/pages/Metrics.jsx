import React, { useState, useEffect } from 'react';
import { useDashboard } from '../context/DashboardContext';
import { Line, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
} from 'chart.js';
import { TrendingUp, Activity, Cpu, Memory, HardDrive } from 'lucide-react';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

const Metrics = () => {
  const { metrics } = useDashboard();
  const [timeRange, setTimeRange] = useState('1h');

  // Mock historical data
  const generateHistoricalData = (hours) => {
    const data = [];
    const now = new Date();
    for (let i = hours; i >= 0; i--) {
      const time = new Date(now - i * 60 * 60 * 1000);
      data.push({
        time: time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
        cpu: Math.random() * 40 + 30,
        memory: Math.random() * 30 + 50,
        disk: Math.random() * 20 + 60,
        network: Math.random() * 100 + 50,
        automation: Math.floor(Math.random() * 20 + 10)
      });
    }
    return data;
  };

  const historicalData = generateHistoricalData(timeRange === '1h' ? 1 : timeRange === '24h' ? 24 : 168);

  const systemChartData = {
    labels: historicalData.map(d => d.time),
    datasets: [
      {
        label: 'CPU %',
        data: historicalData.map(d => d.cpu),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4
      },
      {
        label: 'Memory %',
        data: historicalData.map(d => d.memory),
        borderColor: 'rgb(147, 51, 234)',
        backgroundColor: 'rgba(147, 51, 234, 0.1)',
        tension: 0.4
      },
      {
        label: 'Disk %',
        data: historicalData.map(d => d.disk),
        borderColor: 'rgb(249, 115, 22)',
        backgroundColor: 'rgba(249, 115, 22, 0.1)',
        tension: 0.4
      }
    ]
  };

  const automationChartData = {
    labels: historicalData.map(d => d.time),
    datasets: [
      {
        label: 'Automations per Hour',
        data: historicalData.map(d => d.automation),
        backgroundColor: 'rgba(34, 197, 94, 0.8)',
        borderColor: 'rgb(34, 197, 94)',
        borderWidth: 1
      }
    ]
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: '#d1d5db'
        }
      }
    },
    scales: {
      x: {
        ticks: {
          color: '#9ca3af'
        },
        grid: {
          color: '#374151'
        }
      },
      y: {
        ticks: {
          color: '#9ca3af'
        },
        grid: {
          color: '#374151'
        }
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Metrics</h1>
          <p className="text-gray-400 mt-1">System performance and automation metrics</p>
        </div>
        <div className="flex space-x-2">
          {['1h', '24h', '7d'].map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-4 py-2 rounded-lg transition-colors ${
                timeRange === range
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {range}
            </button>
          ))}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Avg CPU Usage</p>
              <p className="text-2xl font-bold text-white">
                {Math.round(historicalData.reduce((sum, d) => sum + d.cpu, 0) / historicalData.length)}%
              </p>
            </div>
            <Cpu className="w-8 h-8 text-blue-400" />
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Avg Memory Usage</p>
              <p className="text-2xl font-bold text-white">
                {Math.round(historicalData.reduce((sum, d) => sum + d.memory, 0) / historicalData.length)}%
              </p>
            </div>
            <Memory className="w-8 h-8 text-purple-400" />
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Avg Disk Usage</p>
              <p className="text-2xl font-bold text-white">
                {Math.round(historicalData.reduce((sum, d) => sum + d.disk, 0) / historicalData.length)}%
              </p>
            </div>
            <HardDrive className="w-8 h-8 text-orange-400" />
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Automations/Hour</p>
              <p className="text-2xl font-bold text-white">
                {Math.round(historicalData.reduce((sum, d) => sum + d.automation, 0) / historicalData.length)}
              </p>
            </div>
            <Activity className="w-8 h-8 text-green-400" />
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">System Performance</h3>
          <div className="h-64">
            <Line data={systemChartData} options={chartOptions} />
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Automation Rate</h3>
          <div className="h-64">
            <Bar data={automationChartData} options={chartOptions} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Metrics;