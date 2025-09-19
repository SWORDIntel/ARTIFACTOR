"""
GitHub Plugin for ARTIFACTOR v3.0
Reference implementation demonstrating plugin architecture and best practices
"""

import asyncio
import logging
import json
import os
import tempfile
import shutil
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import base64
import hashlib
import hmac

import aiohttp
from github import Github, GithubException
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

class GitHubPluginError(Exception):
    """Custom exception for GitHub plugin errors"""
    pass

class GitHubPlugin:
    """
    GitHub integration plugin for ARTIFACTOR
    Provides repository management, artifact synchronization, and collaboration features
    """

    def __init__(self):
        self.config = {}
        self.github_client = None
        self.authenticated = False
        self.repository = None
        self.webhook_handlers = {}

        # Plugin metadata
        self.name = "github-plugin"
        self.version = "1.0.0"
        self.api_version = "1.0"

    async def initialize(self):
        """Initialize the GitHub plugin"""
        try:
            logger.info("Initializing GitHub Plugin v1.0.0")

            # Load configuration
            await self._load_config()

            # Initialize GitHub client
            if self.config.get('github_token'):
                await self._initialize_github_client()

            # Setup webhook handlers
            self._setup_webhook_handlers()

            logger.info("GitHub Plugin initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize GitHub Plugin: {e}")
            raise GitHubPluginError(f"Initialization failed: {e}")

    async def _load_config(self):
        """Load plugin configuration"""
        try:
            # Configuration would be loaded from ARTIFACTOR's configuration system
            # For this demo, we'll use default values
            self.config = {
                'github_token': os.getenv('GITHUB_TOKEN'),
                'default_repository': os.getenv('GITHUB_DEFAULT_REPO'),
                'auto_sync': False,
                'webhook_secret': os.getenv('GITHUB_WEBHOOK_SECRET'),
                'commit_template': "Add artifact: {artifact_name}\n\n{description}"
            }

            # Validate required configuration
            if not self.config.get('github_token'):
                logger.warning("GitHub token not configured - limited functionality available")

        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise

    async def _initialize_github_client(self):
        """Initialize GitHub API client"""
        try:
            token = self.config['github_token']
            if not token:
                return

            # Initialize GitHub client
            self.github_client = Github(token)

            # Test authentication
            user = self.github_client.get_user()
            logger.info(f"Authenticated as GitHub user: {user.login}")
            self.authenticated = True

            # Set default repository if specified
            if self.config.get('default_repository'):
                try:
                    self.repository = self.github_client.get_repo(self.config['default_repository'])
                    logger.info(f"Connected to repository: {self.repository.full_name}")
                except GithubException as e:
                    logger.warning(f"Could not access default repository: {e}")

        except Exception as e:
            logger.error(f"GitHub authentication failed: {e}")
            self.authenticated = False

    def _setup_webhook_handlers(self):
        """Setup webhook event handlers"""
        self.webhook_handlers = {
            'push': self._handle_push_event,
            'pull_request': self._handle_pull_request_event,
            'issues': self._handle_issues_event,
            'release': self._handle_release_event
        }

    # Public API Methods

    async def connect_repository(self, repository_name: str) -> Dict[str, Any]:
        """Connect to a GitHub repository"""
        try:
            if not self.authenticated:
                return {"success": False, "error": "Not authenticated with GitHub"}

            repo = self.github_client.get_repo(repository_name)
            self.repository = repo

            repo_info = {
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "private": repo.private,
                "default_branch": repo.default_branch,
                "clone_url": repo.clone_url,
                "html_url": repo.html_url,
                "created_at": repo.created_at.isoformat(),
                "updated_at": repo.updated_at.isoformat(),
                "size": repo.size,
                "language": repo.language,
                "forks_count": repo.forks_count,
                "stargazers_count": repo.stargazers_count
            }

            logger.info(f"Connected to repository: {repo.full_name}")

            return {
                "success": True,
                "repository": repo_info,
                "message": f"Connected to {repo.full_name}"
            }

        except GithubException as e:
            logger.error(f"Error connecting to repository {repository_name}: {e}")
            return {"success": False, "error": str(e)}

    async def list_repositories(self, user_only: bool = True) -> Dict[str, Any]:
        """List accessible repositories"""
        try:
            if not self.authenticated:
                return {"success": False, "error": "Not authenticated with GitHub"}

            if user_only:
                repos = self.github_client.get_user().get_repos()
            else:
                repos = self.github_client.get_user().get_repos(type="all")

            repository_list = []
            for repo in repos[:50]:  # Limit to first 50 repositories
                repository_list.append({
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "private": repo.private,
                    "html_url": repo.html_url,
                    "language": repo.language,
                    "updated_at": repo.updated_at.isoformat()
                })

            return {
                "success": True,
                "repositories": repository_list,
                "count": len(repository_list)
            }

        except GithubException as e:
            logger.error(f"Error listing repositories: {e}")
            return {"success": False, "error": str(e)}

    async def sync_artifact(self, artifact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync artifact to GitHub repository"""
        try:
            if not self.repository:
                return {"success": False, "error": "No repository connected"}

            artifact_name = artifact_data.get('title', 'untitled')
            artifact_content = artifact_data.get('content', '')
            artifact_description = artifact_data.get('description', '')
            file_extension = artifact_data.get('file_extension', '.txt')

            # Generate filename
            filename = f"artifacts/{artifact_name}{file_extension}"

            # Check if file exists
            try:
                existing_file = self.repository.get_contents(filename)
                file_exists = True
            except GithubException:
                existing_file = None
                file_exists = False

            # Create commit message
            commit_message = self.config['commit_template'].format(
                artifact_name=artifact_name,
                description=artifact_description
            )

            # Create or update file
            if file_exists:
                # Update existing file
                result = self.repository.update_file(
                    path=filename,
                    message=f"Update artifact: {artifact_name}",
                    content=artifact_content,
                    sha=existing_file.sha
                )
                action = "updated"
            else:
                # Create new file
                result = self.repository.create_file(
                    path=filename,
                    message=commit_message,
                    content=artifact_content
                )
                action = "created"

            commit_info = {
                "sha": result['commit'].sha,
                "url": result['commit'].html_url,
                "message": result['commit'].commit.message,
                "author": result['commit'].commit.author.name,
                "date": result['commit'].commit.author.date.isoformat()
            }

            logger.info(f"Artifact {action} in repository: {filename}")

            return {
                "success": True,
                "action": action,
                "filename": filename,
                "commit": commit_info,
                "file_url": result['content'].html_url
            }

        except GithubException as e:
            logger.error(f"Error syncing artifact: {e}")
            return {"success": False, "error": str(e)}

    async def create_release(self, release_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a GitHub release"""
        try:
            if not self.repository:
                return {"success": False, "error": "No repository connected"}

            tag_name = release_data.get('tag_name')
            name = release_data.get('name', tag_name)
            body = release_data.get('body', '')
            draft = release_data.get('draft', False)
            prerelease = release_data.get('prerelease', False)

            if not tag_name:
                return {"success": False, "error": "Tag name is required"}

            # Create release
            release = self.repository.create_git_release(
                tag=tag_name,
                name=name,
                message=body,
                draft=draft,
                prerelease=prerelease
            )

            release_info = {
                "id": release.id,
                "tag_name": release.tag_name,
                "name": release.title,
                "body": release.body,
                "html_url": release.html_url,
                "created_at": release.created_at.isoformat(),
                "published_at": release.published_at.isoformat() if release.published_at else None,
                "draft": release.draft,
                "prerelease": release.prerelease
            }

            logger.info(f"Created release: {release.tag_name}")

            return {
                "success": True,
                "release": release_info,
                "message": f"Release {tag_name} created successfully"
            }

        except GithubException as e:
            logger.error(f"Error creating release: {e}")
            return {"success": False, "error": str(e)}

    async def get_repository_info(self) -> Dict[str, Any]:
        """Get information about the connected repository"""
        try:
            if not self.repository:
                return {"success": False, "error": "No repository connected"}

            repo = self.repository

            # Get recent commits
            commits = list(repo.get_commits()[:10])
            recent_commits = []
            for commit in commits:
                recent_commits.append({
                    "sha": commit.sha,
                    "message": commit.commit.message,
                    "author": commit.commit.author.name,
                    "date": commit.commit.author.date.isoformat(),
                    "url": commit.html_url
                })

            # Get open issues
            issues = list(repo.get_issues(state='open')[:10])
            open_issues = []
            for issue in issues:
                open_issues.append({
                    "number": issue.number,
                    "title": issue.title,
                    "state": issue.state,
                    "created_at": issue.created_at.isoformat(),
                    "html_url": issue.html_url
                })

            # Get recent releases
            releases = list(repo.get_releases()[:5])
            recent_releases = []
            for release in releases:
                recent_releases.append({
                    "tag_name": release.tag_name,
                    "name": release.title,
                    "created_at": release.created_at.isoformat(),
                    "html_url": release.html_url
                })

            repository_info = {
                "basic_info": {
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "private": repo.private,
                    "html_url": repo.html_url,
                    "language": repo.language,
                    "size": repo.size,
                    "forks_count": repo.forks_count,
                    "stargazers_count": repo.stargazers_count,
                    "watchers_count": repo.watchers_count,
                    "open_issues_count": repo.open_issues_count,
                    "default_branch": repo.default_branch,
                    "created_at": repo.created_at.isoformat(),
                    "updated_at": repo.updated_at.isoformat()
                },
                "recent_commits": recent_commits,
                "open_issues": open_issues,
                "recent_releases": recent_releases
            }

            return {
                "success": True,
                "repository": repository_info
            }

        except GithubException as e:
            logger.error(f"Error getting repository info: {e}")
            return {"success": False, "error": str(e)}

    async def create_webhook(self, webhook_url: str, events: List[str] = None) -> Dict[str, Any]:
        """Create a webhook for the repository"""
        try:
            if not self.repository:
                return {"success": False, "error": "No repository connected"}

            if events is None:
                events = ['push', 'pull_request', 'issues']

            config = {
                'url': webhook_url,
                'content_type': 'json'
            }

            if self.config.get('webhook_secret'):
                config['secret'] = self.config['webhook_secret']

            webhook = self.repository.create_hook(
                name='web',
                config=config,
                events=events,
                active=True
            )

            webhook_info = {
                "id": webhook.id,
                "name": webhook.name,
                "active": webhook.active,
                "events": webhook.events,
                "config": webhook.config,
                "created_at": webhook.created_at.isoformat(),
                "updated_at": webhook.updated_at.isoformat()
            }

            logger.info(f"Created webhook: {webhook.id}")

            return {
                "success": True,
                "webhook": webhook_info,
                "message": "Webhook created successfully"
            }

        except GithubException as e:
            logger.error(f"Error creating webhook: {e}")
            return {"success": False, "error": str(e)}

    async def handle_webhook(self, headers: Dict[str, str], payload: str) -> Dict[str, Any]:
        """Handle incoming webhook payload"""
        try:
            # Verify webhook signature if secret is configured
            if self.config.get('webhook_secret'):
                signature = headers.get('X-Hub-Signature-256', '')
                if not self._verify_webhook_signature(payload, signature):
                    return {"success": False, "error": "Invalid webhook signature"}

            # Parse payload
            data = json.loads(payload)
            event_type = headers.get('X-GitHub-Event', '')

            # Route to appropriate handler
            handler = self.webhook_handlers.get(event_type)
            if handler:
                result = await handler(data)
                return {"success": True, "event": event_type, "result": result}
            else:
                logger.warning(f"No handler for webhook event: {event_type}")
                return {"success": True, "event": event_type, "message": "Event received but not handled"}

        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return {"success": False, "error": str(e)}

    def _verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """Verify GitHub webhook signature"""
        try:
            secret = self.config['webhook_secret'].encode('utf-8')
            expected_signature = 'sha256=' + hmac.new(
                secret,
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(expected_signature, signature)

        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False

    # Webhook Event Handlers

    async def _handle_push_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle push event"""
        try:
            commits = data.get('commits', [])
            repository = data.get('repository', {})
            ref = data.get('ref', '')

            logger.info(f"Push event: {len(commits)} commits to {repository.get('full_name')} ({ref})")

            return {
                "event": "push",
                "repository": repository.get('full_name'),
                "ref": ref,
                "commits_count": len(commits),
                "commits": commits[:5]  # Include first 5 commits
            }

        except Exception as e:
            logger.error(f"Error handling push event: {e}")
            return {"error": str(e)}

    async def _handle_pull_request_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pull request event"""
        try:
            action = data.get('action', '')
            pull_request = data.get('pull_request', {})
            repository = data.get('repository', {})

            logger.info(f"Pull request {action}: #{pull_request.get('number')} in {repository.get('full_name')}")

            return {
                "event": "pull_request",
                "action": action,
                "repository": repository.get('full_name'),
                "pull_request": {
                    "number": pull_request.get('number'),
                    "title": pull_request.get('title'),
                    "state": pull_request.get('state'),
                    "html_url": pull_request.get('html_url')
                }
            }

        except Exception as e:
            logger.error(f"Error handling pull request event: {e}")
            return {"error": str(e)}

    async def _handle_issues_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle issues event"""
        try:
            action = data.get('action', '')
            issue = data.get('issue', {})
            repository = data.get('repository', {})

            logger.info(f"Issue {action}: #{issue.get('number')} in {repository.get('full_name')}")

            return {
                "event": "issues",
                "action": action,
                "repository": repository.get('full_name'),
                "issue": {
                    "number": issue.get('number'),
                    "title": issue.get('title'),
                    "state": issue.get('state'),
                    "html_url": issue.get('html_url')
                }
            }

        except Exception as e:
            logger.error(f"Error handling issues event: {e}")
            return {"error": str(e)}

    async def _handle_release_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle release event"""
        try:
            action = data.get('action', '')
            release = data.get('release', {})
            repository = data.get('repository', {})

            logger.info(f"Release {action}: {release.get('tag_name')} in {repository.get('full_name')}")

            return {
                "event": "release",
                "action": action,
                "repository": repository.get('full_name'),
                "release": {
                    "tag_name": release.get('tag_name'),
                    "name": release.get('name'),
                    "html_url": release.get('html_url')
                }
            }

        except Exception as e:
            logger.error(f"Error handling release event: {e}")
            return {"error": str(e)}

    # Agent Integration Methods

    async def integrate_with_constructor(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Integration with CONSTRUCTOR agent"""
        try:
            task_type = task_data.get('task_type', 'sync_project')

            if task_type == 'sync_project':
                # Sync project artifacts to GitHub
                artifacts = task_data.get('artifacts', [])
                results = []

                for artifact in artifacts:
                    result = await self.sync_artifact(artifact)
                    results.append(result)

                return {
                    "success": True,
                    "integration": "constructor",
                    "task": task_type,
                    "results": results
                }

            return {"success": False, "error": f"Unknown task type: {task_type}"}

        except Exception as e:
            logger.error(f"Error in CONSTRUCTOR integration: {e}")
            return {"success": False, "error": str(e)}

    async def get_status(self) -> Dict[str, Any]:
        """Get plugin status"""
        return {
            "name": self.name,
            "version": self.version,
            "authenticated": self.authenticated,
            "repository_connected": self.repository is not None,
            "repository_name": self.repository.full_name if self.repository else None,
            "config_loaded": bool(self.config),
            "webhook_handlers": len(self.webhook_handlers)
        }

    async def cleanup(self):
        """Cleanup plugin resources"""
        try:
            logger.info("Cleaning up GitHub Plugin...")

            if self.github_client:
                # Close any open connections
                pass

            self.github_client = None
            self.repository = None
            self.authenticated = False

            logger.info("GitHub Plugin cleanup complete")

        except Exception as e:
            logger.error(f"Error during GitHub Plugin cleanup: {e}")

# Plugin instance (required by ARTIFACTOR plugin system)
github_plugin = GitHubPlugin()

# Plugin API exports (required by ARTIFACTOR plugin system)
async def initialize():
    """Plugin initialization entry point"""
    await github_plugin.initialize()

async def cleanup():
    """Plugin cleanup entry point"""
    await github_plugin.cleanup()

# Public API methods (exposed to ARTIFACTOR)
async def connect_repository(repository_name: str) -> Dict[str, Any]:
    return await github_plugin.connect_repository(repository_name)

async def list_repositories(user_only: bool = True) -> Dict[str, Any]:
    return await github_plugin.list_repositories(user_only)

async def sync_artifact(artifact_data: Dict[str, Any]) -> Dict[str, Any]:
    return await github_plugin.sync_artifact(artifact_data)

async def create_release(release_data: Dict[str, Any]) -> Dict[str, Any]:
    return await github_plugin.create_release(release_data)

async def get_repository_info() -> Dict[str, Any]:
    return await github_plugin.get_repository_info()

async def create_webhook(webhook_url: str, events: List[str] = None) -> Dict[str, Any]:
    return await github_plugin.create_webhook(webhook_url, events)

async def handle_webhook(headers: Dict[str, str], payload: str) -> Dict[str, Any]:
    return await github_plugin.handle_webhook(headers, payload)

async def get_status() -> Dict[str, Any]:
    return await github_plugin.get_status()

# Agent integration methods
async def integrate_with_constructor(task_data: Dict[str, Any]) -> Dict[str, Any]:
    return await github_plugin.integrate_with_constructor(task_data)