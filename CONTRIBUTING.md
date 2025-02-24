# Contribution Guidelines

## General Rules
- Follow the structured issue templates when reporting bugs or suggesting features.
- Keep commits atomic (one logical change per commit).
- Follow the commit message format outlined below.
- Use branches for feature development and bug fixes.
- Follow the merge process to ensure a clean and stable repository.

---

# Issue Guidelines

## Bug Reports
- Clearly describe the issue, including:
  - Steps to reproduce
  - Expected behavior
  - Actual behavior
  - Logs, screenshots, or error messages
- Assign appropriate severity and urgency labels.
- Ensure the issue is not a duplicate before submitting.

## Feature Requests
- Clearly describe the problem being solved.
- Provide use cases or examples.
- Suggest possible implementations if applicable.

---

# Commit Guidelines

## Commit Message Format
```
<type>: <short description>

<detailed explanation (if needed)>

Fixes: #<issue_number> (if applicable)
```
### Example:
```
fix: resolve crash on startup

The issue was caused by an unhandled null reference. This commit adds a proper null check.

Fixes: #42
```
### Commit Types:
- `feat:` – A new feature
- `fix:` – A bug fix
- `docs:` – Documentation changes
- `refactor:` – Code restructuring without changing behavior
- `test:` – Adding or updating tests
- `chore:` – Maintenance tasks like dependency updates

---

# Merge Guidelines

## Merge Workflow
1. Ensure all commits follow the commit guidelines.
2. Ensure CI/CD checks pass before merging.
3. Merge with **Squash and Merge** unless preserving history is necessary.
4. Use clear merge messages summarizing the changes.
5. Delete the feature branch after merging if no longer needed.

## When to Rebase Instead of Merge
- If the branch has diverged significantly from `main`, prefer rebasing to avoid merge conflicts.
- Use `git rebase main` instead of `git merge main` when keeping a linear history.

---

By following these guidelines, we ensure a structured and maintainable development process.

