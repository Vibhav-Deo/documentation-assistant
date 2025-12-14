import requests
from typing import List, Dict, Optional
from datetime import datetime
import re
import base64


class JiraService:
    def __init__(self, server: str, email: str, api_token: str):
        """Initialize Jira client"""
        self.server = server.rstrip('/')
        self.email = email
        self.api_token = api_token
        
        # Create auth header
        auth_string = f"{email}:{api_token}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        self.headers = {
            'Authorization': f'Basic {auth_b64}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def sync_project(self, project_key: str) -> List[Dict]:
        """Sync all tickets from a Jira project with pagination"""

        # Test connection first
        if not self.test_connection():
            raise Exception("Failed to connect to Jira")

        # Use the correct v3 search/jql endpoint as specified in the error
        url = f"{self.server}/rest/api/3/search/jql"

        synced_tickets = []
        start_at = 0
        max_results = 100  # Fetch in batches of 100 (Jira's recommended batch size)
        total_issues = None

        # Pagination loop - fetch all tickets
        while True:
            params = {
                'jql': f'project = {project_key}',
                'startAt': start_at,
                'maxResults': max_results,
                'expand': 'changelog,renderedFields',
                'fields': '*all'
            }

            response = requests.get(url, headers=self.headers, params=params)

            if response.status_code != 200:
                print(f"Jira API Error: {response.status_code}")
                print(f"Response: {response.text}")

            response.raise_for_status()

            data = response.json()
            issues = data.get('issues', [])
            total_issues = data.get('total', 0)

            # Extract ticket data from this batch
            for issue in issues:
                ticket_data = self._extract_ticket_data(issue)
                synced_tickets.append(ticket_data)

            # Log progress
            print(f"Fetched {len(synced_tickets)}/{total_issues} tickets from {project_key}")

            # Check if we've fetched all tickets
            if len(synced_tickets) >= total_issues or len(issues) == 0:
                break

            # Move to next page
            start_at += max_results

        print(f"✅ Completed: Synced {len(synced_tickets)} tickets from {project_key}")
        return synced_tickets

    def _extract_ticket_data(self, issue: Dict) -> Dict:
        """Extract all relevant data from Jira ticket"""
        fields = issue.get('fields', {})
        
        # Extract comments
        comments = []
        comment_data = fields.get('comment', {}).get('comments', [])
        for comment in comment_data:
            comments.append({
                "author": comment.get('author', {}).get('displayName', 'Unknown'),
                "body": comment.get('body', ''),
                "created": comment.get('created', '')
            })

        # Extract changelog
        changelog = []
        changelog_data = issue.get('changelog', {}).get('histories', [])
        for history in changelog_data:
            for item in history.get('items', []):
                changelog.append({
                    "field": item.get('field', ''),
                    "from_value": item.get('fromString', ''),
                    "to_value": item.get('toString', ''),
                    "author": history.get('author', {}).get('displayName', 'Unknown'),
                    "created": history.get('created', '')
                })

        # Extract mentioned commits/PRs from description
        # Handle both string and dict formats for description
        description = fields.get('description', '')
        if isinstance(description, dict):
            # For v3 API, description might be in content format
            description = description.get('content', [{}])[0].get('content', [{}])[0].get('text', '') if description.get('content') else ''
        elif description is None:
            description = ''
        
        code_refs = self._extract_code_references(description) if description else []

        # Build Jira ticket URL
        ticket_key = issue.get('key', '')
        ticket_url = f"{self.server}/browse/{ticket_key}" if ticket_key else None

        return {
            "key": issue.get('key', ''),
            "summary": fields.get('summary', ''),
            "description": description,
            "issue_type": fields.get('issuetype', {}).get('name', ''),
            "status": fields.get('status', {}).get('name', ''),
            "priority": fields.get('priority', {}).get('name') if fields.get('priority') else None,
            "assignee": fields.get('assignee', {}).get('displayName') if fields.get('assignee') else None,
            "reporter": fields.get('reporter', {}).get('displayName') if fields.get('reporter') else None,
            "created": fields.get('created', ''),
            "updated": fields.get('updated', ''),
            "resolved": fields.get('resolutiondate'),
            "story_points": fields.get('customfield_10016'),  # May vary
            "labels": fields.get('labels', []),
            "components": [c.get('name', '') for c in fields.get('components', [])],
            "url": ticket_url,  # Add URL for clickable links
            "metadata": {
                "comments": comments,
                "changelog": changelog,
                "code_references": code_refs
            }
        }

    def _extract_code_references(self, text: str) -> List[str]:
        """Extract GitHub PR/commit references from text"""
        if not text:
            return []

        # Patterns: #123, PR-123, commit abc123, github.com/org/repo/pull/123
        patterns = [
            r'#(\d+)',
            r'PR[- ](\d+)',
            r'commit[s]?\s+([a-f0-9]{7,40})',
            r'github\.com/[\w-]+/[\w-]+/pull/(\d+)'
        ]

        references = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            references.extend(matches)

        return list(set(references))

    def test_connection(self) -> bool:
        """Test if Jira connection is working"""
        try:
            url = f"{self.server}/rest/api/3/myself"
            response = requests.get(url, headers=self.headers)
            print(f"Connection test: {response.status_code}")
            if response.status_code != 200:
                print(f"Connection error: {response.text}")
            return response.status_code == 200
        except Exception as e:
            print(f"Connection exception: {e}")
            return False

    def get_projects(self) -> List[Dict]:
        """Get all accessible projects"""
        try:
            url = f"{self.server}/rest/api/3/project"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            projects = response.json()
            return [
                {
                    "key": p.get('key', ''),
                    "name": p.get('name', ''),
                    "lead": p.get('lead', {}).get('displayName') if p.get('lead') else None
                }
                for p in projects
            ]
        except Exception:
            return []
