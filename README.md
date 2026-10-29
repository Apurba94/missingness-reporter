# missingness-reporter

**See how your data are missing, not just how much: per-column and per-row counts, the most
common missingness patterns, variables that go missing together, and hints of non-random missingness.**

Part of the *Research Automation Toolkit*: 100 open tools for daily research work.

## Why

Reporting guidelines (STROBE, CONSORT) require describing missing data, and the right handling
(complete-case analysis, multiple imputation, sensitivity analyses) depends on its pattern. If income
is missing mostly for older participants, data are not missing completely at random and complete-case
estimates may be biased. This report gives the overview needed for that decision and for the methods section.

## Features

- Recognizes blanks and common codes (`NA`, `-99`, `-999`, `.`, `null` ...), plus custom `--codes`
- Missing count and percent per column (with text bars), complete rows, distribution of missing per row
- Top missingness patterns (which combinations of columns are missing together)
- Co-missingness pairs with phi correlation of missing indicators
- Screening for MAR-type dependence: mean of numeric variables when another variable is missing
  vs observed (Welch t; a heuristic, not Little's formal MCAR test)
- Markdown or JSON output

## Usage

```bash
pip install .
missingness-reporter cohort.csv -o missing_report.md
missingness-reporter survey.csv --codes 999,unknown --json
```

## Testing

```bash
python -m unittest discover -s tests -t .
```

## License

MIT (c) JANIN A APURBA
