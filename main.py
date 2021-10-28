"""
Selects the rides which started from Manhattan and ended in John Fitzgerald Kennedy International Airport
from the whole NYC Taxi Dataset: http://www.nyc.gov/html/tlc/html/about/trip_record_data.shtml
"""
from filtering_utils import *

df_cols = unique_file_cols()
filegroups = divide_files_bycols(df_cols)


def main():
    for filename in os.listdir(PATH_DATA):
        info_log(filename)
        select_rides(filegroups, filename)
        info_log('='*30)

if __name__ == "__main__":
    main()