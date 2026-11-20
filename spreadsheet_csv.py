"""Write spreadsheet-facing CSV files with formula neutralization."""

import csv
import re


FORMULA_PREFIX = re.compile(r"^[\s\ufeff]*[=+\-@＝＋－＠\t\r\n]")


def _spreadsheet_cell(value):
    if isinstance(value, str) and FORMULA_PREFIX.match(value):
        return "'" + value
    return value


def write_spreadsheet_csv(file, headers, rows):
    """Quote cells and mark potentially formula-like fields as text."""
    writer = csv.writer(file, quoting=csv.QUOTE_ALL)
    writer.writerow(_spreadsheet_cell(header) for header in headers)
    writer.writerows((_spreadsheet_cell(cell) for cell in row) for row in rows)
