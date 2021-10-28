"""
Utilities for plotting and analyzing resulted data
Used in the enclosed iPython Notebook "analysis and visualization"
"""

from filtering_utils import *
import matplotlib.pyplot as plt
import seaborn as sns
import pickle

# -------------------------Declaration of global variables-------------------------


info_log('Initializing variables... ')
ensure_folder_exists(PATH_TMP)

path_filegroups = os.path.join(PATH_TMP, 'filegroups.pkl')
if os.path.exists(path_filegroups):
    filegroups = pickle.load(open(path_filegroups, 'rb'))
else:
    df_cols = unique_file_cols()
    filegroups = divide_files_bycols(df_cols)
    pickle.dump(filegroups, open(path_filegroups, 'wb'))

airports = shapefile.Reader(PATH_AP)
info_log('Variables successfully initialized')


# -------------------------Scripts for visualization and analysis-------------------------


def plot(shape_ex, t=None):
    """
    Plots areas from shapefile
    :param shape_ex: shape from given shapefile
    :param t: indicator of Manhattan or JFK airport
    """
    x_lon = np.zeros((len(shape_ex.points), 1))
    y_lat = np.zeros((len(shape_ex.points), 1))
    for ip in range(len(shape_ex.points)):
        x_lon[ip] = shape_ex.points[ip][0]
        y_lat[ip] = shape_ex.points[ip][1]
    if t == 'MN':
        plt.plot(x_lon, y_lat, 'r--', label='Manhattan')
    elif t == 'JFK':
        plt.plot(x_lon, y_lat, 'b--', label='JFK airport district')
    else:
        plt.plot(x_lon, y_lat, 'k')


def get_PU_DO(filename):
    """
    Retrieves dates and Pickup/Dropoff locations form a given file with full information
    :param filename: csv file with full information
    :return: dates and Pickup/Dropoff locations
    """
    df_loc = pd.DataFrame()
    for k in range(1, len(filegroups)):
        if filename in filegroups[k]:
            df_loc = pd.read_csv(os.path.join(PATH_RESULT, filename), usecols=selected_columns[k - 1], parse_dates=[0],
                                 date_parser=dateparse_mdy)
            df_loc.columns = ['DATE', 'PU_lon', 'PU_lat', 'DO_lon', 'DO_lat'] if len(df_loc.columns) == 5 else ['DATE',
                                                                                                                'PU_ID',
                                                                                                                'DO_ID']
    return df_loc


def dateparse_mdy(x):
    """
    Auxiliary function to parse dates into specific datetime format when downloading csv file
    """
    if not pd.isnull(x):
        return pd.datetime.strptime(x, '%Y-%m-%d %H:%M:%S').date()
    else:
        return x


def rides_per_day(filtered_file, path=PATH_RESULT):
    """

    :param filtered_file:
    :param path:
    :return:
    """
    file_path = os.path.join(path, filtered_file)
    df = pd.read_csv(file_path,
                     parse_dates=[2],
                     date_parser=dateparse_mdy)
    return df.groupby('PickUp_datetime').size().reset_index(name='counts')


def plot_by_lvl(rides, data, c = 'PRCP', bins=None, plot_c=True, labels=None):
    rides.index.name = 'DATE'
    stats = pd.merge(rides, data, on='DATE')
    n = len(stats[c].unique())
    c_stats = stats[['DATE', 'counts', c]]
    c_stats['level'] = pd.qcut(c_stats[c], q=n, duplicates='drop')
    if not bins:
        bins = c_stats['level'].dropna().unique().categories
        a = list(sorted(c_stats['level'].dropna().unique()))
        if a[0].left < 0:
            s1 = pd.Interval(a[0].left, 0, closed='right')
            s2 = pd.Interval(0, a[0].right, closed='right')
            a.pop(0)
            a.insert(0, s2)
            a.insert(0, s1)
            bins = pd.IntervalIndex(a)
    c_stats['level'] = pd.cut(c_stats[c], bins=bins, labels=labels)
    if plot_c:
        ax = c_stats.groupby('level').mean()['counts'].plot(kind='bar',
                                                            figsize=(20,5),
                                                            fontsize=13,
                                                            colormap='summer',
                                                            title=c+' vs Taxi rides from Manhattan to JFK')
        ax.set_xlabel(c, fontsize=15)
        ax.set_ylabel("Average daily taxi rides", fontsize=15)
    return c_stats


def vis_rides_by_prcp(locations, k, rides, weather):
    prcp = plot_by_lvl(rides, weather, c = 'PRCP', bins=k, plot_c=False, labels=False)
    rpg = pd.merge(locations, prcp, on='DATE')
    plt.figure(figsize=(15,10))
    ax = plt.axes()
    ax.set_aspect('equal')
    colors = sns.color_palette(None, k)
    for i in range(len(colors)):
        plt.plot(rpg[rpg['level']==i]['PU_lon'], rpg[rpg['level']==i]['PU_lat'], '.', color=colors[i],
                 label="PRCP level {}".format(i))
        plt.plot(rpg[rpg['level']==i]['DO_lon'], rpg[rpg['level']==i]['DO_lat'], '.', color=colors[i],
                 label='_nolegend_')
    for shape in list(bb.iterShapes()):
        plot(shape)
    plot(bb.shape(0), 'MN')
    plot(cd.shape(35), 'JFK')
    plt.title('\nPickup and Drop-off Locations, grouped by PRCP level\n', fontsize=20)
    plt.legend(fontsize=15)
    plt.show()