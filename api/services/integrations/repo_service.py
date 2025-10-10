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

    def sync_repository(self, max_files: int = 500) -> List[Dict]:
        """Sync repository and return file data"""
        files = self.get_file_tree()

        # Limit number of files to prevent overload
        if len(files) > max_files:
            print(f"Warning: Repository has {len(files)} files, limiting to {max_files}")
            files = files[:max_files]

        file_data_list = []

        for file_info in files:
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
                'content': content[:50000],  # Limit content size (50KB)
                'functions': parsed_data['functions'],
                'classes': parsed_data['classes'],
                'imports': [imp.strip() for imp in parsed_data['imports']],
                'line_count': parsed_data['line_count'],
                'last_modified': None,  # Can be extracted from Git if needed
                'metadata': metadata
            }

            file_data_list.append(file_data)

        return file_data_list
