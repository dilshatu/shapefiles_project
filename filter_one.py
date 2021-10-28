"""
Selects the rides which started from Manhattan and ended in John Fitzgerald Kennedy International Airport
from given csv file in cmd command
It takes approx. 20 seconds per 500K rows (~0,04 ms per row)
Hardware: Intel(R) Core(TM) i5-7300HQ, 8GB RAM CPU
"""
from filtering_utils import *
import sys

df_cols = unique_file_cols()
filegroups = divide_files_bycols(df_cols)


try:
    filename = sys.argv[1]
except Exception as e:
    error_log('Please specify filename you want to filter :: {}'.format(e))


def main():
    select_rides(filegroups, filename)


if __name__ == "__main__":
    main()