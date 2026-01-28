# Worktree setup (local)

This repo uses a dedicated worktree so new commands can be built in isolation
and still be backed up to Git.

## Folders and branches
- Main repo: a subfolder inside the Fusion folder (example: `C:\Users\phil9\Documents\02 - Fusion\Fusion-360-rules-and-lessons`)
  - Branch: `main` (stable)
- Development worktree: a sibling subfolder inside the Fusion folder (example: `C:\Users\phil9\Documents\02 - Fusion\InDevelopment`)
  - Branch: `feature/in-development` (based on `origin/PhilsDesignTools`)

## Daily workflow
1. Open the `InDevelopment` folder in VS Code for new command work.
2. Commit often and push the feature branch for backup.
3. When ready, merge into `PhilsDesignTools` (or open a PR), then later update `main`.

## Useful commands
- List worktrees:
  `git worktree list`
- Create the dev worktree (from the main repo folder):
  `git fetch --all --prune --tags`
  `git worktree add ..\InDevelopment feature/in-development`
- Push the feature branch:
  `git push -u origin feature/in-development`
- Update the worktree with latest `PhilsDesignTools`:
  `git fetch --all --prune --tags`
  `git merge origin/PhilsDesignTools`
- Remove the worktree (when finished):
  `git worktree remove <path-to-InDevelopment>`
  `git branch -d feature/in-development`

## Notes
- Untracked/ignored local files are not shared between worktrees. Copy any
  local-only folders (for example `Addin\_external`) if you need them there.
- This repo contains two add-ins:
  - `Addin/PhilsDesignTools` (Fusion Add-Ins folder)
  - `PhilsBom` (distribution zip + install notes; source bundle lives in the InDevelopment worktree)
