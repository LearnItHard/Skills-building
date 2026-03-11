#!/usr/bin/env python3
"""
Skills Manager CLI
A simple CLI tool to install and manage Claude Code / OpenCode skills

Usage:
    skills install LearnItHard/Skills-building/mineru-converter
    skills list
    skills uninstall mineru-converter
"""

import os
import sys
import shutil
import argparse
import subprocess
from pathlib import Path
from typing import Optional, List

# Default skill directories for different agents
SKILL_DIRS = {
    "claude-code": Path.home() / ".claude" / "skills",
    "opencode": Path.home() / ".config" / "opencode" / "skill",
    "codex": Path.home() / ".codex" / "skills",
    "cursor": Path.home() / ".cursor" / "skills",
}

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_success(msg: str):
    print(f"{Colors.GREEN}✓{Colors.RESET} {msg}")

def print_error(msg: str):
    print(f"{Colors.RED}✗{Colors.RESET} {msg}", file=sys.stderr)

def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {msg}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {msg}")

class SkillsManager:
    def __init__(self, agent: str = "claude-code"):
        self.agent = agent
        self.skill_dir = SKILL_DIRS.get(agent, SKILL_DIRS["claude-code"])
    
    def detect_agent(self) -> str:
        """Auto-detect which agent is being used"""
        if os.environ.get("CLAUDE_CODE") or (Path.home() / ".claude").exists():
            return "claude-code"
        elif os.environ.get("OPENCODE") or (Path.home() / ".config" / "opencode").exists():
            return "opencode"
        elif os.environ.get("CODEX_HOME") or (Path.home() / ".codex").exists():
            return "codex"
        return "claude-code"
    
    def parse_repo_path(self, path: str) -> tuple:
        """Parse repo path like 'LearnItHard/Skills-building/mineru-converter'"""
        parts = path.strip("/").split("/")
        if len(parts) < 2:
            raise ValueError(f"Invalid repo path: {path}. Expected format: user/repo or user/repo/skill-name")
        
        owner = parts[0]
        repo = parts[1]
        skill_name = parts[2] if len(parts) > 2 else None
        
        return owner, repo, skill_name
    
    def install(self, repo_path: str, force: bool = False):
        """Install a skill from GitHub"""
        try:
            owner, repo, skill_name = self.parse_repo_path(repo_path)
        except ValueError as e:
            print_error(str(e))
            return False
        
        # GitHub repo URL
        repo_url = f"https://github.com/{owner}/{repo}"
        
        # If skill_name not specified, try to find it
        if not skill_name:
            print_info(f"Skill name not specified, searching in {repo}...")
            skill_name = self._find_skill_name(repo_url)
            if not skill_name:
                print_error(f"Could not find skill in {repo_url}")
                print_info("Please specify skill name: user/repo/skill-name")
                return False
        
        install_path = self.skill_dir / skill_name
        
        # Check if already installed
        if install_path.exists():
            if force:
                print_warning(f"Removing existing installation: {install_path}")
                shutil.rmtree(install_path)
            else:
                print_error(f"Skill already installed: {skill_name}")
                print_info("Use --force to overwrite")
                return False
        
        print_info(f"Installing {skill_name}...")
        
        # Clone to temp directory
        temp_dir = Path("/tmp") / f"skills-install-{skill_name}"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, str(temp_dir)],
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError:
            print_error(f"Failed to clone {repo_url}")
            return False
        
        # Find skill directory
        skill_source = temp_dir / "skills" / skill_name
        if not skill_source.exists():
            # Try root directory
            skill_source = temp_dir / skill_name
        if not skill_source.exists():
            print_error(f"Skill not found: {skill_name}")
            shutil.rmtree(temp_dir)
            return False
        
        # Copy to install directory
        self.skill_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(skill_source, install_path)
        shutil.rmtree(temp_dir)
        
        print_success(f"Installed {skill_name} to {install_path}")
        
        # Check for post-install instructions
        skill_md = install_path / "SKILL.md"
        if skill_md.exists():
            print_info(f"Skill ready! View documentation: {skill_md}")
        
        return True
    
    def _find_skill_name(self, repo_url: str) -> Optional[str]:
        """Try to find skill name in repo"""
        temp_dir = Path("/tmp") / "skills-detect"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, str(temp_dir)],
                check=True,
                capture_output=True
            )
            
            # Check skills/ directory
            skills_dir = temp_dir / "skills"
            if skills_dir.exists():
                subdirs = [d.name for d in skills_dir.iterdir() if d.is_dir()]
                if len(subdirs) == 1:
                    return subdirs[0]
            
            # Check root for SKILL.md
            for item in temp_dir.iterdir():
                if item.is_dir() and (item / "SKILL.md").exists():
                    return item.name
                    
        except Exception:
            pass
        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        
        return None
    
    def uninstall(self, skill_name: str):
        """Uninstall a skill"""
        install_path = self.skill_dir / skill_name
        
        if not install_path.exists():
            print_error(f"Skill not found: {skill_name}")
            return False
        
        shutil.rmtree(install_path)
        print_success(f"Uninstalled {skill_name}")
        return True
    
    def list_skills(self) -> List[str]:
        """List installed skills"""
        if not self.skill_dir.exists():
            print_info(f"No skills directory found: {self.skill_dir}")
            return []
        
        skills = []
        for item in self.skill_dir.iterdir():
            if item.is_dir() and (item / "SKILL.md").exists():
                skills.append(item.name)
        
        return sorted(skills)
    
    def update(self, skill_name: Optional[str] = None):
        """Update skill(s) - placeholder for future implementation"""
        print_info("Update functionality coming soon!")
        print_info("For now, uninstall and reinstall to update.")

