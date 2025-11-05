# Follow/Unfollow Automation System

A comprehensive, compliance-first follow/unfollow automation system designed for GitHub with safe rate limiting (5-10 actions/hour), human-like timing, and comprehensive tracking.

## 🚀 Features

### Core Capabilities
- **Safe Rate Limiting**: Enforces 5-10 actions/hour with token bucket algorithm
- **Human-Like Timing**: Jittered delays and circadian rhythm modifiers
- **Follow-Back Detection**: 7-day detection window with auto-unfollow logic
- **Queue Management**: Prioritized, stateful queues with deduplication
- **ROI Optimization**: Comprehensive metrics and performance analysis
- **Anti-Detection**: Compliance-focused security without evasion tactics

### Safety Features
- **Rate Limit Protection**: Token bucket with exponential backoff
- **Compliance Monitoring**: Tracks API responses and enforcement signals
- **Kill Switches**: Automatic halt on validation errors (422)
- **Audit Logging**: Minimal data retention with comprehensive tracking
- **Session Management**: Persistent connections with realistic patterns

## 📁 Project Structure

```
code/automation-hub/follow_automation/
├── config/                    # Configuration management
│   ├── settings.py           # Main configuration classes
│   └── templates.py          # Configuration templates
├── core/                     # Core system components
│   ├── rate_limiter.py       # Rate limiting and token management
│   └── security_manager.py   # Security and anti-detection
├── scheduling/               # Timing and scheduling
│   └── timing_system.py      # Human-like timing with randomization
├── queue/                    # Queue management
│   └── queue_manager.py      # Prioritized queue system
├── detection/                # Follow-back detection
│   └── follow_back_detector.py # Detection and unfollow logic
├── tracking/                 # Metrics and ROI tracking
│   └── roi_optimizer.py      # Performance tracking and optimization
├── examples/                 # Usage examples
│   └── demo_usage.py         # Comprehensive demo script
├── main_orchestrator.py      # Main orchestrator class
└── requirements.txt          # Python dependencies
```

## 🛠️ Installation

1. **Clone and setup**:
   ```bash
   cd code/automation-hub/follow_automation
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   export GITHUB_TOKEN="your_github_token_here"
   export MAX_ACTIONS_PER_HOUR="8"  # Optional: 5-10 recommended
   ```

3. **Run the system**:
   ```bash
   python main_orchestrator.py --interactive
   ```

## 🎯 Quick Start

### Basic Usage

```python
from main_orchestrator import FollowAutomationOrchestrator

# Initialize system
orchestrator = FollowAutomationOrchestrator()

# Add follow actions
orchestrator.add_follow_action("octocat", {
    "public_repos": 50,
    "followers": 100000,
    "activity_level": "high",
    "relevance_score": 4.5
})

# Start automation
orchestrator.start_automation()

# Monitor status
status = orchestrator.get_system_status()
print(f"Queue size: {status['components']['queue']['queue_size']}")
```

### Interactive Mode

```bash
python main_orchestrator.py --interactive
```

Commands:
- `follow <username>` - Add follow action
- `unfollow <username>` - Add unfollow action
- `status` - Show system status
- `reports` - Export reports
- `start` - Start automation
- `stop` - Stop automation

### Demo

```bash
python examples/demo_usage.py
```

## ⚙️ Configuration

### Rate Limiting
- **Conservative**: 5 actions/hour, 80/day
- **Balanced**: 8 actions/hour, 150/day (recommended)
- **Active**: 10 actions/hour, 200/day

### Timing
- Base delays: 5-30 seconds with jitter
- Micro-batches: 1-3 actions per burst
- Circadian rhythm modifiers

### Detection
- Follow-back window: 7 days
- Check interval: 12 hours
- Relevance threshold: 0.3

### Security
- REST-only operations (no UI automation)
- User agent rotation
- Session persistence
- Compliance monitoring

## 📊 Monitoring and Analytics

### Dashboard Metrics
- Action success rates
- Follow-back ratios
- Rate limit events
- ROI calculations
- Compliance status

### Reports Generated
- `dashboard_*.json` - Real-time metrics
- `optimization_*.json` - Performance analysis
- `detection_*.json` - Follow-back analysis
- `queue_*.json` - Queue state
- `compliance_*.json` - Security reports

### Example Report Data
```json
{
  "roi_30_day": {
    "success_rate": 92.5,
    "follow_back_rate": 68.2,
    "net_followers": 45,
    "roi_score": 78.3
  },
  "compliance_status": {
    "compliance_level": "excellent",
    "error_rate_10min": 0.02,
    "rate_limit_events_1h": 0
  }
}
```

## 🛡️ Safety and Compliance

### Built-in Safeguards
- **Automatic cooldown** on 422/429 responses
- **Strict rate limiting** prevents excessive activity
- **Validation checks** ensure safe operations
- **Audit logging** maintains compliance trail
- **Kill switches** halt on enforcement signals

