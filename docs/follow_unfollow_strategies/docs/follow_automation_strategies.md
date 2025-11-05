# GitHub Follow/Unfollow Automation: Safe Rates, Human-Like Behavior, Queues, Detection Logic, and Non-Detectable Tactics

## Executive Summary and Scope

This report analyzes automation of “follow” and “unfollow” actions on GitHub across two surfaces: the official GitHub REST Application Programming Interface (API) and the web user interface (UI). It outlines compliant and non-compliant strategies, safe operation envelopes, and implementation guardrails that reduce detection and enforcement risk.

Three conclusions anchor the analysis. First, GitHub’s policies treat automated, excessive, and inauthentic activity as prohibited conduct; engineering leaders should treat follow/unfollow automation as high-risk unless limited to narrow, compliant use cases and operated with strict controls[^3]. Second, the REST endpoints for followers and following exist, but mutating actions (follow/unfollow) require the user:follow scope and return signals that indicate spam or validation failures; these responses must be handled deterministically[^1]. Third, while general rate limits for the REST API are published, there are no official per-action quotas specific to follow/unfollow; practitioners should infer safe rates from platform guidance and observed signals, not fixed numbers, and should avoid any approach that tries to “mask” automation rather than reduce it[^2].

The report details a compliance-first blueprint: prioritize low-volume, high-signal targeting; pace operations with jitter and adaptive backoff; monitor GitHub’s rate-limit and error surfaces; and institutionalize stop conditions. It also surveys community tools and scripts to illustrate patterns and risks, and it codifies operational controls—such as scope minimization, idempotency, and audit logging—that align with GitHub’s Terms of Service and Acceptable Use Policies[^10][^3].

Information gaps remain: GitHub does not publish per-action quotas for follow/unfollow; the web UI has no documented automation policy or explicit thresholds; comprehensive academic treatment of GitHub follow/unfollow behavior is limited; detection heuristics and enforcement thresholds are undisclosed; and there is no official guidance on browser automation against UI endpoints. Where evidence is sparse, the report uses official documentation and observed tool behaviors as the basis for conservative recommendations, and it flags uncertainties explicitly.

## Platform Capabilities and Limits (API vs Web UI)

GitHub exposes follower and following data and mutating follow/unfollow operations via the REST API. The same actions can be performed manually in the web UI, but there is no official automation许可 for UI endpoints. Understanding endpoint capabilities, authentication requirements, and response semantics is foundational to any compliant design[^1].

### REST Endpoints for Followers/Following

The REST API provides read and write operations related to followers and following. The key endpoints include:

- List the followers of the authenticated user: GET /user/followers
- List the people the authenticated user follows: GET /user/following
- Check if the authenticated user follows a specific person: GET /user/following/{username}
- Follow a user: PUT /user/following/{username} (requires user:follow scope; Content-Length must be zero)
- Unfollow a user: DELETE /user/following/{username} (requires user:follow scope)
- List followers/following of any user: GET /users/{username}/followers and GET /users/{username}/following (read-only, can be unauthenticated)
- Check if one user follows another: GET /users/{username}/following/{target_user} (read-only)

Authentication and scopes govern mutability. For mutating operations, tokens must include the user:follow scope or equivalent Fine-Grained Personal Access Token (PAT) permissions. Read operations against public resources can be unauthenticated but benefit from authentication when higher rate limits or conditional requests are desired. Typical response codes include 204 (No Content) for successful follow/unfollow, 404 (Not Found) when a user does not exist or a follow relationship is absent, and 422 (Unprocessable Entity) when validation fails or the endpoint has been spam-flagged[^1].

To anchor the scope and mechanics, the following summary synthesizes endpoint details and required scopes.

Table 1. Followers/Following Endpoints Summary

