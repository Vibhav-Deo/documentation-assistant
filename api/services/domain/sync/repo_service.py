import requests
import base64
import re
from typing import List, Dict, Tuple, Optional
from fastapi import HTTPException

class RepositoryService:
    """Service for syncing code repositories (GitHub, GitLab, Bitbucket)"""

    def __init__(self, provider: str, repo_url: str, access_token: str, branch: str = "main"):
        self.provider = provider.lower()
        self.repo_url = repo_url
        self.access_token = access_token
        self.branch = branch
        self.api_base = self._get_api_base()
        self.owner, self.repo = self._parse_repo_url()

    def _get_api_base(self) -> str:
        """Get API base URL based on provider"""
        if self.provider == "github":
            return "https://api.github.com"
        elif self.provider == "gitlab":
            return "https://gitlab.com/api/v4"
        elif self.provider == "bitbucket":
            return "https://api.bitbucket.org/2.0"
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {self.provider}")

    def _parse_repo_url(self) -> Tuple[str, str]:
        """Parse repository URL to extract owner and repo name"""
        # Support formats:
        # https://github.com/owner/repo
        # https://github.com/owner/repo.git
        # git@github.com:owner/repo.git
        patterns = [
            r'github\.com[:/]([^/]+)/([^/\.]+)',
            r'gitlab\.com[:/]([^/]+)/([^/\.]+)',
            r'bitbucket\.org[:/]([^/]+)/([^/\.]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, self.repo_url)
            if match:
                return match.group(1), match.group(2)

        raise HTTPException(status_code=400, detail="Invalid repository URL format")

    def test_connection(self) -> bool:
        """Test if connection to repository is valid"""
        try:
            if self.provider == "github":
                url = f"{self.api_base}/repos/{self.owner}/{self.repo}"
                headers = {
                    "Authorization": f"token {self.access_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            elif self.provider == "gitlab":
                # GitLab project ID format: owner%2Frepo
                project_id = f"{self.owner}%2F{self.repo}"
                url = f"{self.api_base}/projects/{project_id}"
                headers = {"PRIVATE-TOKEN": self.access_token}
            elif self.provider == "bitbucket":
                url = f"{self.api_base}/repositories/{self.owner}/{self.repo}"
                headers = {"Authorization": f"Bearer {self.access_token}"}

            r = requests.get(url, headers=headers, timeout=10)
            return r.status_code == 200
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False

    def get_file_tree(self) -> List[Dict]:
        """Get list of all files in repository"""
        if self.provider == "github":
            return self._github_get_tree()
        elif self.provider == "gitlab":
            return self._gitlab_get_tree()
        elif self.provider == "bitbucket":
            return self._bitbucket_get_tree()

    def _github_get_tree(self) -> List[Dict]:
        """Get file tree from GitHub"""
        url = f"{self.api_base}/repos/{self.owner}/{self.repo}/git/trees/{self.branch}?recursive=1"
        headers = {
            "Authorization": f"token {self.access_token}",
            "Accept": "application/vnd.github.v3+json"
        }

        try:
            r = requests.get(url, headers=headers, timeout=30)
            r.raise_for_status()
            data = r.json()

            # Filter only files (not directories) and code files
            files = []
            for item in data.get('tree', []):
                if item['type'] == 'blob' and self._is_code_file(item['path']):
                    files.append({
                        'path': item['path'],
                        'sha': item['sha'],
                        'size': item.get('size', 0),
                        'url': item.get('url')
                    })
            return files
        except requests.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch file tree: {str(e)}")

    def _gitlab_get_tree(self) -> List[Dict]:
        """Get file tree from GitLab"""
        project_id = f"{self.owner}%2F{self.repo}"
        url = f"{self.api_base}/projects/{project_id}/repository/tree?ref={self.branch}&recursive=true&per_page=100"
        headers = {"PRIVATE-TOKEN": self.access_token}

        try:
            files = []
            while url:
                r = requests.get(url, headers=headers, timeout=30)
                r.raise_for_status()
                data = r.json()

                for item in data:
                    if item['type'] == 'blob' and self._is_code_file(item['path']):
                        files.append({
                            'path': item['path'],
                            'id': item['id'],
                            'name': item['name']
                        })

                # Check for next page
                if 'next' in r.links:
                    url = r.links['next']['url']
                else:
                    url = None

            return files
        except requests.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch file tree: {str(e)}")

    def _bitbucket_get_tree(self) -> List[Dict]:
        """Get file tree from Bitbucket"""
        url = f"{self.api_base}/repositories/{self.owner}/{self.repo}/src/{self.branch}/?pagelen=100"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        try:
            files = []
            # Bitbucket API is paginated
            while url:
                r = requests.get(url, headers=headers, timeout=30)
                r.raise_for_status()
                data = r.json()

                for item in data.get('values', []):
                    if item.get('type') == 'commit_file' and self._is_code_file(item['path']):
                        files.append({
                            'path': item['path'],
                            'size': item.get('size', 0)
                        })

                url = data.get('next')  # Next page URL

            return files
        except requests.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch file tree: {str(e)}")

    def _is_code_file(self, path: str) -> bool:
        """Check if file is a code file we want to index"""
        code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs', '.cpp', '.c', '.h',
            '.cs', '.rb', '.php', '.swift', '.kt', '.scala', '.sh', '.bash', '.sql',
            '.html', '.css', '.scss', '.yaml', '.yml', '.json', '.xml', '.md', '.txt'
        }

        # Skip common non-code directories
        skip_dirs = {
            'node_modules', '.git', '__pycache__', 'dist', 'build', '.next',
            'venv', 'env', '.venv', 'vendor', 'target', 'bin', 'obj'
        }

        for skip_dir in skip_dirs:
            if f'/{skip_dir}/' in path or path.startswith(f'{skip_dir}/'):
                return False

        return any(path.endswith(ext) for ext in code_extensions)

    def get_file_content(self, file_path: str) -> Tuple[str, Dict]:
        """Get content of a specific file"""
        if self.provider == "github":
            return self._github_get_content(file_path)
        elif self.provider == "gitlab":
            return self._gitlab_get_content(file_path)
        elif self.provider == "bitbucket":
            return self._bitbucket_get_content(file_path)

    def _github_get_content(self, file_path: str) -> Tuple[str, Dict]:
        """Get file content from GitHub"""
        url = f"{self.api_base}/repos/{self.owner}/{self.repo}/contents/{file_path}?ref={self.branch}"
        headers = {
            "Authorization": f"token {self.access_token}",
            "Accept": "application/vnd.github.v3+json"
        }

        try:
            r = requests.get(url, headers=headers, timeout=30)
            r.raise_for_status()
            data = r.json()

            # Decode base64 content
            content = base64.b64decode(data['content']).decode('utf-8', errors='ignore')

            metadata = {
                'sha': data['sha'],
                'size': data['size'],
                'url': data['html_url']
            }

            return content, metadata
        except Exception as e:
            print(f"Failed to fetch {file_path}: {e}")
            return "", {}

    def _gitlab_get_content(self, file_path: str) -> Tuple[str, Dict]:
        """Get file content from GitLab"""
        project_id = f"{self.owner}%2F{self.repo}"
        # URL encode the file path
        encoded_path = requests.utils.quote(file_path, safe='')
        url = f"{self.api_base}/projects/{project_id}/repository/files/{encoded_path}/raw?ref={self.branch}"
        headers = {"PRIVATE-TOKEN": self.access_token}

        try:
            r = requests.get(url, headers=headers, timeout=30)
            r.raise_for_status()
            content = r.text

            metadata = {
                'file_path': file_path,
                'ref': self.branch
            }

            return content, metadata
        except Exception as e:
            print(f"Failed to fetch {file_path}: {e}")
            return "", {}

    def _bitbucket_get_content(self, file_path: str) -> Tuple[str, Dict]:
        """Get file content from Bitbucket"""
        url = f"{self.api_base}/repositories/{self.owner}/{self.repo}/src/{self.branch}/{file_path}"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        try:
            r = requests.get(url, headers=headers, timeout=30)
            r.raise_for_status()
            content = r.text

            metadata = {
                'file_path': file_path,
                'branch': self.branch
            }

            return content, metadata
        except Exception as e:
            print(f"Failed to fetch {file_path}: {e}")
            return "", {}

    def parse_code_file(self, content: str, file_path: str) -> Dict:
        """Parse code file to extract functions, classes, imports"""
        file_ext = file_path.split('.')[-1] if '.' in file_path else ''
        language = self._detect_language(file_ext)

        data = {
            'file_type': file_ext,
            'language': language,
            'line_count': len(content.split('\n')),
            'functions': [],
            'classes': [],
            'imports': []
        }

        # Basic parsing for Python files
        if language == 'python':
            data['functions'] = re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', content)
            data['classes'] = re.findall(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[\(:]', content)
            data['imports'] = re.findall(r'(?:from\s+[\w\.]+\s+)?import\s+([\w\.,\s]+)', content)

        # Basic parsing for JavaScript/TypeScript
        elif language in ['javascript', 'typescript']:
            data['functions'] = re.findall(r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', content)
            data['functions'] += re.findall(r'const\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\([^)]*\)\s*=>', content)
            data['classes'] = re.findall(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)', content)
            data['imports'] = re.findall(r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]', content)

        # Basic parsing for Java
        elif language == 'java':
            data['functions'] = re.findall(r'(?:public|private|protected)?\s+(?:static\s+)?[\w<>\[\]]+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', content)
            data['classes'] = re.findall(r'(?:public\s+)?class\s+([a-zA-Z_][a-zA-Z0-9_]*)', content)
            data['imports'] = re.findall(r'import\s+([\w\.]+);', content)

        return data

    def _detect_language(self, ext: str) -> str:
        """Detect programming language from file extension"""
        lang_map = {
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'jsx': 'javascript',
            'tsx': 'typescript',
            'java': 'java',
            'go': 'go',
            'rs': 'rust',
            'cpp': 'cpp',
            'c': 'c',
            'h': 'c',
            'cs': 'csharp',
            'rb': 'ruby',
            'php': 'php',
            'swift': 'swift',
            'kt': 'kotlin',
            'scala': 'scala',
            'sh': 'bash',
            'bash': 'bash',
            'sql': 'sql',
            'html': 'html',
            'css': 'css',
            'scss': 'scss',
            'yaml': 'yaml',
            'yml': 'yaml',
            'json': 'json',
            'xml': 'xml',
            'md': 'markdown'
        }
        return lang_map.get(ext.lower(), 'unknown')

    def sync_repository(self, max_files: Optional[int] = None) -> List[Dict]:
        """Sync repository and return file data (NO LIMITS - syncs all files)"""
        files = self.get_file_tree()

        # NO LIMITS - sync all files in repository
        total_files = len(files)
        print(f"📊 Repository has {total_files} code files to sync")

        file_data_list = []

        for idx, file_info in enumerate(files, 1):
            file_path = file_info['path']
            content, metadata = self.get_file_content(file_path)

            if not content:
                continue

            # Parse code structure
            parsed_data = self.parse_code_file(content, file_path)

            file_data = {
                'file_path': file_path,
                'file_name': file_path.split('/')[-1],
                'file_type': parsed_data['file_type'],
                'language': parsed_data['language'],
                'content': content[:100000],  # Increased limit: 100KB per file
                'functions': parsed_data['functions'],
                'classes': parsed_data['classes'],
                'imports': [imp.strip() for imp in parsed_data['imports']],
                'line_count': parsed_data['line_count'],
                'last_modified': None,  # Can be extracted from Git if needed
                'metadata': metadata
            }

            file_data_list.append(file_data)

            # Progress logging every 100 files
            if idx % 100 == 0:
                print(f"Synced {idx}/{total_files} files...")

        print(f"✅ Completed: Synced {len(file_data_list)} files from repository")
        return file_data_list

    def fetch_commit_history(self, max_commits: Optional[int] = None) -> List[Dict]:
        """Fetch ALL commit history from repository (NO LIMITS)"""
        if self.provider == "github":
            return self._github_get_commits(max_commits)
        elif self.provider == "gitlab":
            return self._gitlab_get_commits(max_commits)
        elif self.provider == "bitbucket":
            return self._bitbucket_get_commits(max_commits)

    def _github_get_commits(self, max_commits: Optional[int]) -> List[Dict]:
        """Fetch ALL commits from GitHub (NO LIMITS unless specified)"""
        url = f"{self.api_base}/repos/{self.owner}/{self.repo}/commits?sha={self.branch}&per_page=100"
        headers = {
            "Authorization": f"token {self.access_token}",
            "Accept": "application/vnd.github.v3+json"
        }

        commits = []
        try:
            # Fetch all pages until no more commits or max_commits reached
            while url:
                # Check if we've reached the limit (only if max_commits is set)
                if max_commits and len(commits) >= max_commits:
                    break

                r = requests.get(url, headers=headers, timeout=30)
                r.raise_for_status()
                data = r.json()

                for commit_data in data:
                    commit = commit_data.get('commit', {})
                    author = commit.get('author', {})

                    commits.append({
                        'sha': commit_data['sha'],
                        'message': commit.get('message', ''),
                        'author_name': author.get('name', ''),
                        'author_email': author.get('email', ''),
                        'commit_date': author.get('date'),
                        'files_changed': [f['filename'] for f in commit_data.get('files', [])],
                        'additions': commit_data.get('stats', {}).get('additions', 0),
                        'deletions': commit_data.get('stats', {}).get('deletions', 0),
                        'metadata': {
                            'url': commit_data.get('html_url'),
                            'parents': [p['sha'] for p in commit_data.get('parents', [])]
                        }
                    })

                # Progress logging
                if len(commits) % 500 == 0:
                    print(f"Fetched {len(commits)} commits...")

                # Check for next page
                if 'next' in r.links:
                    url = r.links['next']['url']
                else:
                    url = None

            print(f"✅ Fetched {len(commits)} commits from GitHub")
            return commits[:max_commits] if max_commits else commits
        except requests.RequestException as e:
            print(f"Failed to fetch commits: {e}")
            return []

    def _gitlab_get_commits(self, max_commits: Optional[int]) -> List[Dict]:
        """Fetch ALL commits from GitLab (NO LIMITS unless specified)"""
        project_id = f"{self.owner}%2F{self.repo}"
        url = f"{self.api_base}/projects/{project_id}/repository/commits?ref_name={self.branch}&per_page=100"
        headers = {"PRIVATE-TOKEN": self.access_token}

        commits = []
        try:
            while url:
                if max_commits and len(commits) >= max_commits:
                    break

                r = requests.get(url, headers=headers, timeout=30)
                r.raise_for_status()
                data = r.json()

                for commit_data in data:
                    commits.append({
                        'sha': commit_data['id'],
                        'message': commit_data.get('message', ''),
                        'author_name': commit_data.get('author_name', ''),
                        'author_email': commit_data.get('author_email', ''),
                        'commit_date': commit_data.get('created_at'),
                        'files_changed': [],  # GitLab doesn't include files in list
                        'additions': 0,
                        'deletions': 0,
                        'metadata': {
                            'url': commit_data.get('web_url')
                        }
                    })

                if len(commits) % 500 == 0:
                    print(f"Fetched {len(commits)} commits...")

                # Check for next page
                if 'next' in r.links:
                    url = r.links['next']['url']
                else:
                    url = None

            print(f"✅ Fetched {len(commits)} commits from GitLab")
            return commits[:max_commits] if max_commits else commits
        except requests.RequestException as e:
            print(f"Failed to fetch commits: {e}")
            return []

    def _bitbucket_get_commits(self, max_commits: Optional[int]) -> List[Dict]:
        """Fetch ALL commits from Bitbucket (NO LIMITS unless specified)"""
        url = f"{self.api_base}/repositories/{self.owner}/{self.repo}/commits/{self.branch}?pagelen=100"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        commits = []
        try:
            while url:
                if max_commits and len(commits) >= max_commits:
                    break

                r = requests.get(url, headers=headers, timeout=30)
                r.raise_for_status()
                data = r.json()

                for commit_data in data.get('values', []):
                    author = commit_data.get('author', {}).get('user', {})

                    commits.append({
                        'sha': commit_data['hash'],
                        'message': commit_data.get('message', ''),
                        'author_name': author.get('display_name', ''),
                        'author_email': '',
                        'commit_date': commit_data.get('date'),
                        'files_changed': [],
                        'additions': 0,
                        'deletions': 0,
                        'metadata': {
                            'url': commit_data.get('links', {}).get('html', {}).get('href')
                        }
                    })

                if len(commits) % 500 == 0:
                    print(f"Fetched {len(commits)} commits...")

                url = data.get('next')

            print(f"✅ Fetched {len(commits)} commits from Bitbucket")
            return commits[:max_commits] if max_commits else commits
        except requests.RequestException as e:
            print(f"Failed to fetch commits: {e}")
            return []

    def fetch_pull_requests(self, max_prs: Optional[int] = None) -> List[Dict]:
        """Fetch ALL pull requests from repository (NO LIMITS)"""
        if self.provider == "github":
            return self._github_get_prs(max_prs)
        elif self.provider == "gitlab":
            return self._gitlab_get_prs(max_prs)
        elif self.provider == "bitbucket":
            return self._bitbucket_get_prs(max_prs)

    def _github_get_prs(self, max_prs: Optional[int]) -> List[Dict]:
        """Fetch ALL PRs from GitHub (NO LIMITS unless specified)"""
        url = f"{self.api_base}/repos/{self.owner}/{self.repo}/pulls?state=all&per_page=100"
        headers = {
            "Authorization": f"token {self.access_token}",
            "Accept": "application/vnd.github.v3+json"
        }

        prs = []
        try:
            while url:
                if max_prs and len(prs) >= max_prs:
                    break

                r = requests.get(url, headers=headers, timeout=30)
                r.raise_for_status()
                data = r.json()

                for pr_data in data:
                    prs.append({
                        'pr_number': pr_data['number'],
                        'title': pr_data['title'],
                        'description': pr_data.get('body', ''),
                        'author_name': pr_data.get('user', {}).get('login', ''),
                        'state': pr_data['state'],
                        'created_at': pr_data.get('created_at'),
                        'merged_at': pr_data.get('merged_at'),
                        'closed_at': pr_data.get('closed_at'),
                        'commit_shas': [],  # Would need separate API call
                        'metadata': {
                            'url': pr_data.get('html_url'),
                            'head': pr_data.get('head', {}).get('ref'),
                            'base': pr_data.get('base', {}).get('ref')
                        }
                    })

                if len(prs) % 100 == 0:
                    print(f"Fetched {len(prs)} PRs...")

                # Check for next page
                if 'next' in r.links:
                    url = r.links['next']['url']
                else:
                    url = None

            print(f"✅ Fetched {len(prs)} PRs from GitHub")
            return prs[:max_prs] if max_prs else prs
        except requests.RequestException as e:
            print(f"Failed to fetch PRs: {e}")
            return []

    def _gitlab_get_prs(self, max_prs: Optional[int]) -> List[Dict]:
        """Fetch ALL merge requests from GitLab (NO LIMITS unless specified)"""
        project_id = f"{self.owner}%2F{self.repo}"
        url = f"{self.api_base}/projects/{project_id}/merge_requests?state=all&per_page=100"
        headers = {"PRIVATE-TOKEN": self.access_token}

        prs = []
        try:
            while url:
                if max_prs and len(prs) >= max_prs:
                    break

                r = requests.get(url, headers=headers, timeout=30)
                r.raise_for_status()
                data = r.json()

                for mr_data in data:
                    prs.append({
                        'pr_number': mr_data['iid'],
                        'title': mr_data['title'],
                        'description': mr_data.get('description', ''),
                        'author_name': mr_data.get('author', {}).get('name', ''),
                        'state': mr_data['state'],
                        'created_at': mr_data.get('created_at'),
                        'merged_at': mr_data.get('merged_at'),
                        'closed_at': mr_data.get('closed_at'),
                        'commit_shas': [],
                        'metadata': {
                            'url': mr_data.get('web_url'),
                            'source_branch': mr_data.get('source_branch'),
                            'target_branch': mr_data.get('target_branch')
                        }
                    })

                if len(prs) % 100 == 0:
                    print(f"Fetched {len(prs)} MRs...")

                # Check for next page
                if 'next' in r.links:
                    url = r.links['next']['url']
                else:
                    url = None

            print(f"✅ Fetched {len(prs)} merge requests from GitLab")
            return prs[:max_prs] if max_prs else prs
        except requests.RequestException as e:
            print(f"Failed to fetch merge requests: {e}")
            return []

    def _bitbucket_get_prs(self, max_prs: Optional[int]) -> List[Dict]:
        """Fetch ALL pull requests from Bitbucket (NO LIMITS unless specified)"""
        url = f"{self.api_base}/repositories/{self.owner}/{self.repo}/pullrequests?state=ALL&pagelen=50"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        prs = []
        try:
            while url:
                if max_prs and len(prs) >= max_prs:
                    break

                r = requests.get(url, headers=headers, timeout=30)
                r.raise_for_status()
                data = r.json()

                for pr_data in data.get('values', []):
                    prs.append({
                        'pr_number': pr_data['id'],
                        'title': pr_data['title'],
                        'description': pr_data.get('description', ''),
                        'author_name': pr_data.get('author', {}).get('display_name', ''),
                        'state': pr_data['state'],
                        'created_at': pr_data.get('created_on'),
                        'merged_at': pr_data.get('updated_on') if pr_data['state'] == 'MERGED' else None,
                        'closed_at': pr_data.get('updated_on') if pr_data['state'] == 'DECLINED' else None,
                        'commit_shas': [],
                        'metadata': {
                            'url': pr_data.get('links', {}).get('html', {}).get('href')
                        }
                    })

                if len(prs) % 100 == 0:
                    print(f"Fetched {len(prs)} PRs...")

                url = data.get('next')

            print(f"✅ Fetched {len(prs)} pull requests from Bitbucket")
            return prs[:max_prs] if max_prs else prs
        except requests.RequestException as e:
            print(f"Failed to fetch pull requests: {e}")
            return []
