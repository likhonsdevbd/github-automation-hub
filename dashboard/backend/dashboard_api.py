from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import json
import asyncio
import time
import random
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models
class AlertModel(BaseModel):
    id: int
    severity: str
    message: str
    source: str
    timestamp: datetime
    acknowledged: bool = False
    read: bool = False
    details: Optional[dict] = None

class NotificationModel(BaseModel):
    id: int
    type: str
    title: str
    message: str
    timestamp: datetime
    read: bool = False

class SettingsModel(BaseModel):
    refresh_interval: int = 5000
    enable_sound: bool = True
    enable_push: bool = True
    theme: str = "dark"

class MetricsModel(BaseModel):
    system: Dict
    automation: Dict
    github: Dict
    health: Dict

# Initialize FastAPI app
app = FastAPI(
    title="Automation Hub Dashboard API",
    description="Real-time monitoring and dashboard system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[WebSocket, List[str]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.subscriptions[websocket] = []

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

# Mock data generators
def generate_system_metrics():
    """Generate realistic system metrics"""
    return {
        "cpu": round(random.uniform(20, 80), 1),
        "memory": round(random.uniform(40, 85), 1),
        "disk": round(random.uniform(30, 90), 1),
        "network": round(random.uniform(10, 150), 1),
        "uptime": random.randint(86400, 604800)  # 1 day to 1 week
    }

def generate_automation_metrics():
    """Generate automation metrics"""
    return {
        "active": random.randint(0, 10),
        "queued": random.randint(5, 25),
        "completed": random.randint(50, 200),
        "failed": random.randint(0, 5),
        "rate": random.randint(5, 20)
    }

def generate_github_metrics():
    """Generate GitHub API metrics"""
    return {
        "requests": random.randint(50, 300),
        "limits": {
            "core": {
                "used": random.randint(100, 4500),
                "limit": 5000
            },
            "search": {
                "used": random.randint(1, 28),
                "limit": 30
            }
        }
    }

def generate_health_score():
    """Generate health score based on metrics"""
    system = generate_system_metrics()
    automation = generate_automation_metrics()
    
    # Calculate health score
    score = 100
    if system["cpu"] > 80: score -= 15
    if system["memory"] > 85: score -= 10
    if system["disk"] > 90: score -= 20
    if automation["failed"] > automation["completed"] * 0.1: score -= 25
    
    return max(0, score)

# Mock data store
mock_alerts = [
    AlertModel(
        id=1,
        severity="warning",
        message="High CPU usage detected",
        source="System Monitor",
        timestamp=datetime.now() - timedelta(minutes=5),
        read=False,
        details={"cpu_usage": 85, "threshold": 80}
    ),
    AlertModel(
        id=2,
        severity="info",
        message="Daily health check completed",
        source="Automation Bot",
        timestamp=datetime.now() - timedelta(minutes=15),
        read=False
    ),
    AlertModel(
        id=3,
        severity="critical",
        message="GitHub API rate limit approaching",
        source="GitHub Monitor",
        timestamp=datetime.now() - timedelta(minutes=30),
        read=True,
        details={"remaining": 100, "limit": 5000}
    )
]

mock_notifications = [
    NotificationModel(
        id=1,
        type="alert",
        title="New Alert: WARNING",
        message="High CPU usage detected",
        timestamp=datetime.now() - timedelta(minutes=5),
        read=False
    ),
    NotificationModel(
        id=2,
        type="success",
        title="Automation Complete",
        message="Daily contribution tracking completed successfully",
        timestamp=datetime.now() - timedelta(minutes=15),
        read=False
    )
]

# Routes
@app.get("/")
async def root():
    return {"message": "Automation Hub Dashboard API", "version": "1.0.0"}

@app.get("/api/metrics")
async def get_metrics():
    """Get current system metrics"""
    try:
        metrics = {
            "system": generate_system_metrics(),
            "automation": generate_automation_metrics(),
            "github": generate_github_metrics(),
            "health": {
                "score": generate_health_score(),
                "issues": mock_alerts[:2],  # Show first 2 alerts as issues
                "lastUpdate": datetime.now().isoformat()
            }
        }
        return metrics
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/alerts")
async def get_alerts():
    """Get all alerts"""
    return [alert.dict() for alert in mock_alerts]

@app.delete("/api/alerts/{alert_id}")
async def dismiss_alert(alert_id: int):
    """Dismiss an alert"""
    global mock_alerts
    mock_alerts = [alert for alert in mock_alerts if alert.id != alert_id]
    return {"message": "Alert dismissed"}

@app.post("/api/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int):
    """Acknowledge an alert"""
    for alert in mock_alerts:
        if alert.id == alert_id:
            alert.acknowledged = True
            break
    return {"message": "Alert acknowledged"}

@app.get("/api/notifications")
async def get_notifications():
    """Get all notifications"""
    return [notification.dict() for notification in mock_notifications]

@app.post("/api/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: int):
    """Mark notification as read"""
    for notification in mock_notifications:
        if notification.id == notification_id:
            notification.read = True
            break
    return {"message": "Notification marked as read"}

@app.delete("/api/notifications")
async def clear_notifications():
    """Clear all notifications"""
    global mock_notifications
    mock_notifications = []
    return {"message": "All notifications cleared"}

@app.get("/api/settings")
async def get_settings():
    """Get dashboard settings"""
    return {
        "refresh_interval": 5000,
        "enable_sound": True,
        "enable_push": True,
        "theme": "dark"
    }

@app.post("/api/settings")
async def update_settings(settings: SettingsModel):
    """Update dashboard settings"""
    logger.info(f"Settings updated: {settings.dict()}")
    return {"message": "Settings updated successfully"}

# WebSocket endpoint for real-time updates
@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    logger.info("WebSocket connection established")
    
    try:
        while True:
            # Generate and send metrics update
            metrics_data = {
                "type": "metrics_update",
                "data": {
                    "system": generate_system_metrics(),
                    "automation": generate_automation_metrics(),
                    "github": generate_github_metrics(),
                    "health": {
                        "score": generate_health_score(),
                        "issues": mock_alerts[:2],
                        "lastUpdate": datetime.now().isoformat()
                    }
                }
            }
            
            await manager.send_personal_message(
                json.dumps(metrics_data), 
                websocket
            )
            
            # Occasionally send a new alert
            if random.random() < 0.1:  # 10% chance
                new_alert = AlertModel(
                    id=len(mock_alerts) + 1,
                    severity=random.choice(["info", "warning", "critical"]),
                    message=f"Generated alert at {datetime.now().strftime('%H:%M:%S')}",
                    source="System",
                    timestamp=datetime.now()
                )
                mock_alerts.insert(0, new_alert)
                
                alert_data = {
                    "type": "new_alert",
                    "data": new_alert.dict()
                }
                await manager.broadcast(json.dumps(alert_data))
            
            # Wait before next update
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket connection closed")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# System info endpoint
@app.get("/api/system/info")
async def get_system_info():
    """Get detailed system information"""
    try:
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "cpu_count": psutil.cpu_count(),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_used": psutil.virtual_memory().used,
            "memory_total": psutil.virtual_memory().total,
            "disk_percent": psutil.disk_usage('/').percent,
            "disk_used": psutil.disk_usage('/').used,
            "disk_total": psutil.disk_usage('/').total,
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
            "process_count": len(psutil.pids())
        }
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system info")

if __name__ == "__main__":
    uvicorn.run(
        "dashboard_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )