# Hackathon setup (for us, not for Claude)

## Which model to use (Claude Pro)
- Run `/model opusplan` in Claude Code. It uses **Opus** while planning and switches to **Sonnet** to write and run code, which keeps strong reasoning where it matters while using less of the Pro plan's usage limit.
- Switch to `/model opus` only when stuck on a hard bug or a key design decision, then switch back.
- Pro has usage limits, and six hours of heavy use can hit them. Each of us signs in with our own account so we have two separate limits. If one of us gets limited, the other keeps going.

## Tonight (both laptops, ~20 minutes)
- [ ] Install the **Claude Code** extension in VS Code (Extensions view, search "Claude Code"), open it and sign in with your Claude account.
- [ ] Python 3.10+ works: `python3 --version`
- [ ] `pip install -r requirements.txt`
- [ ] GitHub works from the terminal: install GitHub CLI and run `gh auth login`, or confirm `git push` works on any repo.
- [ ] **Dry run (10 min):** make a throwaway repo from this folder, open it in VS Code, and ask Claude:
  *"Run `python src/baseline_template.py --demo`, tell me what the results show, then commit everything with message 'dry run'."*
  Then push yourself: `git push`. If that whole loop works, we're ready.
- [ ] Copy the Kaggle API token (`kaggle.json`) to `~/.kaggle/` in case the data is on Kaggle. Never put it in the repo.
- [ ] Charge laptops, pack chargers and an extension cable. Phone hotspot as backup Wi-Fi.

## When the hackathon starts
1. One of us creates the **public** GitHub repo, copies this starter folder into it, and pushes. The other clones it.
2. Fill in `data/README.md`, download the data into `data/`.
3. Open the repo in VS Code, open Claude Code, run `/model opusplan`, then send the kickoff message below.
4. Split the work so we don't edit the same files:
   - Person A: `src/eda.py`, `figures/`, `REQUIREMENTS.md`, README
   - Person B: `src/models.py` (start from `baseline_template.py`), tuning
   - Pull before starting each new task: `git pull`
5. Commit after every milestone. Push at least every hour. **We do the final push ourselves**, at least 20 minutes before the cutoff, then check the repo in a logged-out browser window.

## Kickoff message (paste into Claude Code)
```
The hackathon just started. Follow CLAUDE.md.
Time now: <hh:mm>. Cutoff: <hh:mm>.

BRIEF (verbatim):
<paste the whole brief>

DATA: files are in data/: <names>.

Start with the kickoff phase: write REQUIREMENTS.md, state the task type, target
and ranking metric, and propose a timed plan. Use /plan first.
```

## Short prompts for the day
| When | Send |
|---|---|
| After a run | "What does this output tell us, and what's next?" |
| Error | "Minimal fix for this error." |
| Score looks too good | "Validation is X. Run a leakage check." |
| Stuck | "Results table is in results/results.csv, Y hours left. Ranked ideas to improve the ranking metric." |
| Time check | "It's hh:mm. What's left in REQUIREMENTS.md?" |
| Write-up | "Fill README.md from results/results.csv and figures/." |
| Final | "Run the final audit from CLAUDE.md." |
