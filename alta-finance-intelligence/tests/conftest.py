import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import fixtures as fx  # noqa: E402


@pytest.fixture
def files(tmp_path):
    d = tmp_path / "inbox"
    d.mkdir()
    return {
        "gl": fx.gl_line_file(d / "NKC 2026-10 - Alta Plastic.xlsx"),
        "tb": fx.tb_file(d / "CDPS 2026-10 - Alta Plastic.xlsx"),
        "sales": fx.sales_file(d / "Bang ke ban hang 2026-10 - Alta Plastic.xlsx"),
        "pair": fx.gl_pair_file(d / "Bang ke chung tu 2026-10 - Alta Media.xlsx"),
        "dir": d,
    }


@pytest.fixture
def data(tmp_path):
    return tmp_path / "data"