| Operation                                       | HTTP Method | Endpoint                          | Required Scope/Permissions        | Typical Response Codes              |
|-------------------------------------------------|-------------|-----------------------------------|-----------------------------------|-------------------------------------|
| List authenticated user’s followers             | GET         | /user/followers                   | Authenticated; read access        | 200 (OK), 304 (Not Modified)        |
| List people the authenticated user follows      | GET         | /user/following                   | Authenticated; read access        | 200, 304                            |
| Check if authenticated user follows username    | GET         | /user/following/{username}        | Authenticated; read access        | 204 (yes), 404 (no)                 |
| Follow a user                                   | PUT         | /user/following/{username}        | user:follow (write)               | 204, 304, 401, 403, 404, 422        |
| Unfollow a user                                 | DELETE      | /user/following/{username}        | user:follow (write)               | 204, 304, 401, 403, 404             |
| List a user’s followers                         | GET         | /users/{username}/followers       | None for public reads             | 200                                 |
| List who a user follows                         | GET         | /users/{username}/following       | None for public reads             | 200                                 |
| Check if user follows target_user               | GET         | /users/{username}/following/{tgt} | None for public reads             | 204 (yes), 404 (no)                 |

Mutations must set Content-Length to zero for PUT follow requests and handle error cases with precise idempotency and backoff logic[^1]. The API version referenced is 2022-11-28, and clients should plan for change management by tracking official documentation updates[^1].

### Rate Limits Overview

GitHub’s REST API is governed by primary rate limits that vary by authentication and plan. Unauthenticated requests are more constrained; authenticated requests generally receive higher allowances. Changes continue to roll out, including tighter constraints for unauthenticated access and behavior around timeouts and 429 (Too Many Requests) responses[^2][^7][^8].

Practitioners should design clients to:

- Authenticate whenever possible to benefit from higher limits.
- Avoid concurrent bursts and apply jittered pacing between mutating calls.
- Handle 429 with exponential backoff and respect Retry-After headers.
- Use conditional requests (ETags/If-None-Match) to reduce read load and conserve rate-limit budget.
- Avoid polling; prefer event-driven workflows where feasible.

The following table provides an operational overview.

Table 2. Rate Limit Overview and Client Behaviors

| Auth Context                      | Typical Limit Posture           | Client Behavior Requirements                                                                                 |
|----------------------------------|---------------------------------|--------------------------------------------------------------------------------------------------------------|
| Unauthenticated                  | Tight constraints; changes in 2025 | Prefer authenticated calls; avoid heavy reads; anticipate stricter limits and 429 responses[^7].             |
| Authenticated (personal)         | Higher allowances               | Pace calls; avoid bursts; implement adaptive backoff and conditional requests; handle 429 and timeouts[^2][^8]. |
| Enterprise/Installation contexts | Plan-specific limits            | Consult plan docs; apply standard backoff and monitoring; validate behaviors under organizational policy.    |

Two policy changes are particularly relevant to automation design. First, unauthenticated rate limits have been tightened, reducing the viability of unauthenticated scraping or bulk reads as part of any automation. Second, request timeouts are now counted against the primary rate limit, which means poorly tuned clients that experience frequent network-level timeouts can inadvertently exhaust their own budgets[^7][^8]. Read and write calls should be orchestrated to avoid synchronization and “thundering herd” effects, especially in multi-worker systems[^2].

### Web UI Capabilities (Scripts/Tampermonkey)

Community scripts demonstrate that the web UI can be manipulated programmatically by clicking visible “Follow/Unfollow” buttons. A representative Tampermonkey userscript inserts “Follow All” and “Unfollow All” buttons on profile, followers, and following pages. It sequentially clicks input elements corresponding to Follow/Unfollow actions with a fixed delay (e.g., 1500 milliseconds) and updates a progress counter. The script notes that it only acts on visible elements, so users must scroll to load more items on infinite scroll pages. The repository includes explicit warnings that users bear all risk of rate limiting, blocking, or banning[^4].

