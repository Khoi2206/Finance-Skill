import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
TOOL = HERE.parent
REPO = TOOL.parents[1]
for p in (TOOL, REPO / "alta-finance-intelligence" / "src", REPO / "alta-finance-intelligence" / "tests"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from boardpack.sample import build_warehouse, write_plan  # noqa: E402


@pytest.fixture(scope="session")
def group(tmp_path_factory):
    """Warehouse tổng hợp 01/2025–10/2026 (tests/fixtures.py · group_dataset); APL 10/2026 đã được CFO duyệt."""
    from boardpack.facts import Facts
    work = tmp_path_factory.mktemp("group")
    wh = build_warehouse(work, approve=[("APL", "2026-10")])
    plan = write_plan(Facts(wh), 2026, work / "plan_2026.csv")
    return {"wh": wh, "plan": plan, "data": work / "data"}
