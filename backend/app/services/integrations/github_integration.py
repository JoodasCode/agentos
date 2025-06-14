from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from app.services.base_integration import BaseIntegration, IntegrationStatus
from app.models.api_keys import SupportedService
from app.core.logging import get_logger

logger = get_logger(__name__)

class GitHubIntegration(BaseIntegration):
    """GitHub API integration for repository management, issues, PRs, and CI/CD automation"""
    
    def __init__(self):
        super().__init__(SupportedService.GITHUB)
    
    @property
    def base_url(self) -> str:
        return "https://api.github.com"
    
    @property
    def required_scopes(self) -> List[str]:
        return [
            "repo",
            "issues",
            "pull_requests",
            "actions",
            "user:read",
            "user:email"
        ]
    
    async def _prepare_auth_headers(self, api_key: str) -> Dict[str, str]:
        """Prepare GitHub API headers"""
        return {
            "Authorization": f"token {api_key}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
    
    async def _test_api_connection(self, api_key: str) -> Dict[str, Any]:
        """Test GitHub API connection by getting user info"""
        try:
            result = await self.make_api_request(
                method="GET",
                endpoint="user",
                api_key=api_key
            )
            
            if result.get("success"):
                user_data = result.get("data", {})
                return {
                    "connected": True,
                    "status": "success",
                    "message": "Successfully connected to GitHub",
                    "user_info": {
                        "login": user_data.get("login", "Unknown"),
                        "name": user_data.get("name", "Unknown"),
                        "email": user_data.get("email", "Unknown"),
                        "public_repos": user_data.get("public_repos", 0),
                        "private_repos": user_data.get("total_private_repos", 0)
                    }
                }
            else:
                return {
                    "connected": False,
                    "status": "error",
                    "message": result.get("message", "Failed to connect to GitHub")
                }
                
        except Exception as e:
            logger.error(f"GitHub connection test failed: {str(e)}")
            return {
                "connected": False,
                "status": "error", 
                "message": str(e)
            }
    
    # Core GitHub Operations
    
    async def get_repositories(self, session_id: str, type: str = "all") -> Dict[str, Any]:
        """Get user's repositories"""
        api_key = await self.get_api_key(session_id)
        if not api_key:
            return {"success": False, "error": "no_api_key"}
        
        try:
            params = {"type": type, "sort": "updated", "per_page": 50}
            
            result = await self.make_api_request(
                method="GET",
                endpoint="user/repos",
                api_key=api_key,
                params=params
            )
            
            if result.get("success"):
                repos_data = result.get("data", [])
                repositories = []
                
                for repo in repos_data:
                    repositories.append({
                        "id": repo.get("id"),
                        "name": repo.get("name"),
                        "full_name": repo.get("full_name"),
                        "description": repo.get("description", ""),
                        "private": repo.get("private", False),
                        "html_url": repo.get("html_url"),
                        "clone_url": repo.get("clone_url"),
                        "language": repo.get("language"),
                        "stars": repo.get("stargazers_count", 0),
                        "forks": repo.get("forks_count", 0),
                        "open_issues": repo.get("open_issues_count", 0),
                        "updated_at": repo.get("updated_at"),
                        "default_branch": repo.get("default_branch", "main")
                    })
                
                return {
                    "success": True,
                    "repositories": repositories,
                    "count": len(repositories)
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error getting GitHub repositories: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_issues(
        self, 
        session_id: str, 
        repo_owner: str, 
        repo_name: str,
        state: str = "open",
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get issues from a repository"""
        api_key = await self.get_api_key(session_id)
        if not api_key:
            return {"success": False, "error": "no_api_key"}
        
        try:
            params = {"state": state, "per_page": 50}
            if labels:
                params["labels"] = ",".join(labels)
            
            result = await self.make_api_request(
                method="GET",
                endpoint=f"repos/{repo_owner}/{repo_name}/issues",
                api_key=api_key,
                params=params
            )
            
            if result.get("success"):
                issues_data = result.get("data", [])
                issues = []
                
                for issue in issues_data:
                    # Skip pull requests (they appear in issues API)
                    if issue.get("pull_request"):
                        continue
                    
                    issues.append({
                        "id": issue.get("id"),
                        "number": issue.get("number"),
                        "title": issue.get("title"),
                        "body": issue.get("body", ""),
                        "state": issue.get("state"),
                        "labels": [label.get("name") for label in issue.get("labels", [])],
                        "assignees": [assignee.get("login") for assignee in issue.get("assignees", [])],
                        "author": issue.get("user", {}).get("login", "Unknown"),
                        "created_at": issue.get("created_at"),
                        "updated_at": issue.get("updated_at"),
                        "html_url": issue.get("html_url")
                    })
                
                return {
                    "success": True,
                    "issues": issues,
                    "count": len(issues)
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error getting GitHub issues: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def create_issue(
        self, 
        session_id: str, 
        repo_owner: str, 
        repo_name: str,
        title: str,
        body: Optional[str] = None,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new issue"""
        api_key = await self.get_api_key(session_id)
        if not api_key:
            return {"success": False, "error": "no_api_key"}
        
        try:
            issue_data = {"title": title}
            
            if body:
                issue_data["body"] = body
            
            if labels:
                issue_data["labels"] = labels
            
            if assignees:
                issue_data["assignees"] = assignees
            
            result = await self.make_api_request(
                method="POST",
                endpoint=f"repos/{repo_owner}/{repo_name}/issues",
                api_key=api_key,
                data=issue_data
            )
            
            if result.get("success"):
                issue = result.get("data", {})
                return {
                    "success": True,
                    "issue": {
                        "id": issue.get("id"),
                        "number": issue.get("number"),
                        "title": issue.get("title"),
                        "html_url": issue.get("html_url"),
                        "created_at": issue.get("created_at")
                    }
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error creating GitHub issue: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_pull_requests(
        self, 
        session_id: str, 
        repo_owner: str, 
        repo_name: str,
        state: str = "open"
    ) -> Dict[str, Any]:
        """Get pull requests from a repository"""
        api_key = await self.get_api_key(session_id)
        if not api_key:
            return {"success": False, "error": "no_api_key"}
        
        try:
            params = {"state": state, "per_page": 50}
            
            result = await self.make_api_request(
                method="GET",
                endpoint=f"repos/{repo_owner}/{repo_name}/pulls",
                api_key=api_key,
                params=params
            )
            
            if result.get("success"):
                prs_data = result.get("data", [])
                pull_requests = []
                
                for pr in prs_data:
                    pull_requests.append({
                        "id": pr.get("id"),
                        "number": pr.get("number"),
                        "title": pr.get("title"),
                        "body": pr.get("body", ""),
                        "state": pr.get("state"),
                        "author": pr.get("user", {}).get("login", "Unknown"),
                        "head_branch": pr.get("head", {}).get("ref", ""),
                        "base_branch": pr.get("base", {}).get("ref", ""),
                        "mergeable": pr.get("mergeable"),
                        "created_at": pr.get("created_at"),
                        "updated_at": pr.get("updated_at"),
                        "html_url": pr.get("html_url")
                    })
                
                return {
                    "success": True,
                    "pull_requests": pull_requests,
                    "count": len(pull_requests)
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error getting GitHub pull requests: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def create_pull_request(
        self, 
        session_id: str, 
        repo_owner: str, 
        repo_name: str,
        title: str,
        head_branch: str,
        base_branch: str = "main",
        body: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new pull request"""
        api_key = await self.get_api_key(session_id)
        if not api_key:
            return {"success": False, "error": "no_api_key"}
        
        try:
            pr_data = {
                "title": title,
                "head": head_branch,
                "base": base_branch
            }
            
            if body:
                pr_data["body"] = body
            
            result = await self.make_api_request(
                method="POST",
                endpoint=f"repos/{repo_owner}/{repo_name}/pulls",
                api_key=api_key,
                data=pr_data
            )
            
            if result.get("success"):
                pr = result.get("data", {})
                return {
                    "success": True,
                    "pull_request": {
                        "id": pr.get("id"),
                        "number": pr.get("number"),
                        "title": pr.get("title"),
                        "html_url": pr.get("html_url"),
                        "created_at": pr.get("created_at")
                    }
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error creating GitHub pull request: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_workflow_runs(
        self, 
        session_id: str, 
        repo_owner: str, 
        repo_name: str,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get GitHub Actions workflow runs"""
        api_key = await self.get_api_key(session_id)
        if not api_key:
            return {"success": False, "error": "no_api_key"}
        
        try:
            params = {"per_page": 50}
            if status:
                params["status"] = status
            
            result = await self.make_api_request(
                method="GET",
                endpoint=f"repos/{repo_owner}/{repo_name}/actions/runs",
                api_key=api_key,
                params=params
            )
            
            if result.get("success"):
                runs_data = result.get("data", {})
                workflow_runs = []
                
                for run in runs_data.get("workflow_runs", []):
                    workflow_runs.append({
                        "id": run.get("id"),
                        "name": run.get("name"),
                        "status": run.get("status"),
                        "conclusion": run.get("conclusion"),
                        "workflow_id": run.get("workflow_id"),
                        "head_branch": run.get("head_branch"),
                        "head_sha": run.get("head_sha"),
                        "created_at": run.get("created_at"),
                        "updated_at": run.get("updated_at"),
                        "html_url": run.get("html_url")
                    })
                
                return {
                    "success": True,
                    "workflow_runs": workflow_runs,
                    "count": len(workflow_runs)
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error getting GitHub workflow runs: {str(e)}")
            return {"success": False, "error": str(e)}
    
    # Trigger.dev Workflow Integration
    
    async def _create_service_workflow(
        self, 
        workflow_payload: Dict[str, Any], 
        api_key: str
    ) -> Dict[str, Any]:
        """Create GitHub-specific Trigger.dev workflows"""
        
        workflow_name = workflow_payload.get("name")
        config = workflow_payload.get("config", {})
        
        # Define available GitHub workflows
        github_workflows = {
            "issue_management": {
                "description": "Automatically manage issues and project tracking",
                "triggers": ["issue_created", "issue_updated", "manual"],
                "actions": ["create_issue", "update_labels", "assign_users"]
            },
            "pr_automation": {
                "description": "Automate pull request workflows and reviews",
                "triggers": ["pr_created", "pr_updated", "review_requested"],
                "actions": ["create_pr", "request_review", "merge_pr"]
            },
            "ci_cd_monitoring": {
                "description": "Monitor CI/CD pipelines and deployments",
                "triggers": ["workflow_completed", "deployment_status"],
                "actions": ["send_notification", "create_issue", "trigger_workflow"]
            },
            "release_management": {
                "description": "Automate release processes and changelog generation",
                "triggers": ["tag_created", "milestone_reached"],
                "actions": ["create_release", "generate_changelog", "notify_team"]
            }
        }
        
        workflow_type = config.get("workflow_type", "issue_management")
        
        if workflow_type not in github_workflows:
            return {
                "success": False,
                "error": "invalid_workflow_type",
                "available_workflows": list(github_workflows.keys())
            }
        
        # Create workflow configuration
        workflow_config = {
            "name": workflow_name,
            "service": "github",
            "type": workflow_type,
            "config": github_workflows[workflow_type],
            "user_config": config,
            "created_at": datetime.utcnow().isoformat()
        }
        
        return {
            "success": True,
            "workflow": workflow_config,
            "message": f"GitHub workflow '{workflow_name}' created successfully"
        }
    
    # Helper Methods
    
    def format_issue_for_display(self, issue: Dict[str, Any]) -> str:
        """Format issue data for human-readable display"""
        title = issue.get("title", "No Title")
        number = issue.get("number", "Unknown")
        state = issue.get("state", "unknown")
        labels = issue.get("labels", [])
        
        result = f"🐛 #{number}: {title}\n📊 Status: {state.upper()}"
        
        if labels:
            result += f"\n🏷️ Labels: {', '.join(labels)}"
        
        return result
    
    def format_pr_for_display(self, pr: Dict[str, Any]) -> str:
        """Format pull request data for human-readable display"""
        title = pr.get("title", "No Title")
        number = pr.get("number", "Unknown")
        state = pr.get("state", "unknown")
        head_branch = pr.get("head_branch", "unknown")
        base_branch = pr.get("base_branch", "unknown")
        
        result = f"🔀 #{number}: {title}\n📊 Status: {state.upper()}\n🌿 {head_branch} → {base_branch}"
        
        return result

# Global instance
github_integration = GitHubIntegration() 