These scripts are illustrative rather than prescriptive. There is no official automation许可 for UI endpoints, and the design pattern—fixed delays, batch clicking, page reload—carries detection and enforcement risk. This report does not recommend UI automation. If teams choose to experiment for research purposes, they must adopt stringent pacing, human-like variability, and immediate stop conditions, and they must accept that GitHub’s detection and enforcement posture for UI automation is not publicly documented and may change without notice.

## Compliance and Risk Posture

GitHub’s Acceptable Use Policies (AUP) prohibit excessive automated bulk activity, inauthentic interactions, and rank abuse, including automated starring or following. The Terms of Service (ToS) authorize suspension or termination for violations and give GitHub discretion to manage abuse that degrades platform integrity[^3][^10]. Even activities that might seem benign—such as mass following and quick unfollowing to manufacture reciprocity—fall within prohibited categories if they are automated, coordinated, or excessive.

Risk manifests through several signals: HTTP 403 (Forbidden), HTTP 422 (Unprocessable Entity, including spam flags), HTTP 429 (Too Many Requests), and unusual rate-limit responses. While not exhaustive, these signals are reliable indicators that either the rate-limit budget is stressed or the platform is gating suspected automation or abuse. Mitigation requires a compliance-first posture: reduce volume, slow pacing, eliminate bulk patterns, and incorporate adaptive controls.

Table 3. Compliance Risk Mapping

| Behavior Category            | Risk Level | Relevant Policy Clauses (summary)                                                       | Typical Triggers/Signals                             |
|-----------------------------|------------|----------------------------------------------------------------------------------------|------------------------------------------------------|
| Automated mass following    | High       | AUP: excessive bulk activity; rank abuse (automated following)                          | 422 (spam/validation), 429, sudden drop in success   |
| Coordinated follow/unfollow | High       | AUP: coordinated inauthentic activity                                                   | Repeated spikes synchronized across accounts         |
| High-frequency unfollows    | Medium     | AUP: excessive automated bulk activity                                                  | 403, 429, regular 404 on attempted deletions         |
| Scraping lists at scale     | Medium     | AUP: scraping restrictions; ToS: server burden prohibitions                             | Heavy reads without authentication; timeouts counted[^8] |
| Inauthentic engagement      | High       | AUP: inauthentic interactions; rank abuse                                               | Complaints; anomalous patterns; sudden reversals     |

Operationally, leaders should adopt a risk register that is reviewed periodically, with clear accountability and stop conditions.

Table 4. Operational Risk Register

| Risk                                     | Likelihood | Impact  | Mitigation                                                         | Owner            |
|------------------------------------------|------------|---------|--------------------------------------------------------------------|------------------|
| Enforcement action (suspension/ban)      | Medium     | High    | Compliance-first design; strict quotas; audit logging; stop rules | Eng Lead         |
| Rate-limit exhaustion                    | Medium     | Medium  | Pacing/jitter; conditional requests; adaptive backoff             | DevOps           |
| Reputation damage (perceived spammy行为) | Medium     | Medium  | Low-volume targeting; human-like timing; avoid bulk operations    | Community Mgr    |
| Data privacy incident (tokens/logs)      | Low        | High    | Secure token storage; least privilege; redact logs                | Security         |
| Tool misuse by operators                 | Medium     | Medium  | Training; approvals; automated guards; preflight checks           | Program Manager  |

## Safe Rate Limits and Operational Envelopes

GitHub’s documentation defines primary rate limits and recommended client behaviors but does not publish per-action quotas for follow/unfollow. Accordingly, “safe” operation must be inferred from documented general limits, error semantics, and prudent pacing[^2][^8]. For read operations, use conditional requests and avoid polling. For mutating operations, limit concurrency, vary timings with jitter, and stop on any enforcement signal.

In the absence of official numbers, we recommend limits framed as operating principles rather than fixed counts. The following table codifies these practices and the rationale behind them.

