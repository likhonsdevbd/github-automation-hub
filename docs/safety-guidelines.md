# Safety Guidelines

⚠️ **CRITICAL**: Read this guide thoroughly before enabling any automation features. These guidelines are designed to keep your GitHub account safe and compliant.

## 🛡️ Core Safety Principles

### 1. **Safety First, Always**
- All automation features are **disabled by default** for good reason
- Never disable safety features like emergency stops or rate limiting
- When in doubt, choose the more conservative option

### 2. **Compliance Over Convenience**
- GitHub's Acceptable Use Policies take precedence over any automation benefits
- If you receive enforcement signals (422 errors), **stop immediately**
- Err on the side of caution with all rate limits and timing

### 3. **Human-in-the-Loop Operations**
- Maintain manual oversight of all automation activities
- Regularly review audit logs and compliance reports
- Be prepared to disable automation at any time

## ⚡ Rate Limiting Safety

### Conservative Limits (Recommended)

| Action Type | Limit | Delay | Rationale |
|-------------|-------|-------|-----------|
| Follow/Unfollow | 12-24/hour | 2.5-5 minutes | Stay well below potential enforcement thresholds |
| API Calls | <5000/hour | N/A | Respect GitHub's documented limits |
| Concurrent Actions | 1 maximum | N/A | Avoid synchronized bursts |

### Safe Rate Configuration

```yaml
# Conservative safe configuration
rate_limits:
  max_actions_per_hour: 12   # Very conservative: 12/hour
  base_delay_seconds: 300    # 5 minutes between actions
  min_gap_between_actions: 300 # 5 minutes minimum
  jitter_factor: 0.3         # 30% variability
```

### Rate Limit Warning Signs

⚠️ **Take immediate action if you observe:**

- **429 errors > 5%** of requests
- **Consistent rate limiting** across multiple days
- **Increasing delays** needed between actions
- **Spikes in error rates**

## 🚨 Emergency Stop Procedures

### Automatic Stops

The system will automatically stop if:
- **422 errors detected** (spam/enforcement signals)
- **Critical compliance violations**
- **Rate limits consistently exceeded**

### Manual Stops

```bash
# Disable all automation immediately
python -m scripts.cli safety --disable

# Or stop the automation manager
python -m scripts.cli status  # Check current status
```

### Emergency Actions

1. **Stop automation immediately**
2. **Review recent audit logs**
3. **Check compliance report**
4. **Identify root cause**
5. **Wait before restarting** (at least 24 hours)

## 📊 Compliance Monitoring

### Daily Compliance Checks

```bash
# Check current compliance status
python -m scripts.cli safety --check

# Generate detailed audit report
python -m scripts.cli audit report

# Review recent events
python -m scripts.cli audit export --format json
```

### Key Compliance Metrics

| Metric | Safe Range | Action Required |
|--------|------------|-----------------|
| 422 Error Rate | 0% | Any occurrence = stop immediately |
| 429 Error Rate | <1% | <1% ok, >1% increase delays |
| Success Rate | >95% | <90% review and adjust |
| Compliance Score | >90/100 | <80/100 stop and investigate |

### Compliance Score Calculation

The system calculates compliance scores based on:
- ✅ Error rates (lower is better)
- ✅ Rate limiting adherence
- ✅ Audit trail completeness
- ✅ Safety feature status

## 🔍 Monitoring and Alerts

### Log Monitoring

```bash
# Monitor logs in real-time
tail -f automation_hub.log | grep -E "(422|429|ERROR|WARNING)"

# Search for specific events
grep "enforcement_signal" automation_hub.log
grep "emergency_stop" automation_hub.log
```

### Performance Indicators

Monitor these trends for early warning:
- **Increasing 429 error rates**
- **Decreasing success rates**
- **Higher latency between actions**
- **Compliance score trending down**

### Automated Alerts

Configure notifications in `config.yaml`:

