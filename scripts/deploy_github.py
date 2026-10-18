"""Automated deployment script to push repo, set secrets, and trigger GitHub Actions."""
import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
GH_PATH = r"C:\Program Files\GitHub CLI\gh.exe"
if not Path(GH_PATH).exists():
    GH_PATH = "gh"

ENV_PATH = BASE_DIR / ".env"


def run_cmd(args, check=True):
    print(f"Running: {' '.join(args)}")
    result = subprocess.run(args, cwd=str(BASE_DIR), capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error ({result.returncode}):\n{result.stderr}\n{result.stdout}")
        return None
    return result.stdout.strip()


def deploy_to_github(repo_name="devresearch-daily-briefing"):
    print("=== DevResearch GitHub Deployment ===")
    
    # 1. Check gh authentication
    auth_check = run_cmd([GH_PATH, "auth", "status"], check=False)
    if auth_check is None or "Logged in to" not in (auth_check or ""):
        # Check stderr
        res = subprocess.run([GH_PATH, "auth", "status"], cwd=str(BASE_DIR), capture_output=True, text=True)
        if "Logged in to" not in res.stderr and "Logged in to" not in res.stdout:
            print("\n[ACTION REQUIRED] GitHub CLI is not authenticated.")
            print("Please run this command in your PowerShell terminal to authenticate:")
            print(f'  & "{GH_PATH}" auth login')
            print("Select: GitHub.com -> HTTPS -> Login with a web browser\n")
            return False

    # Get current username
    user_out = run_cmd([GH_PATH, "api", "user", "-q", ".login"])
    username = user_out or "user"
    print(f"Authenticated as GitHub user: {username}")

    # 2. Check if remote origin already exists
    remotes = run_cmd(["git", "remote"], check=False) or ""
    if "origin" not in remotes:
        print(f"Creating private repository: {repo_name}...")
        create_res = subprocess.run(
            [GH_PATH, "repo", "create", repo_name, "--private", "--source=.", "--remote=origin", "--push"],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True
        )
        print(create_res.stdout)
        if create_res.returncode != 0 and "already exists" not in create_res.stderr:
            print("Repo creation notice:", create_res.stderr)
    else:
        print("Remote origin already configured. Pushing to origin main...")
        run_cmd(["git", "push", "-u", "origin", "main"], check=False)

    # 3. Automatically populate GitHub Secrets from local .env
    if ENV_PATH.exists():
        print("Reading secrets from local .env...")
        secret_keys = [
            "SMTP_USER", "SMTP_PASSWORD", "MAIL_RECIPIENTS", "SMTP_HOST", "SMTP_PORT",
            "LLM_PROVIDER", "GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
            "MAIL_PROVIDER", "MAIL_FROM", "RESEND_API_KEY", "SENDGRID_API_KEY"
        ]
        
        env_lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
        env_dict = {}
        for line in env_lines:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                v = v.strip().strip('"').strip("'")
                if v:
                    env_dict[k.strip()] = v

        for k in secret_keys:
            if k in env_dict:
                val = env_dict[k]
                sec_res = subprocess.run(
                    [GH_PATH, "secret", "set", k, "--body", val],
                    cwd=str(BASE_DIR),
                    capture_output=True,
                    text=True
                )
                if sec_res.returncode == 0:
                    print(f"  [OK] Secret set: {k}")
                else:
                    print(f"  [WARN] Failed to set secret {k}: {sec_res.stderr.strip()}")

    # 4. Enable GitHub Pages for workflow deployment
    print("Configuring GitHub Pages for GitHub Actions deployment...")
    pages_res = subprocess.run(
        [GH_PATH, "api", "-X", "POST", f"repos/{username}/{repo_name}/pages", "-f", "build_type=workflow"],
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True
    )
    if pages_res.returncode == 0:
        print("  [OK] GitHub Pages enabled for Actions.")
    else:
        print(f"  [INFO] GitHub Pages configuration status: {pages_res.stderr.strip() or 'Already enabled / requires initial run'}")

    # 5. Trigger manual workflow run
    print("Triggering manual workflow run for daily.yml...")
    trigger_res = subprocess.run(
        [GH_PATH, "workflow", "run", "daily.yml"],
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True
    )
    if trigger_res.returncode == 0:
        print("  [OK] Workflow run successfully triggered!")
    else:
        print(f"  [WARN] Workflow trigger message: {trigger_res.stderr.strip()}")

    pages_url = f"https://{username}.github.io/{repo_name}/"
    repo_url = f"https://github.com/{username}/{repo_name}"

    print("\n=== Deployment Summary ===")
    print(f"Repository URL: {repo_url} (Private)")
    print(f"Dashboard URL:  {pages_url}")
    print(f"Check runs:     {GH_PATH} run list")
    return True


if __name__ == "__main__":
    deploy_to_github()
