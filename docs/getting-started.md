# Getting Started with Automation Hub

Welcome to the Automation Hub! This guide will help you set up and safely use the GitHub automation system.

## 🎯 What This Tool Does

The Automation Hub helps you:
- ✅ **Track repository growth** (stars, forks, contributors)
- ✅ **Find follow/unfollow candidates** (read-only analysis)
- ✅ **Monitor automation compliance** (safety checks)
- ✅ **Generate audit reports** (comprehensive logging)
- ⚠️ **Execute follow/unfollow actions** (disabled by default)

**Important**: All automation features are **disabled by default** for safety.

## 📋 Prerequisites

Before starting, ensure you have:

1. **Python 3.9 or higher**:
   ```bash
   python --version
   ```

2. **GitHub Personal Access Token**:
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Generate new token with minimal scopes:
     - `read:user` (required for all operations)
     - `user:follow` (only if you plan to enable following)

3. **Git** (for cloning and version control)

## 🚀 Step-by-Step Setup

### Step 1: Install the System

```bash
# Clone the repository
git clone <repository-url>
cd automation-hub

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Set Up GitHub Token

**🔐 CRITICAL**: The GitHub token is required and must be set as an environment variable:

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

To make this permanent, add to your shell profile (`~/.bashrc`, `~/.zshrc`):
```bash
echo 'export GITHUB_TOKEN="your_token_here"' >> ~/.bashrc
```

### Step 3: Create Configuration

```bash
# Generate configuration template
python -m scripts.cli config create-template

# Copy safe configuration (recommended for beginners)
cp config/config_safe.yaml config.yaml
```

### Step 4: Validate Setup

```bash
# Check if everything is configured correctly
python -m scripts.cli config validate

# Verify safety status
python -m scripts.cli safety --check

# Check current status
python -m scripts.cli status
```

If all commands run without errors, you're ready to proceed!

## 🎮 First Steps (Safe Mode)

### Explore Your Current State (Read-Only)

Start with **read-only operations** to understand your current GitHub state:

```bash
# Check your current automation status
python -m scripts.cli status --detailed

# Find potential unfollow candidates (analysis only)
python -m scripts.cli unfollow-candidates --limit 20

# Generate a comprehensive audit report
python -m scripts.cli audit report --format summary
```

### Understand the Output

The `unfollow-candidates` command shows users you follow who don't follow back, sorted by likelihood to unfollow:

```
📋 Found 15 unfollow candidates:
------------------------------------------------------------
Username            Score    Repos   Followers
------------------------------------------------------------
user1               3.5      0       5
user2               2.8      1       12
user3               2.1      2       8
```

**Score interpretation**:
- **3.0+**: High priority unfollow (low activity, no recent interaction)
- **1.0-3.0**: Medium priority unfollow (moderate activity)
- **<1.0**: Low priority unfollow (active user, consider keeping)

## 🧪 Testing with Dry Runs

Before enabling any automation, test everything with **dry runs**:

```bash
# Test follow action (no actual following)
python -m scripts.cli follow --username testuser --dry-run

# Test unfollow action (no actual unfollowing)
python -m scripts.cli execute-unfollow --usernames user1 user2 --dry-run
```

Dry runs simulate the exact behavior without making actual API calls.

## ⚙️ Configuration Walkthrough

Open your configuration file to understand the key settings:

```bash
nano config.yaml
```

### Critical Settings to Understand

```yaml
# Core automation (KEEP DISABLED)
automation:
  enabled: false              # ← KEEP FALSE until tested
  operation_mode: "analysis"  # "analysis" = safe, "active" = risky

# Rate limits (CONSERVATIVE DEFAULTS)
rate_limits:
  max_actions_per_hour: 24    # ← Safe range: 12-30
  base_delay_seconds: 150     # ← 2.5 minutes between actions
  
# Follow automation (HIGH RISK)
follow_unfollow:
  auto_follow_enabled: false   # ← NEVER enable without testing
  auto_unfollow_enabled: false # ← NEVER enable without testing
```

### Safety Features (Never Disable)

```yaml
safety_features:
  emergency_stop_on_422: true      # ← Stops on spam signals
  exponential_backoff_on_429: true # ← Respects rate limits
  audit_logging: true              # ← Full audit trail
