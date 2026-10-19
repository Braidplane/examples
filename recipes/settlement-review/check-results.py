"""Compare every synthetic destination field without calling a provider."""
import json
import sys
from pathlib import Path

comparisons = json.loads(Path(sys.argv[1]).read_text())["rows"]
totals = json.loads(Path(sys.argv[2]).read_text())["rows"]
expected = json.loads((Path(__file__).parent / "expected.json").read_text())
assert sorted(comparisons, key=lambda row: row["line_id"]) == expected["comparisons"], "Comparison rows differ from the synthetic expectation"
assert totals == expected["totals"], "Batch totals differ from the synthetic expectation"
print("PASS: 3 complete comparisons, missing match preserved as NULL, refund difference 500, one correct batch total")
