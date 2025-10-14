# 🔄 Re-sync Guide: Get Proper Clickable Links

## Problem
You're seeing broken URLs like:
- `https://confluence.com/x/0a9859512ae446958f915f008e6bd031` (wrong)
- `https://git.com/414c423` (wrong)
- `https://code.go/internal/middleware/admin_auth.go` (wrong)

## Root Cause
Your data was synced **before** URL support was added. The old data has placeholder/incomplete URLs.

## Solution: Re-sync Your Data Sources

You need to re-sync your Jira and Repository to populate proper URLs.

---

## Step 1: Re-sync Jira Tickets

Go to the UI → **Jira Sync** tab and re-sync your project.

**What this does:**
- Fetches Jira tickets again
- Builds proper URLs like: `https://yourcompany.atlassian.net/browse/DEMO-001`
- Stores URLs in both PostgreSQL and Qdrant
- Overwrites old data with new data (same ticket_key)

**Expected URLs:**
- **Jira Cloud**: `https://yourcompany.atlassian.net/browse/TICKET-123`
- **Jira Server**: `https://jira.yourcompany.com/browse/TICKET-123`

---

## Step 2: Re-sync Repository

Go to the UI → **Repository Sync** tab and re-sync your repo.

**What this does:**
- Fetches commits and code files again
- GitHub/GitLab APIs provide proper URLs automatically
- Stores URLs in both PostgreSQL and Qdrant

**Expected URLs:**
- **Commits**: `https://github.com/owner/repo/commit/abc123def456`
- **Code Files**: `https://github.com/owner/repo/blob/main/path/to/file.py`
- **GitLab Commits**: `https://gitlab.com/owner/repo/-/commit/abc123`
- **GitLab Files**: `https://gitlab.com/owner/repo/-/blob/main/path/to/file.py`

---

## Step 3: Re-sync Confluence (If using)

Go to the UI → **Confluence Sync** tab and re-sync your space.

**Expected URLs:**
- **Confluence Cloud**: `https://yourcompany.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title`

**Note:** Confluence URL support will be added in a future update. For now, Confluence docs won't have clickable links.

---

## Step 4: Verify

After re-syncing, ask a question:

**Query:** "How does authentication work?"

**Expected Response:**
```markdown
User authentication is tracked in [[TICKET-1: DEMO-001](https://yourcompany.atlassian.net/browse/DEMO-001)],
implemented in [[COMMIT-2: abc123d](https://github.com/yourcompany/project/commit/abc123def456)],
and the code is in [[CODE-3: auth.go](https://github.com/yourcompany/project/blob/main/internal/middleware/auth.go)].
```

**Test the links:**
- Click `[TICKET-1: DEMO-001]` → Should open your Jira ticket
- Click `[COMMIT-2: abc123d]` → Should open GitHub/GitLab commit
- Click `[CODE-3: auth.go]` → Should open GitHub/GitLab file

---

## Alternative: Use Backfill (If you have many sources)

If you have many Jira projects or repositories and don't want to re-sync them all manually via UI, you can use the backfill endpoint after re-syncing at least one project/repo:

```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:4000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@acmecorp.com","password":"admin123"}' \
  | jq -r .access_token)

# Backfill (this won't help with URLs though - you need to re-sync sources)
curl -X POST http://localhost:4000/admin/backfill/qdrant \
  -H "Authorization: Bearer $TOKEN" | jq .
```

**Note:** Backfill **does NOT** fetch fresh data from Jira/GitHub. It only indexes existing PostgreSQL data into Qdrant. To get proper URLs, you **MUST re-sync** from the source (Jira, GitHub, etc.).

---

## Why This Happened

The URL support was added in these commits:
1. **Jira URLs**: Added `url` field to `jira_service.py` (line 100-102)
2. **Commit URLs**: Already available from GitHub API (`metadata.url`)
3. **Code File URLs**: Need to be constructed from repo URL + file path

Your existing data was synced **before** these changes, so it has:
- Missing URLs (empty strings)
- Placeholder URLs from test data
- Incorrect URL formats

---

## Quick Check: View Your Current Data

**Check Jira ticket URLs:**
```bash
TOKEN="your_token_here"

curl -X GET "http://localhost:4000/search/jira?query=authentication&limit=1" \
  -H "Authorization: Bearer $TOKEN" | jq '.results[0].url'
```

**Expected:**
- ✅ Good: `"https://yourcompany.atlassian.net/browse/DEMO-001"`
- ❌ Bad: `""` (empty) or `"https://jira.com/browse/DEMO-001"` (placeholder)

---

## Summary

**To fix broken links:**
1. ✅ Go to UI → Jira Sync → Re-sync your project
2. ✅ Go to UI → Repository Sync → Re-sync your repo
3. ✅ Ask a question and verify links are clickable
4. ✅ Clicks should navigate to actual Jira/GitHub pages

**This is a one-time operation.** Once re-synced, all future syncs will automatically include proper URLs.

---

## Still Having Issues?

If links are still broken after re-syncing:

1. **Check browser console** for errors
2. **Verify Jira/GitHub settings:**
   - Jira server URL is correct
   - GitHub repo URL is correct
   - API tokens have proper permissions
3. **Check API response:**
   ```bash
   # Ask a question and inspect the answer
   curl -X POST http://localhost:4000/ask \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"question":"test","model":"mistral"}' | jq '.answer'
   ```
   Look for markdown links in the format: `[[TICKET-1: KEY](https://...)]`

4. **Restart containers** if needed:
   ```bash
   docker compose restart api
   ```