Table 5. Recommended Rate-Control Patterns

| Control                     | Recommended Practice                                            | Rationale                                                                                   |
|----------------------------|------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| Burst size (per action)    | Keep small; avoid “all at once” patterns                         | Reduces detection risk and rate-limit spikes                                                |
| Concurrency                | Avoid parallel mutating calls; serialize with jitter             | Prevents synchronized spikes that resemble automation                                       |
| Pacing                     | Use adaptive delays with jitter; avoid fixed intervals           | Human-like variability; lower correlation with bots                                         |
| Reads vs writes            | Batch reads with conditional requests; minimize write frequency  | Conserve rate-limit budget; avoid unnecessary mutations                                     |
| Backoff strategy           | Exponential backoff on 429/422; respect Retry-After              | Aligns with platform guidance; prevents hammering                                           |
| Error handling             | Treat 422 as a hard stop; log and investigate; do not retry blindly | 422 can indicate spam/validation issues; retrying may escalate enforcement[^1]             |
| Monitoring                 | Track rate-limit headers; error rates; throughput; anomalies     | Early warning system; supports adaptive control                                             |

Table 6. Error-Handling Playbook

| Signal                         | Meaning (indicative)                           | Immediate Action                                      | Next Steps                                               |
|-------------------------------|------------------------------------------------|--------------------------------------------------------|----------------------------------------------------------|
| 204 No Content                | Success (follow/unfollow)                      | Record audit log; continue                            | Monitor next batch for anomalies                         |
| 404 Not Found                 | User not found or relationship absent          | Stop action; mark as idempotent success               | Validate targets; update queue                           |
| 422 Unprocessable Entity      | Validation failed or spam flag                 | Hard stop on batch; log details; alert operators      | Reduce scope; slow pacing; investigate root cause[^1]    |
| 403 Forbidden                 | Access denied or policy gate                   | Stop; verify scopes/permissions                        | Review token scopes and policies                         |
| 429 Too Many Requests         | Rate limit exceeded                            | Back off; respect Retry-After; slow schedule          | Improve pacing; check for synchronized bursts[^2][^8]    |

These controls reflect the best practices articulated by GitHub and the need to avoid behaviors associated with rank abuse or excessive bulk activity[^2][^3]. If a client observes a 422 after a follow attempt, it should stop further follow actions, record context (timestamp, token, targets), and escalate rather than retry, as the endpoint may have been flagged for spam[^1].

## Human-Like Behavioral Patterns

Human-like behavior is less about faking inputs and more about removing automation signatures. Developers typically follow selectively, in small bursts, at varied times, with context such as repository activity or mutual projects. Unfollowing also has recognizable temporal patterns: people are more likely to unfollow accounts with low activity or low programming language similarity, and unfollow waves often follow periods of low engagement[^12]. 

To design systems that behave like responsible humans:

- Pace actions with randomness and daily/weekly rhythms, not fixed intervals.
- Perform small, purposeful batches with contextual justification (e.g., following contributors to a project you starred).
- Avoid synchronized bursts across multiple accounts.
- For UI experiments, use realistic interaction patterns (e.g., scrolling, reading, pausing) rather than only programmatic clicking; this is mentioned to contextualize risks, not to recommend UI automation.

Table 7. Heuristic Behavioral Guards

| Action Type | Batch Size Guidance         | Daily/Weekly Rhythm                      | Cool-down Rules                                  |
|-------------|-----------------------------|------------------------------------------|--------------------------------------------------|
| Follow      | Very small; context-driven  | Spread across day/week; avoid peaks      | Mandatory cool-down after any enforcement signal |
| Unfollow    | Very small; targeted        | Avoid waves; tie to low-similarity scores| Mandatory cool-down after 422/429                |

The academic work on unfollowing behavior provides a useful anchor: developers tend to unfollow those with fewer activities and lower programming language similarity. Automation that ignores these signals is more likely to appear inorganic and trigger enforcement[^12].

