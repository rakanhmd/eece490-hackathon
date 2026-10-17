# Requirements checklist (quoted from the brief)

| # | Requirement (brief wording) | Status | Where we meet it |
|---|---|---|---|
| 1 | "Choose a business problem that matters." | Met | README: Bottom line: three actions; The business problem; Decisions |
| 2 | "Support your conclusions with evidence. Check data quality and test alternative explanations." | Met | data/README.md (data quality); README findings 4 (recording-error tests), 6 (placebos, control choice), 7 (random-assignment null), 8 (FINDING_8.md); Did outside factors cause this? (table) |
| 3 | "Estimate business value, costs, and tradeoffs. Explain which assumptions could change the recommended action." | Met | README: Decisions (thresholds in `results/decision_thresholds.csv`, break-even implementation cost); Estimated business value; Assumptions and what would change the recommendation; docs/estimates_detail.md |
| 4 | "If you build a model, compare it with a simple baseline. Test it on data it did not use for training." | Met | README finding 5; [docs/forecast.md](docs/forecast.md); `src/forecast.py`. Rolling origin (fit up to each day, predict 7 days ahead, 1 Mar–23 Jun) against "same weekday last week" and a dummy, with block-bootstrap intervals; the earlier May-validation / June-test split is kept as a check |
| 5 | "Explain weak areas, uncertainty, and possible failures. Identify missing information and a practical test Stories could run before wider use." | Met | README: Weak areas and uncertainty; Pilots, staffing, menu and customers (EXPERIMENTS.md: simulated pilots with power, false positives and rules) |
| 6 | "Do not present correlation as proof of cause." | Met | README finding 6 (promo not credited with the rise), finding 4 (Tuesday mechanism not identified), Did outside factors cause this? (verdict vs still possible) |
| 7 | "Keep measured results separate from estimated benefits." | Met | README: Measured findings vs Decisions and Estimated business value (estimates labelled with their assumptions) |
| 8 | "Explain your important choices and the approaches you rejected." | Met | README: Approaches we considered and rejected |
| 9 | "Make all assumptions you need to proceed. State each assumption clearly. Explain how important assumptions affect your conclusions. Keep assumptions separate from observed facts." | Met | README: Assumptions and what would change the recommendation |
| 10 | "Submit one public GitHub repository URL per team (with names of team members clear)." | Met; recheck after the final push | README header names both members; repo confirmed public |
| 11 | "Make your evidence easy to inspect." | Met | One script per finding in `src/`, tables in `results/`, figures in `figures/`; README cites the source of each finding |
| 12 | "Basic sales summaries and a 'query my database' interface will not earn credit on their own." | Met | README Decisions: each area ends in a decision (costs, prices, Tuesday, prompts, discount, promo, win-back) |
