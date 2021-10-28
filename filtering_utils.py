import shapefile
import numpy as np
import matplotlib.path as mpltPath
from time import time
import os
import pandas as pd
import yaml

CONFIG_FILE = 'config.yml'


def info_log(msg):
    print(msg)


def error_log(msg):
    print(msg)
    raise msg


# -------------------------Reading config file-------------------------


try:
    info_log('Reading config file...')
    ymlfile = open(CONFIG_FILE, 'r')
    config = yaml.load(ymlfile)

    # ----------------Declaration of global variables-----------------

    PATH_CD = config['paths']['PATH_CD']  # path to shapefile of nyc districts
    PATH_BB = config['paths']['PATH_BB']  # path to shapefile of nyc boroughs
    PATH_AP = config['paths']['PATH_AP']  # path to shapefile of nyc airports
    PATH_DATA = config['paths']['PATH_DATA']  # path to nyc taxi dataset (csv files)
    PATH_RESULT = config['paths']['PATH_RESULT']  # path to folder, where filtered files will be stored
    PATH_TAXI_ZONES = config['paths'][
        'PATH_TAXI_ZONES']  # path to file mapping of location IDs and names - taxi_zone_lookup.csv
    PATH_TMP = config['paths']['PATH_TMP']  # path to files generated while analysis

    cd = shapefile.Reader(PATH_CD)
    bb = shapefile.Reader(PATH_BB)
    jfk = mpltPath.Path(cd.shape(35).points)
    mn = mpltPath.Path(bb.shape(0).points)

    loc_ids = pd.read_csv(PATH_TAXI_ZONES)
    jfk_loc_id = loc_ids.iloc[np.where(loc_ids['Zone'].str.lower().str.contains('jfk') == True)[0]]['LocationID'].values
    manhattan_loc_ids = loc_ids.iloc[np.where(loc_ids['Borough'].str.lower().str.contains('manhattan') == True)[0]][
        'LocationID'].values

    all_columns = config['columns']['ALL_COLUMNS']
    selected_columns = config['columns']['SELECTED_COLUMNS']

    chunksize = config['files']['chunksize']
    info_log('Config file read successfully')

except Exception as e:
    error_log('Config file is missed: {}'.format(e))


# -------------------------Scripts for rides filtering-------------------------


def ensure_folder_exists(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)


prev_cols = []


def read_cols(filename, df_cols, path=PATH_DATA):
    """
    Extract column names from given file to make dictionary of unique column names only
    :param filename: csv file, located in path
    :param df_cols:  global dictionary
    """
    global prev_cols
    df = pd.read_csv(os.path.join(path, filename), nrows=0)
    cols = list(df.columns)
    if cols != prev_cols:
        df_cols[filename] = tuple(cols)
        prev_cols = cols


def unique_file_cols(path=PATH_DATA):
    """
    Extract unique sets of column names with corresponding file names in order they occur in path
    :param path: path to csv files (nyc taxi dataset)
    :return: dictionary of pairs (filename, columns) - only unique sets of column names
    """
    df_cols = {}
    for filename in os.listdir(path):
        read_cols(filename, df_cols)
    return df_cols


def divide_files_bycols(cols, path=PATH_DATA):
    """
    Make group of files by their column names and content
    :param cols: dictionary of pairs (filename, columns) - output of unique_file_cols() function
    :param path: path to csv files (nyc taxi dataset)
    :return: 15 groups of files
    """
    files = []
    tmp_files = []
    filegroups = []
    for file_name in os.listdir(path):
        if file_name in list(cols.keys()):
            if tmp_files:
                files.append(tmp_files)
            tmp_files = []
            tmp_files.append(file_name)
        else:
            tmp_files.append(file_name)
    files.append(tmp_files)

    filegroups.append(files[0])
    filegroups.append(files[1])
    filegroups.append(files[2])
    filegroups.append(files[3])
    filegroups.append(files[4][:6])
    filegroups.append(files[4][6:])
    filegroups.append(files[5][:6])
    filegroups.append(files[5][6:])
    filegroups.append(files[6])
    filegroups.append(files[7])
    filegroups.append(files[8])
    filegroups.append(files[9])
    filegroups.append(files[10])
    filegroups.append(files[11][:6])
    filegroups.append(files[11][6:])
    return filegroups


def dateparse(x):
    """
    Auxiliary function to parse dates into specific datetime format when downloading csv file
    """
    if not pd.isnull(x):
        return pd.datetime.strptime(x, '%Y-%m-%d %H:%M:%S')
    else:
        return x


def select_rides(filegroups, file_name, path=PATH_DATA, save_path=PATH_RESULT, columns=all_columns,
                 selected=selected_columns):
    """
    Selects the rides which started from Manhattan and ended in John Fitzgerald Kennedy International Airport
    from given csv file (of nyc taxi dataset)
    :param filegroups: groups of files by their columns names and content - output of divide_files_bycols()
    :param file_name: given csv file (nyc taxi dataset)
    :param path: path to all csv files (nyc taxi dataset)
    :param save_path: path to folder, where filtered files will be stored
    :param columns: all columns set per each filegroup (from filegroups)
    :param selected: selected columns (PUdatetime, PUlocation, DOlocation) per each filegroup (from filegroups)
    :return:
    """
    t0 = time()
    mn2jfk = pd.DataFrame()
    ensure_folder_exists(save_path)

    if file_name in filegroups[0]:
        info_log('File {} doesn\'t contain all required information (date, PU and DO locations) and therefore '
                 'ignored'.format(file_name))

    for k in range(1, len(filegroups)):
        if file_name in filegroups[k]:
            file_path = os.path.join(path, file_name)
            reader = pd.read_csv(file_path,
                                 header=0,
                                 names=columns[k - 1],
                                 parse_dates=[1],
                                 date_parser=dateparse,
                                 chunksize=chunksize)
            for i, df in enumerate(reader):
                df = df.dropna(subset=list(selected[k - 1]))
                t1 = time()
                info_log('#{} chunk of file {} is read. Chunksize = {}'.format(i, file_name, df.shape[0]))

                if len(selected[k - 1]) == 3:
                    mn2jfk_tmp = df.loc[lambda df: df[selected[k - 1][1]].isin(manhattan_loc_ids)
                                                   & df[selected[k - 1][2]].isin(jfk_loc_id)]
                    mn2jfk = mn2jfk.append(mn2jfk_tmp)
                    t2 = time()
                    info_log('#{} chunk processed in {} seconds'.format(i, t2 - t1))

                else:
                    mn2jfk_tmp = df.loc[
                        lambda df: mn.contains_points(df[[selected[k - 1][1], selected[k - 1][2]]])
                                   & jfk.contains_points(df[[selected[k - 1][3], selected[k - 1][4]]])]
                    mn2jfk = mn2jfk.append(mn2jfk_tmp)
                    t2 = time()
                    info_log('#{} chunk processed in {} seconds'.format(i, t2 - t1))

            mn2jfk.to_csv(os.path.join(save_path, file_name))
            t3 = time()
            info_log('Whole processing of {} took {} minutes'.format(file_name, (t3 - t0) / 60))