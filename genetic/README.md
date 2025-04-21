# GA‑Driven Long‑Only Strategy for `cad_ig_er_index`

## Quick‑start

```bash
# create or activate your environment then:
poetry install

# run the GA pipeline
poetry run python strategy_ga.py --csv monthly_all.csv

# view interactive audit charts in ./plots

# (optional) open the forthcoming Jupyter report once generated
poetry run jupyter lab cad_ig_er_report.ipynb
```

All random seeds are fixed at script start for reproducibility.