```

## 🔄 Enabling Automation Safely

⚠️ **Only proceed after thorough testing!**

### 1. Enable Read-Only Mode First

```yaml
# In config.yaml
automation:
  enabled: true              # Now enable for read-only operations
  operation_mode: "analysis" # Analysis mode is safe
```

### 2. Test with Individual Actions

```bash
# Enable automation (requires explicit confirmation)
python -m scripts.cli safety --enable

# Execute single action
python -m scripts.cli follow --username targetuser

# Check status immediately after
python -m scripts.cli status --detailed
```

### 3. Monitor Compliance

```bash
# Check compliance status
python -m scripts.cli safety --check

# Generate audit report
python -m scripts.cli audit report
```

## 📊 Understanding Reports

### Status Report

```
🤖 Automation Hub Status
==================================================
Status: 🟢 Running
Runtime: 2.5 hours
Total Actions: 12
Success Rate: 100.0%

📊 Detailed Statistics:
  Successful Actions: 12
  Failed Actions: 0
  422 Errors: 0 (enforcement signals)
  429 Errors: 0 (rate limits)
  Follow-back Ratio: 1.25
```

### Compliance Report

```
🛡️ Compliance Assessment:
Compliance Score: 95.0/100

⚠️ Risk Indicators:
  MEDIUM: Frequent rate limiting (3 rate limit hits in session)

💡 Recommendations:
  • Increase delays between actions to reduce rate limit occurrences
```

## 🚨 Emergency Procedures

### If You See 422 Errors

**🚨 STOP IMMEDIATELY** - 422 indicates spam/enforcement signals:

```bash
# Disable automation
python -m scripts.cli safety --disable

# Review audit logs
python -m scripts.cli audit export --format json
```

### If Rate Limits Are Hit Frequently

```bash
# Increase delays (edit config.yaml)
rate_limits:
  base_delay_seconds: 300  # Increase from 150 to 300 (5 minutes)
  min_gap_between_actions: 600  # Increase from 300 to 600 (10 minutes)

# Or reduce hourly limits
  max_actions_per_hour: 12  # Reduce from 24 to 12
```

### General Troubleshooting

```bash
# Check recent logs
tail -f automation_hub.log

# Validate configuration
python -m scripts.cli config validate

# Reset to safe defaults
cp config/config_safe.yaml config.yaml
```

## 📈 Advanced Usage

### Automated Workflows

Set up GitHub Actions for regular automation:

1. Copy workflows from `workflows/` directory
2. Customize for your repository
3. Set up secrets (GitHub token)
4. Enable workflows

### Custom Analysis

```python
# Use the Python API directly
from scripts.automation_manager import AutomationManager

manager = AutomationManager('config.yaml')
candidates = manager.get_follow_back_candidates()
# Analyze candidates in detail
```

### Performance Monitoring

```bash
# Export detailed metrics
python -m scripts.cli audit export --format json

# Check performance over time
python -c "
import json
with open('telemetry_export_*.json') as f:
    data = json.load(f)
    print(f'Average success rate: {data[\"performance_summary\"][\"action_statistics\"][\"success_rate\"]}%')
"
```

## ✅ Next Steps

After completing this guide:

1. **Bookmark the [Safety Guidelines](safety-guidelines.md)** - Read them thoroughly
2. **Review [Configuration Guide](configuration.md)** - Understand all options
3. **Check [CLI Reference](cli-reference.md)** - Learn all available commands
4. **Explore [Monitoring & Analytics](monitoring.md)** - Set up ongoing monitoring

## 🆘 Getting Help

- **Documentation**: Check the `docs/` directory for detailed guides
- **Troubleshooting**: See [troubleshooting.md](troubleshooting.md)
- **FAQ**: Check [faq.md](faq.md) for common questions
- **Issues**: Open a GitHub issue for bugs or feature requests

## 🎉 Congratulations!

You now have a fully configured, safe automation system. Remember:

- ✅ **Always test with dry runs first**
- ✅ **Monitor compliance regularly**
- ✅ **Keep audit logs**
- ✅ **Start conservatively, optimize gradually**

**Happy automating!** 🤖✨
