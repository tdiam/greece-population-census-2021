import csv
import re
from pathlib import Path
from typing import List, Tuple


CSV_DIR_PATH = 'data/raw/csv/'

# NUTS2 (2021) administrative region codes
# as per https://eur-lex.europa.eu/legal-content/EN/TXT/?qid=1571919890809&uri=CELEX:32019R1755
ADM_CODES_PATH = 'data/raw/nuts2_region_codes.csv'

OUT_PATH = 'data/adm_regions/populations.csv'

def _parse_number(text: str) -> int:
    """Parses number with thousand separator, into integer."""
    return int(text.replace('.', ''))

def _extract_pops(text: str) -> Tuple[str, List[int]]:
    """
    Extracts population numbers and region name from CSV column.

    ELSTAT's table in the booklet has a form similar to this:
    Περιφέρειες        2011     2021   ...
    Ηπείρου         336.856  319.543   ...

    i.e. columns aren't separated by visible lines, therefore Camelot is unable
    to split them into separate columns and the output CSV only has a column
    of this form: "ΗΠΕΙΡΟΥ\n336.856\n319.543\n...".

    This function extracts the name and the population numbers from the text.

    Args:
        text: First column text.

    Returns:
        A tuple (region_name, populations) where region_name is the
        adminstrative region name as a string and populations is a list
        containing the numbers from the six columns as integers.

    Raises:
        ValueError: If the column text is not of the expected format.
    """
    POPULATION_REGEX = r'((?:\d+\.)*\d+)'

    populations = [_parse_number(p) for p in re.findall(POPULATION_REGEX, text)]

    region_name = re.sub(POPULATION_REGEX, '', text)
    region_name = re.sub('\s+', ' ', region_name).strip()

    return region_name, populations


def main():
    # reverse lookup name => code
    with open(ADM_CODES_PATH, 'r', encoding='utf-8') as fp:
        adm_codes = {name: code for code, name in csv.reader(fp)}

    with open(OUT_PATH, 'w', newline='') as outfile:
        fieldnames = [
            'region_code', 'region_name', 'pop_total_2021',
            'pop_total_2011', 'pop_men_2021', 'pop_men_2011', 'pop_women_2021',
            'pop_women_2011',
        ]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)

        writer.writeheader()
        for p in Path(CSV_DIR_PATH).glob('adm*.csv'):
            with open(p, 'r', encoding='utf-8') as infile:
                for row in csv.reader(infile):
                    region_name, pops = _extract_pops(row[1])
                    try:
                        writer.writerow({
                            'region_code': adm_codes.get(region_name, ''),
                            'region_name': region_name,
                            'pop_total_2021': pops[1],
                            'pop_total_2011': pops[0],
                            'pop_men_2021': pops[3],
                            'pop_men_2011': pops[2],
                            'pop_women_2021': pops[5],
                            'pop_women_2011': pops[4],
                        })
                    except:
                        raise ValueError(f'Could not parse row {row}') from None


if __name__ == '__main__':
    main()
