import csv
import re
from pathlib import Path
from typing import Tuple


CSV_DIR_PATH = 'data/raw/csv/'

# ELSTAT municipality codes
# as found in https://www.statistics.gr/statistics/-/publication/SKA01/-
MUN_CODES_PATH = 'data/raw/elstat_municipality_codes.csv'

OUT_PATH = 'data/municipalities/populations.csv'

def _parse_number(text: str) -> int:
    """Parses number with thousand separator, into integer."""
    return int(text.replace('.', ''))

def _extract_pop2011(text: str) -> Tuple[str, int]:
    """
    Extracts total 2011 population and municipality name from first CSV column.

    ELSTAT's tables in the booklet have a form similar to this:
    | Δήμος              2011 |   2021 | ... |
    | ΚΟΜΟΤΗΝΗΣ        66.919 | 65.107 | ... |

    i.e. the municipality name and its 2011 population aren't separated by a
    visible line, therefore Camelot is unable to split them into separate
    columns and the output CSVs have first columns of the following form:
    "ΚΟΜΟΤΗΝΗΣ\n66.919".

    Another case is when the municipality name is long enough to occupy two
    lines:
    | Δήμος             2011 |   2021 | ... |
    | ΑΜΠΕΛΟΚΗΠΩΝ -   52.127 | 49.674 | ... |
    | ΜΕΝΕΜΕΝΗΣ              |        | ... |

    where Camelot produces a first column of this form:
    "ΑΜΠΕΛΟΚΗΠΩΝ -  \n52.127\nΜΕΝΕΜΕΝΗΣ"

    This function extracts the two attributes from the first column text and
    cleans them.

    Args:
        text: First column text.

    Returns:
        A tuple (municipality_name, pop2011) where municipality_name is the
        municipality name as a string and pop2011 is the 2011 population total
        as an integer.

    Raises:
        ValueError: If the column text is not of the expected format.
    """
    POPULATION_REGEX = r'((?:\d+\.)*\d+)'

    m = re.search(POPULATION_REGEX, text)
    try:
        pop2011 = _parse_number(m.group(1))
    except (AttributeError, IndexError):
        raise ValueError(f'No population number found in first column: {text}') from None

    municipality_name = re.sub(POPULATION_REGEX, '', text)
    municipality_name = re.sub('\s+', ' ', municipality_name).strip()

    return municipality_name, pop2011


def main():
    # reverse lookup name => code
    with open(MUN_CODES_PATH, 'r', encoding='utf-8') as fp:
        mun_codes = {name: code for code, name in csv.reader(fp)}

    with open(OUT_PATH, 'w', newline='') as outfile:
        fieldnames = [
            'elstat_municipality_code', 'municipality_name', 'pop_total_2021',
            'pop_total_2011', 'pop_men_2021', 'pop_men_2011', 'pop_women_2021',
            'pop_women_2011',
        ]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)

        writer.writeheader()
        for p in Path(CSV_DIR_PATH).glob('mun*.csv'):
            with open(p, 'r', encoding='utf-8') as infile:
                for row in csv.reader(infile):
                    if not row[0]:
                        # Skip empty rows
                        continue

                    # In some cases, columns 2-5 are incorrectly parsed as one,
                    # split by newlines
                    if '\n' in row[2]:
                        row = [
                            row[0],
                            row[1],
                            *row[2].split('\n'),
                        ]

                    mun, pop2011 = _extract_pop2011(row[0])
                    try:
                        writer.writerow({
                            'elstat_municipality_code': mun_codes.get(mun, ''),
                            'municipality_name': mun,
                            'pop_total_2021': _parse_number(row[1]),
                            'pop_total_2011': pop2011,
                            'pop_men_2021': _parse_number(row[3]),
                            'pop_men_2011': _parse_number(row[2]),
                            'pop_women_2021': _parse_number(row[5]),
                            'pop_women_2011': _parse_number(row[4]),
                        })
                    except:
                        raise ValueError(f'Could not parse row {row}') from None


if __name__ == '__main__':
    main()