## Auto-Follow Queues and Timing Strategies

Automation that must be attempted should be orchestrated through a queue that enforces deterministic pacing, prioritization, and idempotency. A compliant design emphasizes high-signal targets (e.g., collaborators on projects you actively support) and includes robust guardrails: concurrency caps, adaptive delays, and backoff.

Table 8. Queue Configuration Blueprint

| Parameter          | Recommended Setting                                  | Rationale                                                             |
|--------------------|------------------------------------------------------|------------------------------------------------------------------------|
| Concurrency cap    | 1 for mutating actions; no parallelism               | Avoid synchronized spikes; align with low-rate patterns                |
| Prioritization     | High-signal targets first (e.g., project collaborators)| Maximize relevance; minimize bulk risk                                 |
| Batch size         | Very small (single-digit actions per batch)          | Reduce automation signature; allow monitoring to catch anomalies       |
| Delays             | Jittered; adaptive based on error rates              | Human-like variability; reduce correlation with bots                   |
| Backoff            | Exponential on 429/422; honor Retry-After            | Platform alignment; prevent hammering[^2]                              |
| Idempotency        | Deduplicate targets; safe retries on reads           | Prevent duplicate actions; avoid unnecessary mutations                 |
| Stop conditions    | Any 422, sudden error spike, or rate-limit stress    | Compliance-first; immediate de-escalation                              |
| Audit logging      | Structured logs; minimal data retention              | Accountability; privacy preservation                                   |

Community scripts that auto-follow or unfollow often use fixed delays (e.g., 1500 milliseconds between button clicks). While such scripts illustrate pacing, their fixed intervals are suboptimal. Adaptive delays with jitter outperform fixed pacing because they avoid regularity that detection systems may correlate with automation[^4].

Table 9. Scheduling Strategies Comparison

| Strategy                       | Pros                                         | Cons                                           | Compliance Fit |
|-------------------------------|----------------------------------------------|------------------------------------------------|----------------|
| Fixed-interval (e.g., 1.5s)   | Simple to implement                           | Regularity resembles bot patterns; rigid       | Low            |
| Jittered delays               | Reduces regularity; tunable variability       | Still requires careful tuning                  | Medium         |
| Event-driven bursts           | Aligns with real activity; avoids periodic patterns | Requires event sourcing; more complex           | High           |

## Follow-Back Detection and Unfollow Logic

Follow-back detection on GitHub can be implemented safely via the REST API by comparing two sets: the list of accounts you follow and the list of your followers. Users who appear in “following” but not in “followers” are candidates for review. Authentication with PAT (Personal Access Token) or Fine-Grained tokens is required for read/write operations, and pagination should be used to handle large lists (per_page up to 100)[^1].

Two community tools illustrate common detection approaches. One tool compares your “following” and “followers” lists to identify non-reciprocal follows and can handle large accounts using locally stored tokens; it is designed for analysis rather than continuous monitoring[^5]. Another approach fetches both lists via the API and prints results to the console, optionally separating reciprocal from non-reciprocal follows, and can be run manually or with external scheduling[^6]. These tools demonstrate reliable detection logic and safe token usage patterns—namely, storing tokens locally, minimizing scopes, and avoiding server-side collection of user data.

Unfollow logic should prioritize targets based on explicit criteria and a defined schedule. Academic evidence suggests prioritizing accounts with low activity and low programming language similarity, and avoiding unfollow “waves” that look automated. A straightforward prioritization scheme is to rank non-reciprocal follows by last activity (ascending) and language similarity (ascending), then unfollow in small, spaced batches with mandatory cool-downs after any error spike[^12].

Table 10. Detection Signals and Actions

