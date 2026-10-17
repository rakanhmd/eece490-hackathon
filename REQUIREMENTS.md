# Requirements checklist (quoted from the brief)

| # | Requirement (brief wording) | Where we meet it |
|---|---|---|
| 1 | "Choose a business problem that matters." | README: The business problem |
| 2 | "Support your conclusions with evidence. Check data quality and test alternative explanations." | data/README.md; each finding's checks |
| 3 | "Estimate business value, costs, and tradeoffs. Explain which assumptions could change the recommended action." | README: Estimated business value; Assumptions |
| 4 | "If you build a model, compare it with a simple baseline. Test it on data it did not use for training." | src/forecast.py; results/results.csv |
| 5 | "Explain weak areas, uncertainty, and possible failures. Identify missing information and a practical test Stories could run before wider use." | README: Weak areas; Practical test |
| 6 | "Do not present correlation as proof of cause." | README wording; promo diff-in-diff and placebos |
| 7 | "Keep measured results separate from estimated benefits." | README: Measured findings vs Estimated business value |
| 8 | "Explain your important choices and the approaches you rejected." | README: Approaches we considered and rejected |
| 9 | "Make all assumptions you need to proceed. State each assumption clearly. Explain how important assumptions affect your conclusions. Keep assumptions separate from observed facts." | README: Assumptions table |
| 10 | "Submit one public GitHub repository URL per team (with names of team members clear)." | README header; repo visibility checked at the end |
| 11 | "Make your evidence easy to inspect." | Tables in results/, figures in figures/, one script per finding |
| 12 | "Basic sales summaries and a 'query my database' interface will not earn credit on their own." | Findings are decisions, not summaries |