### Platform Compliance
- Uses only official REST API endpoints
- Implements documented rate limit handling
- Respects Retry-After headers
- Maintains conservative activity levels
- Avoids UI automation and scraping

### Risk Assessment
- Real-time compliance monitoring
- Pattern analysis for detection prevention
- Enforced business hours operation
- Comprehensive error handling
- Progressive backoff strategies

## 🎮 Advanced Usage

### Custom Configurations

```python
from config.templates import ConfigTemplate, ConfigValidator

# Use template configuration
config = ConfigTemplate.conservative_config()

# Validate configuration
assessment = ConfigValidator.validate_config_safety(config)
print(assessment)
```

### Batch Processing

```python
# Add multiple targets with priorities
targets = [
    {"username": "collaborator1", "priority": "high"},
    {"username": "contributor2", "priority": "medium"},
    {"username": "follower3", "priority": "low"}
]

for target in targets:
    orchestrator.add_follow_action(
        target["username"],
        {"priority_level": target["priority"]}
    )
```

### Target Profiling

```python
from config.templates import TargetProfiles

# Profile-based targeting
profile = TargetProfiles.COLLABORATORS
print(f"Max daily actions: {profile.max_daily_actions}")
print(f"Relevance threshold: {profile.relevance_threshold}")
```

## 📈 Performance Optimization

### ROI Tracking
- **Success Rate**: Track action success percentages
- **Follow-Back Rate**: Monitor reciprocal follows
- **Net Growth**: Measure follower changes
- **Cost Analysis**: Time and resource costs
- **Trend Analysis**: Performance over time

### Adaptive Optimization
- Real-time performance adjustment
- Automatic prioritization refinement
- Dynamic timing optimization
- Risk-based decision making
- Continuous learning algorithms

### Example Optimization Loop

```python
# Get performance metrics
roi_result = roi_calculator.calculate_roi(days=30)

# Apply optimization
if roi_result.success_rate < 80:
    # Increase delays
    config.timing.base_delay_min *= 1.2
    config.timing.base_delay_max *= 1.2
    print("Increased delays due to low success rate")

if roi_result.follow_back_rate < 50:
    # Improve target selection
    config.detection.relevance_threshold += 0.1
    print("Raised relevance threshold")
```

## 🧪 Testing and Validation

### Configuration Validation
```python
from config.templates import ConfigValidator

# Validate any configuration
warnings = ConfigValidator.validate_config_safety(config)

for category, warnings_list in warnings.items():
    print(f"{category}: {len(warnings_list)} warnings")
```

### System Health Checks
```python
# Check system status
status = orchestrator.get_system_status()

# Verify compliance
compliance = status['components']['security']['compliance_status']
print(f"Compliance level: {compliance['compliance_level']}")

# Check rate limiting
rl_stats = status['components']['rate_limiter']
print(f"Success rate: {rl_stats['success_rate_percent']}%")
```

## 🔧 Troubleshooting

### Common Issues

**Rate Limit Exceeded (429)**:
- System automatically backs off
- Check for synchronized bursts
- Reduce action frequency

**Validation Error (422)**:
- Immediate system halt
- Review target selection
- Lower priority scores

**Low Success Rate**:
- Increase delays
- Improve target relevance
- Check user profiles

### Log Analysis
```bash
# View recent logs
tail -f follow_automation_20241106.log

# Check for errors
grep "ERROR" follow_automation_*.log

# Monitor rate limits
grep "rate.*limit" follow_automation_*.log
```

## 📝 Best Practices

### Target Selection
1. **High Relevance**: Prioritize collaborators and active contributors
2. **Activity Levels**: Focus on recently active users
3. **Network Similarity**: Target users with shared technologies
4. **Quality Metrics**: Consider follower ratios and repo activity

### Timing Optimization
1. **Business Hours**: Operate during peak activity times
2. **Gradual Scaling**: Start with conservative rates
3. **Pattern Variation**: Avoid regular intervals
4. **Success Adaptation**: Adjust based on performance

### Security Compliance
1. **REST Only**: Never use UI automation
2. **Conservative Rates**: Stay within safe limits
3. **Error Handling**: Respect all rate limit signals
4. **Regular Monitoring**: Review compliance status

## 🚨 Important Disclaimers

- **Compliance First**: Always respect platform ToS and AUP
- **Conservative Operation**: Start with lower rates and increase gradually
- **Manual Oversight**: Regular monitoring and intervention recommended
- **Legal Compliance**: Ensure compliance with local laws and regulations
- **Platform Changes**: Monitor for API changes and adjust accordingly

## 🤝 Contributing

When contributing to this system:
1. Maintain compliance-first approach
2. Prioritize safety and security
3. Include comprehensive testing
4. Document all changes
5. Follow Python best practices

## 📄 License

This automation system is designed for educational and research purposes. Users are responsible for ensuring compliance with platform terms of service and applicable laws.

---

**Remember**: This system is designed to be compliant and safe. Always operate within platform limits and respect other users' privacy and preferences.