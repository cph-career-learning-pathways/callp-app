# Contributing

## Workflow

For commonly used Git commands, see [Git Workflow Command Reference](docs/git-workflow.md).

1. Select or create an Issue in the repository.
2. Assign the Issue and set its Labels, Type, Priority, and Target Date (at minimum).
3. Set the Issue to **In Progress** when beginning work.
4. Create a branch from the latest `main`.
5. Make, test, and commit your changes on branch.
6. Push the branch to GitHub.
7. Open a Pull Request into `main` and link the related Issue.
8. Have at least one other teammate review and approve the Pull Request.
9. Address any requested changes.
10. Squash and merge the Pull Request.

Do not commit or push development work directly to `main`.

## Branches

Before creating a branch:

```bash
git switch main
git pull
git switch -c <branch-name>
```

Use descriptive names and include the Issue number when practical:

```text
feature/42-skill-confidence
fix/57-mobile-navigation
research/63-linkedin-integration
docs/31-update-readme
chore/repository-setup
```

## Pull Requests

After pushing your branch, use **Compare & pull request** on GitHub, or go to **Pull requests → New pull request**.

The Pull Request should target `main` and include:

```markdown
Resolves #<issue-number>

## Summary

Briefly describe the changes.
```

Only use `Closes` when the Pull Request fully completes the linked Issue.

At least one other teammate must review and approve the Pull Request. If changes are requested, commit and push them to the same branch; the existing Pull Request will update automatically.

Once approved, the Pull Request author should use **Squash and merge**.

## After Merging

After the Pull Request is merged, delete the remote branch using GitHub's **Delete branch** button.

Then update your local repository:

```bash
git switch main
git pull
git branch -d <branch-name>
```

## Definition of Done

Work is considered complete when:

- The Issue's acceptance criteria or expected outcome are satisfied.
- Relevant changes have been tested.
- Necessary documentation has been updated.
- The Pull Request has been reviewed, approved, and merged into `main`.