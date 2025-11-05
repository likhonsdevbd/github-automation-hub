# Daily Commit Automation - Quick Start Guide

## 📁 Complete File Structure

```
daily_contributions/
├── README.md                          # Comprehensive documentation
├── requirements.txt                   # Python dependencies
├── main_coordinator.py                # Main orchestration script
│
├── config/
│   └── automation_config.json        # Configuration settings
│
├── scripts/
│   ├── repo_health_checker.py        # Repository health improvements
│   ├── dependency_updater.py          # Dependency management  
│   ├── doc_automation.py              # Documentation automation
│   ├── code_quality_tool.py           # Code quality tools
│   ├── timing_manager.py              # Natural timing patterns
│   ├── setup.py                       # Installation script
│   └── utils.py                       # Utility functions
│
└── workflows/
    └── daily_automation.yml           # GitHub Actions workflow
```

## 🚀 Installation Commands

```bash
# 1. Navigate to your repository
cd /path/to/your/repo

# 2. Copy the automation system (if not already there)
# The system should already be at: ./code/automation-hub/daily_contributions/

# 3. Navigate to automation directory
cd code/automation-hub/daily_contributions

# 4. Run setup
python scripts/setup.py

# 5. Test the system
python main_coordinator.py --interactive
```

## ⚙️ First-Time Configuration

### 1. Basic Configuration Check
```bash
# Review the auto-generated configuration
cat config/automation_config.json
```

### 2. Customize Timing (Optional)
Edit `config/automation_config.json`:
```json
{
  "timing": {
    "working_hours_start": 9,      # Your start time (0-23)
    "working_hours_end": 17,       # Your end time (0-23)
    "commit_frequency": "2-4_per_day",
    "avoid_weekends": true,
    "timezone": "America/New_York" # Set your timezone
  }
}
```

### 3. Enable GitHub Actions (Recommended)
```bash
# Copy the workflow file
mkdir -p ../../.github/workflows/
cp workflows/daily_automation.yml ../../.github/workflows/

# The automation will now run automatically!
```

## 🧪 Testing the System

### Test Individual Components
```bash
# Test repository health checker
python -c "
from scripts.repo_health_checker import RepoHealthChecker
health = RepoHealthChecker()
tasks = health.get_improvement_tasks()
print(f'Found {len(tasks)} repository improvements')
"

# Test dependency updater  
python -c "
from scripts.dependency_updater import DependencyUpdater
updater = DependencyUpdater()
tasks = updater.get_pending_updates()
print(f'Found {len(tasks)} dependency updates')
"

# Test documentation automation
python -c "
from scripts.doc_automation import DocumentationAutomator
automator = DocumentationAutomator()
tasks = automator.get_documentation_tasks()
print(f'Found {len(tasks)} documentation improvements')
"
```

### Full System Test
```bash
# Interactive test (recommended first time)
python main_coordinator.py --interactive

# Dry run test
python -c "
import sys
sys.path.append('scripts')
from main_coordinator import DailyCommitCoordinator
coordinator = DailyCommitCoordinator()
coordinator.run_daily_cycle()
"
```

## 📊 Monitoring and Logs

### Check Automation Logs
```bash
# View recent automation activity
tail -f daily_contributions.log

# View commit history
cat .commit_history.json

# View latest automation report
cat automation_report.md 2>/dev/null || echo "No report yet"
```

### Analyze Commit Patterns
```bash
# Check timing analysis
python -c "
import sys
sys.path.append('scripts')
from scripts.timing_manager import TimingManager
from scripts.utils import AutomationUtils

utils = AutomationUtils()
info = utils.get_git_status()
print('Git Status:', info)

timing = TimingManager({})
analysis = timing.get_commit_pattern_analysis()
print('Pattern Analysis:', analysis)
"
```

## 🔧 Common Customizations

### Add Custom Scripts
Create `scripts/my_custom_checker.py`:
```python
from scripts.utils import AutomationUtils

class MyCustomChecker:
    def get_tasks(self):
        return [{
            "type": "custom_task",
            "description": "My custom improvement",
            "priority": 1
        }]
    
    def execute_task(self, task):
        # Your custom logic
        return True
```

### Modify Timing
```bash
# Edit timing settings
python -c "
import json
with open('config/automation_config.json', 'r') as f:
    config = json.load(f)

config['timing']['working_hours_start'] = 8
config['timing']['working_hours_end'] = 18
config['timing']['commit_frequency'] = '3-5_per_day'

with open('config/automation_config.json', 'w') as f:
    json.dump(config, f, indent=2)
print('Timing updated!')
"
```

### Disable Specific Modules
```json
{
  "modules": {
    "repo_health": {"enabled": false},
    "dependency_updates": {"enabled": false},
    "documentation": {"enabled": true},
    "code_quality": {"enabled": true}
  }
}
```

## 🛡️ Safety Features

### Backup Before Running
```bash
# Create backup of current state
tar -czf backup_$(date +%Y%m%d_%H%M%S).tar.gz .
```

### Dry Run Mode
```bash
# Test without committing
export DRY_RUN=true
python main_coordinator.py --interactive
```

### Rollback if Needed
```bash
# Restore from backup
tar -xzf backup_YYYYMMDD_HHMMSS.tar.gz
```

## 📈 What to Expect

### First Run
```
🤖 Daily Commit Automation - Starting Cycle
🔍 Analyzing repository...
📊 Found 15 improvement opportunities
✅ Repository health: 5 improvements
📦 Dependencies: 3 updates available  
📚 Documentation: 4 improvements
⚡ Code quality: 3 enhancements

⏰ Checking timing...
✅ Good time for commits
🎯 Starting automation...

[Process runs, commits are made]
🎉 Automation cycle completed!
```

### After First Week
- Comprehensive README.md
- Missing configuration files (.gitignore, LICENSE, etc.)
- Updated dependencies
- Organized TODO.md
- Documentation guides
- Code quality improvements

### Ongoing Benefits
- Regular repository health improvements
- Up-to-date dependencies
- Consistent code quality
- Comprehensive documentation
- Natural commit history

## 🆘 Troubleshooting

### Permission Issues
```bash
# Ensure git is configured
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Check file permissions
ls -la
chmod +x scripts/*.py
```

### Import Errors
```bash
# Ensure all dependencies are installed
pip install -r requirements.txt

# Check Python path
echo $PYTHONPATH
```

### No Tasks Found
```bash
# Check if improvements are actually needed
python -c "
import os
print('README exists:', os.path.exists('README.md'))
print('Has Python files:', bool(list(os.glob('**/*.py'))))
print('Has TODO items:', bool(list(os.glob('**/*.todo'))))
"
```

## 🎯 Best Practices

1. **Always test in interactive mode first**
2. **Review generated pull requests before merging**
3. **Monitor automation logs regularly**
4. **Backup important files periodically**
5. **Customize configuration for your project**
6. **Adjust timing based on your work schedule**
7. **Keep dependencies updated**
8. **Review and merge PRs promptly**

## 📞 Getting Help

- **Check logs**: `cat daily_contributions.log`
- **Test components**: Run individual script tests
- **Review configuration**: Check `config/automation_config.json`
- **GitHub Issues**: Open issues for bugs or feature requests
- **Documentation**: Read `README.md` for detailed information

---

**Ready to automate? Start with `python main_coordinator.py --interactive`!** 🚀