| Criterion                              | Data Source                     | Action Rule                                                       |
|----------------------------------------|----------------------------------|-------------------------------------------------------------------|
| Not following back                      | Set difference: following vs followers | Flag for review; do not auto-unfollow without additional context |
| Low activity                            | Public profile/repo activity     | Add to low-priority unfollow list                                 |
| Low programming language similarity     | Repo language metadata           | Add to unfollow list (moderate priority)                          |
| High relevance (mutual projects)        | Repo contributions/starring      | Keep follow; re-evaluate periodically                            |
| Recent unfollow attempts by target      | Observed changes                 | Add cool-down; avoid repeated toggling                            |

Table 11. Unfollow Prioritization and Safeguards

| Risk Level | Prioritization Rule                                        | Safeguards                                      |
|------------|------------------------------------------------------------|-------------------------------------------------|
| Low        | High-similarity; active collaborators                      | No unfollow; keep under observation             |
| Medium     | Medium activity; moderate similarity                       | Unfollow in small batches with jitter           |
| High       | Low activity; low similarity; no recent interactions       | Unfollow in very small batches; mandatory cool-downs |

## Non-Detectable Automation Techniques: Feasibility and Ethics

The web ecosystem increasingly uses browser-side bot detection libraries and behavioral analytics to identify automation. For example, BotD can detect common automation toolkits in the browser, and commercial providers have documented the sophistication of modern bot frameworks and evasion tools[^9][^13]. This reality argues for minimizing automation footprint rather than attempting to “evade” detection.

Recommended practices are pragmatic and compliance-oriented:

- Prefer the REST API over UI automation; authenticate and pace calls; avoid bursts; and handle errors deterministically[^2].
- Reduce volume drastically; avoid coordinated actions across accounts; and prioritize high-signal targeting.
- Avoid proxy rotation and fingerprint spoofing in the context of GitHub automation. These tactics carry legal and ethical risk and may conflict with platform policies and organizational standards.
- Establish hard stop conditions, audit logging, and least-privilege scopes for tokens; use multi-factor authentication (MFA) and secure storage.

Table 12. Risk–Benefit Trade-offs

| Approach                            | Benefit Claimed                         | Detection/Enforcement Risk                    | Policy Risk                        | Recommendation              |
|-------------------------------------|-----------------------------------------|-----------------------------------------------|------------------------------------|-----------------------------|
| REST API with strict pacing         | Stable; documented; higher rate limits  | Lower, if paced and monitored                  | Lower, if compliant with AUP/ToS   | Acceptable (compliant)      |
| UI automation with fixed delays     | Rapid execution                         | Medium–High; regular patterns visible          | High; no official许可               | Not recommended             |
| Proxy/fingerprint evasion           | “Stealth”                               | High; strong anti-bot systems                  | High; ethical/legal concerns       | Avoid                       |

The core principle is simple: if your automation looks like a human’s normal use of the platform, it is less likely to trigger enforcement. If it looks like a bulk, coordinated, or evasive operation, it is more likely to do so.

## Implementation Patterns and Sample Workflows

Two workflow patterns are instructive: a compliant API pipeline and a UI-script pattern with explicit warnings.

Compliant API pipeline:
1. Authenticate with least privilege scopes (user:follow for mutations; read-only scopes for analysis).
2. Discover targets using read endpoints and pagination (per_page up to 100); store minimal metadata.
3. Run follow/unfollow operations in small batches with jittered delays.
4. Handle responses deterministically: stop on 422, back off on 429, treat 404 as idempotent success.
5. Log audit records with minimal data and secure token storage; rotate tokens periodically.
6. Monitor rate-limit headers and error rates; adjust pacing adaptively[^1][^2].

UI-script pattern:
- A Tampermonkey userscript inserts “Follow All/Unfollow All” buttons, clicks visible inputs with fixed delays, and shows a live counter. It warns users about rate limiting and banning risks and requires manual scrolling on infinite lists[^4].

Table 13. Workflow Step Map (API Pipeline)

