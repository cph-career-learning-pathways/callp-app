===========================================================================================
# Git Workflow Command Reference

Quick reference for the Git commands commonly used in this project's development workflow.

===========================================================================================
## Configure Automatic Upstream Branches

Configure Git to automatically create a tracking relationship when pushing a new local branch for the first time:

```bash
git config --global push.autoSetupRemote true
```

This only needs to be configured once per development environment.

Afterward, the first push of a new branch can use:

```bash
git push
```

instead of:

```bash
git push -u origin <branch-name>
```

===========================================================================================
## Start New Work

Update `main`:

```bash
git switch main
git pull
```

Create and switch to a new branch:

```bash
git switch -c <branch-name>
```

Example:

```bash
git switch -c feature/42-skill-confidence
```

===========================================================================================
## Check Your Work

View changed and staged files:

```bash
git status
```

View unstaged changes:

```bash
git diff
```

View staged changes:

```bash
git diff --staged
```

===========================================================================================
## Commit Changes

### Stage Specific Files

Stage selected files:

```bash
git add <file>
```

### Stage All Changes

Stage all additions, modifications, and deletions in the repository:

```bash
git add -A
```

Review the staged changes before committing:

```bash
git status
```

### Commit Staged Changes

Commit the staged changes:

```bash
git commit -m "<commit message>"
```

Example:

```bash
git commit -m "Add skill confidence selection"
```

===========================================================================================
## Push Changes

If automatic upstream configuration has been enabled as described above, push the current branch with:

```bash
git push
```

Otherwise, the first push of a new branch requires:

```bash
git push -u origin <branch-name>
```

Subsequent pushes can use:

```bash
git push
```

After pushing a branch containing completed work, open a Pull Request into `main` on GitHub.

===========================================================================================
## Update an Existing Branch

If additional changes are requested during Pull Request review:

```bash
git add <file>
git commit -m "<commit message>"
git push
```

The existing Pull Request updates automatically.

===========================================================================================
## After a Pull Request Is Merged

Update local `main`:

```bash
git switch main
git pull
```

Delete the completed local branch:

```bash
git branch -d <branch-name>
```

The remote branch can be deleted using GitHub's **Delete branch** button after the Pull Request is merged.

===========================================================================================
## Useful Commands

### Check Repository Status

View the current branch and any staged, modified, or untracked files:

```bash
git status
```

### View Current Branch

Display the name of the currently checked-out branch:

```bash
git branch --show-current
```

### View Branches

View local branches:

```bash
git branch
```

View local and remote branches:

```bash
git branch -a
```

### View Recent Commit History

View the 10 most recent commits with shortened commit IDs and branch/tag references:

```bash
git log --oneline --decorate -10
```

View the 10 most recent commits as a branch graph:

```bash
git log --oneline --graph --decorate -10
```

### View Remote Configuration

View the repository's configured remote URLs:

```bash
git remote -v
```

===========================================================================================