def main():
    parser = argparse.ArgumentParser(
        description="Skills Manager - Install and manage AI agent skills",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  skills install LearnItHard/Skills-building/mineru-converter
  skills install user/repo/skill-name --force
  skills list
  skills uninstall mineru-converter
        """
    )
    
    parser.add_argument(
        "--agent",
        choices=["claude-code", "opencode", "codex", "cursor"],
        help="Target agent (auto-detected if not specified)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Install command
    install_parser = subparsers.add_parser("install", help="Install a skill")
    install_parser.add_argument("repo", help="Repository path (e.g., user/repo/skill)")
    install_parser.add_argument("--force", "-f", action="store_true", help="Overwrite if exists")
    
    # List command
    subparsers.add_parser("list", help="List installed skills")
    
    # Uninstall command
    uninstall_parser = subparsers.add_parser("uninstall", help="Uninstall a skill")
    uninstall_parser.add_argument("skill", help="Skill name to uninstall")
    
    # Update command
    update_parser = subparsers.add_parser("update", help="Update skill(s)")
    update_parser.add_argument("skill", nargs="?", help="Skill name (omit for all)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize manager
    manager = SkillsManager(agent=args.agent or "claude-code")
    if not args.agent:
        manager.agent = manager.detect_agent()
        manager.skill_dir = SKILL_DIRS[manager.agent]
    
    if args.command == "install":
        success = manager.install(args.repo, force=args.force)
        sys.exit(0 if success else 1)
    
    elif args.command == "list":
        skills = manager.list_skills()
        if skills:
            print(f"\nInstalled skills for {manager.agent}:")
            for skill in skills:
                print(f"  • {skill}")
            print()
        else:
            print_info(f"No skills installed for {manager.agent}")
            print_info(f"Skill directory: {manager.skill_dir}")
    
    elif args.command == "uninstall":
        success = manager.uninstall(args.skill)
        sys.exit(0 if success else 1)
    
    elif args.command == "update":
        manager.update(args.skill)

if __name__ == "__main__":
    main()
