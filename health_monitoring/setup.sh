#!/bin/bash

# Repository Health Monitoring System Setup Script
# This script helps you set up the health monitoring system

set -e

echo "🚀 Setting up Repository Health Monitoring System"
echo "================================================="

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✓ Python version: $python_version"

if [[ $(echo "$python_version >= 3.8" | bc -l) -eq 0 ]]; then
    echo "❌ Python 3.8+ required. Current version: $python_version"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Make script executable
chmod +x scripts/health_monitor.py

# Create required directories
echo "📁 Creating directories..."
mkdir -p data reports dashboard_data alerts logs config

# Copy example configuration files
if [ ! -f "config/config.yaml" ]; then
    echo "📋 Creating configuration files..."
    cp config/config.yaml.example config/config.yaml
    echo "✓ Created config/config.yaml from example"
fi

if [ ! -f "config/alert_rules.yaml" ]; then
    cp config/alert_rules.yaml.example config/alert_rules.yaml
    echo "✓ Created config/alert_rules.yaml from example"
fi

# Create .env.example file
cat > .env.example << 'EOF'
# GitHub Configuration
GITHUB_TOKEN=your_github_personal_access_token_here

# Email Notifications (optional)
EMAIL_USERNAME=your_email@example.com
EMAIL_PASSWORD=your_email_password_or_app_password
SMTP_SERVER=smtp.gmail.com

# Slack Integration (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# Discord Integration (optional)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/DISCORD/WEBHOOK

# Additional Integrations (optional)
SLACK_APP_TOKEN=xoxb-your-slack-app-token
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
DISCORD_BOT_TOKEN=your_discord_bot_token
PAGERDUTY_API_KEY=your_pagerduty_api_key
OPSGENIE_API_KEY=your_opsgenie_api_key
EOF

echo "✓ Created .env.example file"

# Create quick start guide
cat > QUICKSTART.md << 'EOF'
# Quick Start Guide

## 1. Set up GitHub Token

1. Go to GitHub Settings > Developer settings > Personal access tokens
2. Generate new token with scopes: `repo`, `read:org`
3. Copy the token

## 2. Configure the system

1. Copy `.env.example` to `.env` and fill in your credentials
2. Edit `config/config.yaml` with your settings
3. Edit `config/alert_rules.yaml` if needed

## 3. Test the system

```bash
# Run health monitoring for a test repository
python scripts/health_monitor.py \
  --repositories "owner/test-repo" \
  --config config/config.yaml \
  --skip-alerts
```

## 4. Set up automated monitoring

1. Create GitHub Actions workflow files (see `.github/workflows/`)
2. Add secrets to your repository settings
3. Enable daily scheduled runs

## 5. Customize alerts

Edit `config/alert_rules.yaml` to:
- Adjust thresholds
- Enable/disable specific alerts
- Configure notification channels
- Set repository-specific overrides

For more details, see the full README.md
EOF

echo "✓ Created QUICKSTART.md"

# Create a simple test script
cat > test_setup.py << 'EOF'
#!/usr/bin/env python3
"""
Test script to verify health monitoring system setup
"""

import sys
import os
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_imports():
    """Test that all required modules can be imported"""
    try:
        from github_api_client import GitHubAPIClient
        from health_score_calculator import HealthScoreCalculator
        from community_engagement_tracker import CommunityEngagementTracker
        from report_generator import ReportGenerator
        from dashboard_data_generator import DashboardDataGenerator
        from alert_system import AlertSystem
        print("✓ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

async def test_github_token():
    """Test GitHub token if available"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("⚠️  GITHUB_TOKEN not set - skipping GitHub API test")
        return True
    
    try:
        from github_api_client import GitHubAPIClient
        async with GitHubAPIClient(token) as client:
            # Test a simple API call
            user = await client._make_request("/user")
            print(f"✓ GitHub API working - authenticated as: {user.get('login', 'unknown')}")
            return True
    except Exception as e:
        print(f"❌ GitHub API test failed: {e}")
        return False

async def main():
    print("🧪 Testing Repository Health Monitoring System Setup")
    print("=" * 50)
    
    success = True
    
    # Test imports
    success &= await test_imports()
    
    # Test GitHub token
    success &= await test_github_token()
    
    if success:
        print("\n🎉 Setup test passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Configure your repositories in config/config.yaml")
        print("2. Set up notification channels (email, Slack, etc.)")
        print("3. Run: python scripts/health_monitor.py --help")
        print("4. See QUICKSTART.md for detailed setup instructions")
    else:
        print("\n❌ Setup test failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
EOF

chmod +x test_setup.py

echo ""
echo "✅ Setup Complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Set your GitHub token: export GITHUB_TOKEN='your_token_here'"
echo "2. Configure repositories: edit config/config.yaml"
echo "3. Test the setup: python test_setup.py"
echo "4. Run monitoring: python scripts/health_monitor.py --help"
echo ""
echo "📖 For detailed instructions, see:"
echo "   - README.md (comprehensive documentation)"
echo "   - QUICKSTART.md (quick setup guide)"
echo "   - config/config.yaml.example (configuration options)"
echo ""
echo "🎯 Quick test:"
echo "python scripts/health_monitor.py --repositories 'octocat/Hello-World' --config config/config.yaml --skip-alerts"
echo ""