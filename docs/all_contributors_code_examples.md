# Quick Reference: All-Contributors Automation Code Examples

## 1. GitHub Actions Workflows

### Test Workflow (CI Pipeline)
```yaml
name: Test
on:
  push:
    branches: [main]
  pull_request:
    types: [opened, synchronize]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@08c6903cd8fde910a37f88322edcfb5dd907a8 # v5.0.0
      - uses: actions/setup-node@dbe1369d7be17e7823f8c1ee1ae8bec5779239dd # v3.9.0
        with:
          cache: npm
          node-version: 22
      - run: npm ci
      - run: npm test
      - run: ./node_modules/.bin/codecov --token=${{ secrets.CODECOV_TOKEN }}
```

### Release Workflow (Automated Deployment)
```yaml
name: Release
on:
  push:
    branches: [main]

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@08c6903cd8fde910a37f88322edcfb5dd907a8 # v5.0.0
      - uses: actions/setup-node@dbe1369d7be17e7823f8c1ee1ae8bec5779239dd # v3.9.0
        with:
          cache: npm
          node-version: lts/*
      - run: npm ci
      - run: npx semantic-release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Stats Workflow (Daily Analytics)
```yaml
name: Stats
on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight UTC
  workflow_dispatch: {}

jobs:
  stats:
    runs-on: ubuntu-latest
    steps:
      - uses: gr2m/app-stats-action@v1.x
        id: stats
        with:
          id: ${{ secrets.ALL_CONTRIBUTORS_APP_ID }}
          private_key: ${{ secrets.ALL_CONTRIBUTORS_APP_PRIVATE_KEY }}
      - run: "echo installations: '${{ steps.stats.outputs.installations }}'"
      - uses: logflare/action@v1
        with:
          api_key: ${{ secrets.LOGFLARE_API_KEY }}
          source_id: ${{ secrets.LOGFLARE_SOURCE_ID }}
          message: "stats: ${{ steps.stats.outputs.installations }} / ${{ steps.stats.outputs.repositories }}"
          metadata: |
            {
              "num_installations": ${{ steps.stats.outputs.installations }},
              "num_repositories": ${{ steps.stats.outputs.repositories }},
              "num_suspended_installations": ${{ steps.stats.outputs.suspended_installations }}
            }
```

## 2. Configuration Files

### .all-contributorsrc
```json
{
  "projectName": "app",
  "projectOwner": "all-contributors",
  "repoType": "github",
  "repoHost": "https://github.com",
  "files": ["README.md"],
  "imageSize": 100,
  "contributorsPerLine": 7,
  "commit": false,
  "skipCi": true,
  "commitConvention": "angular",
  "commitType": "docs",
  "contributors": [
    {
      "login": "username",
      "name": "User Name",
      "avatar_url": "https://github.com/username.png",
      "profile": "https://github.com/username",
      "contributions": ["code", "doc"]
    }
  ]
}
```

## 3. Bot Architecture Components

### Core Components Structure
```javascript
// Event Processing
/src/tasks/processIssueComment
├── CommentReply          // Response generation
├── ContentFiles         // README updates
├── OptionsConfig        // Configuration management
├── Repository           // GitHub API interface
└── utils/parse-comment  // Comment parsing
```

### Processing Flow
1. **Input:** GitHub event → `/src/tasks/processIssueComment`
2. **Parse:** `utils/parse-comment` determines intent
3. **Generate:** `CommentReply` creates response
4. **Update:** `ContentFiles` regenerates documentation
5. **Submit:** `Repository` creates branch and PR

## 4. Security Best Practices

### Action Version Pinning
```yaml
# ❌ Avoid (can break on new versions)
- uses: actions/checkout@v5

# ✅ Recommended (immutable)
- uses: actions/checkout@08c6903cd8fde910a37f88322edcfb5dd907a8
```

### Secret Management
```yaml
# ✅ Use GitHub Secrets
- run: npx semantic-release
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
```

### Environment Security
```yaml
# ✅ LTS versions for stability
node-version: lts/*

# ✅ Ubuntu runners for consistency
runs-on: ubuntu-latest

# ✅ npm ci for reproducible builds
run: npm ci  # Uses package-lock.json
```

## 5. Community Management Patterns

### Issue Templates Structure
```
.github/
└── ISSUE_TEMPLATE/
    ├── bug_report.md      # Bug reporting format
    └── feature_request.md # Feature request format
```

### Code Ownership Pattern
```
# .github/CODEOWNERS
# Global owners
* @maintainer1 @maintainer2

# Directory-specific owners
/docs/ @doc-team
/src/ @core-team
```

## 6. Automation Triggers Reference

### Common Triggers
```yaml
# Push to specific branches
on:
  push:
    branches: [main, develop]

# Pull request events
  pull_request:
    types: [opened, synchronize, closed]

# Scheduled execution
  schedule:
    - cron: '0 0 * * *'        # Daily at midnight
    - cron: '0 2 * * 1'        # Weekly on Monday 2 AM

# Manual trigger
  workflow_dispatch: {}

# Repository events
  issues:
    types: [opened, edited]
  issue_comment:
    types: [created, edited]
  pull_request_review:
    types: [submitted]
```

## 7. Dependencies and Tooling

### Key Packages
```json
{
  "dependencies": {
    "probot": "^12.0.0",      // GitHub App framework
    "@octokit/rest": "^20.0.0", // GitHub API client
    "semantic-release": "^21.0.0" // Automated releases
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "typescript": "^5.0.0"
  }
}
```

### GitHub Actions Integration
```yaml
# Common action patterns
- uses: actions/checkout@v5         # Repository checkout
- uses: actions/setup-node@v3       # Node.js setup
- uses: actions/cache@v3            # Dependency caching
- uses: codecov/codecov-action@v3   # Code coverage
```

---

**Quick Implementation Checklist:**
- [ ] Set up CI/CD with GitHub Actions
- [ ] Configure automated testing pipeline  
- [ ] Implement semantic versioning for releases
- [ ] Create issue templates for community
- [ ] Set up code owners for review automation
- [ ] Configure contributor acknowledgment bot
- [ ] Implement scheduled analytics collection
- [ ] Use GitHub Secrets for sensitive data
- [ ] Pin action versions for security
- [ ] Document contribution guidelines

**Author:** MiniMax Agent  
**Last Updated:** November 6, 2025