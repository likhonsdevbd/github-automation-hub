# Data directory structure

This directory contains data files for the automation hub:

## Files and their purposes:

### Cache files (auto-generated):
- `user_cache.json` - Cached user data to reduce API calls
- `rate_limit_cache.json` - Cached rate limit information
- `followers_cache.json` - Cached followers list (with ETags)
- `following_cache.json` - Cached following list (with ETags)

### User lists (manually curated):
- `target_users.json` - List of users you want to interact with
- `excluded_users.json` - Users to exclude from all automation
- `whitelist_users.json` - Users with special handling rules

### Analytics data (auto-generated):
- `daily_stats.json` - Daily automation statistics
- `performance_metrics.json` - Performance tracking data
- `compliance_reports.json` - Compliance audit data

### Configuration snapshots:
- `config_snapshots/` - Directory for configuration backups

## Data retention:
- Cache files are automatically refreshed based on ETag validation
- Old analytics data is automatically cleaned up based on retention settings
- Sensitive data is redacted from all logs and exports

## Privacy:
All user data is handled according to privacy settings in configuration.
Minimal necessary data is stored, and sensitive information is redacted.