| Step                       | Inputs                             | API Calls                                   | Outputs                                | Guardrails                                          |
|----------------------------|-------------------------------------|----------------------------------------------|-----------------------------------------|-----------------------------------------------------|
| Authenticate               | Token with least privilege          | N/A                                          | Authenticated session                   | user:follow only for mutations; secure storage[^1]  |
| Discover targets           | Curated lists; pagination           | GET /users/{username}/following/followers    | Sets of targets                         | Conditional requests; avoid polling[^2]             |
| Follow batch               | Small, prioritized set              | PUT /user/following/{username} (per target)  | 204/404/422 responses                   | Jitter; stop on 422                                 |
| Unfollow batch             | Prioritized non-reciprocal list     | DELETE /user/following/{username} (per tgt)  | 204/404/403 responses                   | Exponential backoff; audit logs                     |
| Monitor and adapt          | Rate-limit headers; error rates     | N/A                                          | Adjusted pacing                         | Honor Retry-After; reduce concurrency[^2][^8]       |

Table 14. UI-Script Risk Profile

| Pattern                    | Detection Likelihood | Policy Risk                    | Mitigation Options (limited)                   |
|---------------------------|----------------------|--------------------------------|-----------------------------------------------|
| Fixed 1.5s click delays   | Medium–High          | High; no automation许可         | Increase variability; reduce batch size; stop on signals |
| Page reload on completion | Medium               | Medium–High                    | Manual review; avoid automation altogether     |

## Monitoring, Metrics, and Operational Controls

Compliant automation requires continuous monitoring and adaptive control. Track rate-limit headers (including primary limits and search-specific limits where relevant), HTTP error rates (422, 429, 403), action throughput, and anomalies in follow-back ratios. GitHub’s rate-limit endpoints and best-practice guidance emphasize conditional requests, backoff, and avoiding concurrency[^2][^14].

Alerts and dashboards should be configured to trigger on backoff events, sudden throughput drops, and any 422 occurrences, which can indicate spam flags. Key performance indicators (KPIs) should be framed to encourage quality over quantity. Adoption of an error budget helps bound risk exposure.

Table 15. Operational KPI Catalog

| KPI                           | Definition                                         | Target Posture                                  | Alert Thresholds                                  |
|-------------------------------|----------------------------------------------------|--------------------------------------------------|---------------------------------------------------|
| Follow-back ratio             | Followers / following                              | Stable, modest growth over time                  | Sharp drops; sudden anomalies                     |
| 422 rate                      | 422 responses per 100 follow attempts              | Near zero                                       | Any occurrence triggers alert                     |
| 429 rate                      | 429 responses per 100 requests                     | Low; declining with adaptive pacing              | Exceeds baseline by set margin                    |
| Action throughput             | Successful actions per hour                        | Smooth, low-volume                               | Spikes or sudden drops                            |
| Audit coverage                | % of actions logged with minimal metadata          | 100%                                             | Any gaps                                         |

Table 16. Monitoring Dashboard Blueprint

| Data Source                  | Retention         | Access Control                 | Escalation Path                      |
|-----------------------------|-------------------|--------------------------------|--------------------------------------|
| API responses and headers   | Minimal (privacy) | Restricted (need-to-know)      | Eng Lead → Security → Legal          |
| Structured audit logs       | Short-term        | Restricted; redact tokens      | Eng Lead → Program Manager           |
| Rate-limit endpoints        | Real-time         | DevOps only                    | DevOps → Eng Lead                    |
| Error-rate aggregates       | Short-term        | Eng + DevOps                   | Eng Lead → Program Manager           |

## Appendix: Tooling Landscape and Quick-Start Patterns

The tooling landscape illustrates common detection patterns and UI-script risks. These tools are not endorsed; they serve as cautionary examples and sources of operational insight.

Table 17. Tooling Matrix

