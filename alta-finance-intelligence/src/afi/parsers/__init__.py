from .gl_journal import parse as parse_gl_journal
from .sales_list import parse as parse_sales_list
from .trial_balance import parse as parse_trial_balance

PARSERS = {"gl_journal": parse_gl_journal, "trial_balance": parse_trial_balance, "sales_list": parse_sales_list}