```yaml
notifications:
  enabled: true
  webhook_url: "your_webhook_url"
  
  alert_thresholds:
    422_error_rate: 0.0      # Alert on ANY 422 errors
    429_error_rate: 0.01     # Alert on 1% 429 errors
    consecutive_failures: 1   # Alert on first failure
```

## 🎯 Best Practices

### Safe Automation Patterns

✅ **DO:**
- Start with read-only analysis mode
- Use dry runs before any actual actions
- Monitor compliance continuously
- Keep detailed audit logs
- Use conservative rate limits
- Implement gradual rollout

❌ **DON'T:**
- Disable safety features
- Increase rate limits beyond 30/hour
- Ignore enforcement signals
- Run automation 24/7
- Use automation during peak hours
- Mass follow/unfollow operations

### Timeline Recommendations

| Phase | Duration | Actions | Monitoring |
|-------|----------|---------|------------|
| **Setup** | 1-2 days | Configuration & validation | Continuous |
| **Testing** | 1 week | Dry runs, analysis mode | Daily checks |
| **Pilot** | 1 month | Single actions, conservative limits | Continuous |
| **Production** | Ongoing | Full automation, optimized settings | Real-time |

### Time-Based Safety Rules

- **Business Hours Only**: Run automation 9 AM - 5 PM local time
- **Weekend Reduction**: Reduce activity by 50% on weekends
- **Holiday Pause**: Stop automation during major holidays
- **Gradual Ramp-Up**: Increase limits slowly over weeks

## 🔐 Token Security

### Token Management

- **Use minimal scopes**: Only `read:user` for analysis
- **Regular rotation**: Change tokens every 90 days
- **Environment storage**: Never hardcode tokens in config files
- **Secure storage**: Use environment variables or secure vaults

### Token Security Checklist

- [ ] Token stored in environment variable only
- [ ] Minimal required scopes granted
- [ ] Token rotation schedule established
- [ ] Revoke unused tokens immediately
- [ ] Monitor token usage for anomalies

## 📋 Pre-Deployment Checklist

Before enabling automation for the first time:

- [ ] Configuration reviewed and validated
- [ ] GitHub token configured with minimal scopes
- [ ] Safety features enabled and tested
- [ ] Audit logging configured
- [ ] Rate limits set conservatively
- [ ] Emergency stop procedures documented
- [ ] Monitoring and alerting set up
- [ ] Team members trained on safety procedures
- [ ] Backup configuration saved
- [ ] Rollback plan prepared

## 🚨 Incident Response

### If You Receive 422 Errors

**IMMEDIATE ACTION REQUIRED:**

1. Stop all automation:
   ```bash
   python -m scripts.cli safety --disable
   ```

2. Review audit logs:
   ```bash
   python -m scripts.cli audit export --format json
   ```

3. Analyze recent actions for patterns

4. Wait 24-48 hours before resuming

5. Reduce rate limits when restarting

### If You Hit Rate Limits Frequently

1. Increase delays between actions
2. Reduce hourly action limits
3. Implement circadian rhythm modifiers
4. Add more jitter to timing patterns
5. Consider spreading actions across longer periods

### If Success Rate Drops Below 90%

1. Stop automation immediately
2. Review error patterns
3. Check for enforcement signals
4. Validate token permissions
5. Test with single actions
6. Gradually resume with reduced limits

## 📚 Additional Resources

- [GitHub Acceptable Use Policies](https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies)
- [GitHub API Rate Limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)
- [REST API Best Practices](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api)

## 🤝 Support and Community

- **Documentation**: Check `docs/` directory for detailed guides
- **Issues**: Report bugs or request features via GitHub issues
- **Discussions**: Join community discussions for questions and sharing experiences

---

**Remember**: It's better to be safe than sorry. When in doubt, stop automation and review your configuration.

🛡️ **Stay safe, stay compliant!** 🛡️