| Tool/Repo                                  | Purpose                          | Automation Surface       | Rate-Limiting Strategy               | Token Scope                | Last Updated | Notes/Limitations                                    |
|--------------------------------------------|----------------------------------|--------------------------|--------------------------------------|----------------------------|--------------|------------------------------------------------------|
| github-unfollower (web-based)              | Detect non-reciprocal follows    | REST API (reads)         | Paginated fetches; local token store | read:user (typical)        | 2025         | Safe design; analysis focus; not continuous[^5]      |
| Follow-Back Checker (article/script)       | Identify non-reciprocal follows  | REST API (reads)         | Paginated fetches; console output    | read:user (typical)        | 2024–2025    | Flexible execution; manual scheduling[^6]            |
| auto-github-follow-and-unfollow (userscript)| Auto follow/unfollow via UI     | Web UI (DOM clicks)      | Fixed 1500ms delay                   | N/A (UI actions)           | 2025         | Explicit warnings; high policy risk[^4]              |

For secure token handling, use Fine-Grained PATs with minimal scopes; store tokens securely; rotate them periodically; and never log full tokens. When using Marketplace or community Actions, validate that they do not perform bulk mutating operations and confirm their compliance with platform policies.

## References

[^1]: GitHub Docs. REST API endpoints for followers — GitHub Docs. https://docs.github.com/en/rest/users/followers  
[^2]: GitHub Docs. Rate limits for the REST API — GitHub Docs. https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api  
[^3]: GitHub Docs. GitHub Acceptable Use Policies. https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies  
[^4]: isyuricunha/auto-github-follow-and-unfollow — GitHub. https://github.com/isyuricunha/auto-github-follow-and-unfollow  
[^5]: nimakian/github-unfollower — GitHub. https://github.com/nimakian/github-unfollower  
[^6]: Dev.to. GitHub Follow-Back Checker: Find Who Hasn't Followed You Back. https://dev.to/vibhuvibes/github-follow-back-checker-find-who-hasnt-followed-you-back-15e0  
[^7]: GitHub Changelog. Updated rate limits for unauthenticated requests. https://github.blog/changelog/2025-05-08-updated-rate-limits-for-unauthenticated-requests/  
[^8]: GitHub Changelog. Including timeouts in primary rate limits. https://github.blog/changelog/2025-07-21-including-timeouts-in-primary-rate-limits/  
[^9]: GitHub Topics. anti-bot-detection — GitHub Topics. https://github.com/topics/anti-bot-detection  
[^10]: GitHub Docs. GitHub Terms of Service. https://docs.github.com/site-policy/github-terms/github-terms-of-service  
[^11]: GitHub Docs. Best practices for using the REST API — GitHub Docs. https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api  
[^12]: SOAR. A first look at unfollowing behavior on GitHub. https://soarsmu.github.io/papers/2019/Jiang2019UnfollowingBehavior.pdf  
[^13]: DataDome. The State of Bots 2024: Changes to the Bot Ecosystem. https://datadome.co/threat-research/the-state-of-bots-2024-changes-to-bot-ecosystem/  
[^14]: GitHub Docs. REST API endpoints for rate limits — GitHub Docs. https://docs.github.com/en/rest/rate-limit/rate-limit  
[^15]: GitHub Marketplace Actions. Auto Follows & Unfollows by Github Actions for Github users. https://github.com/marketplace/actions/auto-follows-unfollows-by-github-actions-for-github-users

---

Information gaps acknowledged:
- No official per-action quotas exist for follow/unfollow operations; safe rates must be inferred from general rate limits and observed signals.
- No explicit GitHub documentation defines automation policy or quotas for web UI actions; UI automation risk is inferred from acceptable use policies and observed behaviors.
- Academic literature specifically analyzing GitHub follow/unfollow behavior is limited; this report uses one study and general platform guidance as the evidence base.
- Detection heuristics and enforcement thresholds are not publicly documented.
- No official guidance exists on using browser automation against UI endpoints; UI scripts are community examples with explicit warnings.