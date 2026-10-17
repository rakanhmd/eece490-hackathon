# Requirements checklist (quoted from the brief)

| # | Requirement (brief wording) | Status | Where we meet it |
|---|---|---|---|
| 1 | "Choose a business problem that matters." | Met | README: The business problem; Conclusion |
| 2 | "Support your conclusions with evidence. Check data quality and test alternative explanations." | Met | data/README.md (data quality); README findings 4 (five artifact tests), 6 (placebos, control choice, pre-trend), 7 (random-assignment null), 8 (adjusted tests, reshuffle null) |
| 3 | "Estimate business value, costs, and tradeoffs. Explain which assumptions could change the recommended action." | Met | README: Estimated business value (elasticity and attach-rate ranges, break-even points); Assumptions table |
| 4 | "If you build a model, compare it with a simple baseline. Test it on data it did not use for training." | Met | README finding 5; `src/forecast.py`; `results/forecast_mae.csv`, `results/results.csv`. Model chosen on May, tested once on June, against "same weekday last week" and a dummy |
| 5 | "Explain weak areas, uncertainty, and possible failures. Identify missing information and a practical test Stories could run before wider use." | Met | README: Weak areas and uncertainty; A practical test Stories could run |
| 6 | "Do not present correlation as proof of cause." | Met | README finding 6 (promo not credited with the rise), finding 8 (no claim that a prompt works; a test is proposed instead) |
| 7 | "Keep measured results separate from estimated benefits." | Met | README: Measured findings vs Estimated business value; ranked table marks each row measured or estimated |
| 8 | "Explain your important choices and the approaches you rejected." | Met | README: Approaches we considered and rejected |
| 9 | "Make all assumptions you need to proceed. State each assumption clearly. Explain how important assumptions affect your conclusions. Keep assumptions separate from observed facts." | Met | README: Assumptions and what would change the recommendation |
| 10 | "Submit one public GitHub repository URL per team (with names of team members clear)." | Met; recheck after the final push | README header names both members; repo confirmed public |
| 11 | "Make your evidence easy to inspect." | Met | One script per finding in `src/`, tables in `results/`, figures in `figures/`; README cites the source of each finding |
| 12 | "Basic sales summaries and a 'query my database' interface will not earn credit on their own." | Met | Each finding ends in a decision: costs, prices, discounts, staffing, cross-sell |
