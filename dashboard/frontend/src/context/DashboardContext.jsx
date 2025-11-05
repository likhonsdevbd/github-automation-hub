import React, { createContext, useContext, useReducer, useEffect } from 'react';
import axios from 'axios';

const DashboardContext = createContext();

const initialState = {
  metrics: {
    system: {
      cpu: 0,
      memory: 0,
      disk: 0,
      network: 0,
      uptime: 0
    },
    automation: {
      active: 0,
      queued: 0,
      completed: 0,
      failed: 0,
      rate: 0
    },
    github: {
      requests: 0,
      limits: {
        core: { used: 0, limit: 5000 },
        search: { used: 0, limit: 30 }
      }
    },
    health: {
      score: 0,
      issues: [],
      lastUpdate: null
    }
  },
  alerts: [],
  notifications: [],
  settings: {
    refreshInterval: 5000,
    enableSound: true,
    enablePush: true,
    theme: 'dark'
  },
  loading: false,
  error: null
};

const dashboardReducer = (state, action) => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    
    case 'SET_ERROR':
      return { ...state, error: action.payload, loading: false };
    
    case 'UPDATE_METRICS':
      return { 
        ...state, 
        metrics: { ...state.metrics, ...action.payload },
        error: null
      };
    
    case 'ADD_ALERT':
      return { 
        ...state, 
        alerts: [action.payload, ...state.alerts]
      };
    
    case 'UPDATE_ALERT':
      return {
        ...state,
        alerts: state.alerts.map(alert => 
          alert.id === action.payload.id ? { ...alert, ...action.payload } : alert
        )
      };
    
    case 'DISMISS_ALERT':
      return {
        ...state,
        alerts: state.alerts.filter(alert => alert.id !== action.payload)
      };
    
    case 'ADD_NOTIFICATION':
      return {
        ...state,
        notifications: [action.payload, ...state.notifications]
      };
    
    case 'MARK_NOTIFICATION_READ':
      return {
        ...state,
        notifications: state.notifications.map(notification =>
          notification.id === action.payload 
            ? { ...notification, read: true }
            : notification
        )
      };
    
    case 'CLEAR_NOTIFICATIONS':
      return {
        ...state,
        notifications: []
      };
    
    case 'UPDATE_SETTINGS':
      return {
        ...state,
        settings: { ...state.settings, ...action.payload }
      };
    
    default:
      return state;
  }
};

export const DashboardProvider = ({ children, socket }) => {
  const [state, dispatch] = useReducer(dashboardReducer, initialState);

  // Fetch initial data
  useEffect(() => {
    fetchMetrics();
    fetchAlerts();
    fetchNotifications();
  }, []);

  // Set up WebSocket listeners
  useEffect(() => {
    if (!socket) return;

    socket.on('metrics_update', (data) => {
      dispatch({ type: 'UPDATE_METRICS', payload: data });
    });

    socket.on('new_alert', (alert) => {
      dispatch({ type: 'ADD_ALERT', payload: alert });
      dispatch({ type: 'ADD_NOTIFICATION', payload: {
        id: Date.now(),
        type: 'alert',
        title: `New Alert: ${alert.severity.toUpperCase()}`,
        message: alert.message,
        timestamp: new Date().toISOString(),
        read: false
      }});
    });

    socket.on('notification', (notification) => {
      dispatch({ type: 'ADD_NOTIFICATION', payload: notification });
    });

    return () => {
      socket.off('metrics_update');
      socket.off('new_alert');
      socket.off('notification');
    };
  }, [socket]);

  const fetchMetrics = async () => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      const response = await axios.get('/api/metrics');
      dispatch({ type: 'UPDATE_METRICS', payload: response.data });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  const fetchAlerts = async () => {
    try {
      const response = await axios.get('/api/alerts');
      dispatch({ type: 'UPDATE_ALERTS', payload: response.data });
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
    }
  };

  const fetchNotifications = async () => {
    try {
      const response = await axios.get('/api/notifications');
      dispatch({ type: 'SET_NOTIFICATIONS', payload: response.data });
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    }
  };

  const dismissAlert = async (alertId) => {
    try {
      await axios.delete(`/api/alerts/${alertId}`);
      dispatch({ type: 'DISMISS_ALERT', payload: alertId });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message });
    }
  };

  const updateSettings = async (newSettings) => {
    try {
      await axios.post('/api/settings', newSettings);
      dispatch({ type: 'UPDATE_SETTINGS', payload: newSettings });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message });
    }
  };

  const value = {
    ...state,
    dispatch,
    fetchMetrics,
    dismissAlert,
    updateSettings
  };

  return (
    <DashboardContext.Provider value={value}>
      {children}
    </DashboardContext.Provider>
  );
};

export const useDashboard = () => {
  const context = useContext(DashboardContext);
  if (!context) {
    throw new Error('useDashboard must be used within DashboardProvider');
  }
  return context;
};