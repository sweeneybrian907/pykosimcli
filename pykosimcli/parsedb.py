#!/usr/bin/python
# -*- coding: utf8 -*-

# TODO write documentation
'''
Documentation goes here
'''

import os
import io
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from collections import OrderedDict
from pykosimcli.kdbf import kdbf
from pykosimcli.kdbf import KDBFselect


def get_filetype_in_dir(dirIn, fileEnd=".kdbf"):
    """search recursively from a given root for a given file ending
    """
    dbs = []
    for root, dirs, files in os.walk(dirIn):
        for f in files:
            if f.endswith(fileEnd.lower()) or f.endswith(fileEnd.upper()):
                resDB = os.path.join(root, f)
                dbs.append(resDB)
    print(('{} Kosim-7 databases found'.format(len(dbs))))
    return dbs


def get_filename(filePath):
    """get filename without file extension from file path
    """
    absFilePath = os.path.abspath(filePath)
    return os.path.basename(os.path.splitext(absFilePath)[0])


def add_sim_col_to_query(query, conn, simName):
    df = pd.read_sql_query(query, conn)
    df["sim"] = simName
    return df


def concat_dfs_by_index(dictIn, idxVal, dfAdd):
    try:
        dictIn[idxVal] = dictIn[idxVal].append(dfAdd)
    except KeyError:
        dictIn[idxVal] = dfAdd


def clean_col_names(df):
    """ clean up duplicate names in columns
    """
    cols = pd.Series(df.columns)

    for dup in cols[cols.duplicated()].unique():
        cols[cols[cols == dup].index.values.tolist()] = [dup + '_' + str(i) if i != 0 else dup for i in range(sum(cols == dup))]

    df.columns = cols
    return df


def parse(fIn):
    """open connection to db and parse information

    Params
    ------
    fIn (str): input directory path as string

    Returns
    -------
    res (dict): dictionary of results in pandas.dataframes format
    """
    res = {}

    with kdbf(fIn) as conn:
        # queries to database
        for query in KDBFselect:
            #TODO add step to clean up column names?
            df = pd.read_sql_query(KDBFselect[query], conn)
            df = clean_col_names(df)
            res[query] = df.set_index('BEZEICHNUNG')
    return res


def create_zb_df(res):
    """create zentral becken dataframe

    Params
    ------
    res (dict): results dictionary from parsing function
    """
    fzbcols = ["GESAMTVOLUMENERFORDERLICH", "VOLUMENANRECHENBAR",
               "VOLUMENERFORDERLICH", "ENTLASTUNGSFRACHT"]
    fzb = res["zentralbecken"][fzbcols]
    # remove index
    fzb.reset_index(drop=True, inplace=True)
    bwvals = res["mischwasserbauwerke"][["VVORH", "SFUE", "SFUEIN128"]].sum()

    #change to df
    bwvals = pd.DataFrame(bwvals).transpose()
    return pd.concat([fzb, bwvals], axis=1)


def get_fracht_color(entFr, entFr85, compVal):
    if compVal >= entFr:
        return "tab:red"
    elif compVal >= entFr85:
        return "tab:orange"
    else:
        return "tab:green"


def get_color_by_thresholds(valSeries, minVal, maxVal):
    colors = []
    for i in list(valSeries):
        if i < minVal or i > maxVal:
            colors.append('tab:red')
        else:
            colors.append('tab:blue')
    return colors


def plot_zb(res):
    """plot information about fiktiv zentral becken and Entlastungsfracht
    """
    df = create_zb_df(res)
    N = 4
    vals = tuple(list(df["ENTLASTUNGSFRACHT"]) +
                 list(df["ENTLASTUNGSFRACHT"]*0.85) + list(df["SFUE"]) +
                 list(df["SFUEIN128"]))
    ind = np.arange(N)    # the x locations for the groups
    width = 0.5       # the width of the bars: can also be len(x) sequence
    # add colors dependent on the Schmutzfracht amount
    colors = ["tab:blue", "tab:blue",
              get_fracht_color(vals[0], vals[1], vals[2]),
              get_fracht_color(vals[0], vals[1], vals[3])]

    p1 = plt.bar(ind, vals, width, color=colors)

    plt.ylabel('Fracht [kg/a]')
    plt.title('Fiktiv Zentralbecken Fracht / Modellfracht')
    plt.xticks(ind, ('FZB', 'FZB 85%', 'Fracht', 'Fracht DWA-A 128'))

    plt.show()


def plot_mbw_fracht(res):
    """plot mischwasserbauwerke, total loads
    """
    mwb = res['mischwasserbauwerke']
    # mwb = mwb.set_index('BEZEICHNUNG')

    mwb = mwb.sort_values(by='SFUEIN128', ascending=True)
    ax = mwb.plot.barh(y='SFUEIN128', legend=None)
    ax.set(xlabel='Fracht [kg/a]', ylabel='Bauwerk')

    # move legende to bottom righthand corner
    plt.show()


def plot_mbw_spez_fracht_and_vol(res):
    """plot mischwasserbauwerke, total and specific loads
    """
    mwb = res['mischwasserbauwerke']
    # mwb = mwb.set_index('BEZEICHNUNG')

    # generate specific fracht and volumen columns
    mwb['SPEZFRACHT'] = mwb['SFUEIN128'] / mwb['AUA128']
    mwb['SPEZVOL'] = mwb['VOLUMEN'] / mwb['AUA128']

    mwb = mwb.sort_values(by='SPEZFRACHT', ascending=True)

    # make 2 subplots with horizontal alignment
    fig, axes = plt.subplots(nrows=1, ncols=2, sharey="all")
    fig.suptitle('Spezifische Fracht und Volumen')

    # plot specific loads
    mwb.plot.barh(ax=axes[0], y='SPEZFRACHT', legend=None)
    axes[0].set(ylabel="Bauwerk",
                xlabel='Spezifische Fracht [kg/a*ha]')

    # plot specific volumes
    # get colors for bw out of the range
    colors = get_color_by_thresholds(mwb["SPEZVOL"], 10, 30)
    mwb.plot.barh(ax=axes[1], y='SPEZVOL', color=colors, legend=None)
    axes[1].set(xlabel='Spezifisches Volumen [m^3/ha]')
    axes[1].axvline(x=10, linestyle='--', linewidth=0.5)
    axes[1].axvline(x=30, linestyle='--', linewidth=0.5)

    # move legende to bottom righthand corner
    plt.show()


def plot_ka_last(res):
    """plot of the austlastung an der Kläranlage according to a198
    """
    mwb = res['mischwasserbauwerke']
    # mwb = mwb.set_index('BEZEICHNUNG')

    #
    colors = get_color_by_thresholds(mwb["NA198"], 3, 9)
    ax = mwb.plot.barh(y='NA198', legend=None, color=colors)
    ax.axvline(x=3, linestyle='--', linewidth=0.5)
    ax.axvline(x=9, linestyle='--', linewidth=0.5)
    ax.set(xlabel='Auslastungswert Kläranlage (A198)', ylabel='Bauwerk')

    # move legende to bottom righthand corner
    plt.show()


def plot_entlastungswerte(res):
    """plot entlastunggsrate und -häufigkeit
    entlastungsrate between 10-40
    entlastungshäufigkeit between 20-50
    """
    mwb = res['mischwasserbauwerke']
    # mwb = mwb.set_index('BEZEICHNUNG')

    # make 2 subplots with horizontal alignment
    fig, axes = plt.subplots(nrows=1, ncols=2, sharey="all")
    fig.suptitle('Entlastungsrate und -häufigkeit')

    # plot entlastungsrate
    colors1 = get_color_by_thresholds(mwb["E0"], 10, 40)
    mwb.plot.barh(ax=axes[0], y='E0', color=colors1, legend=None)
    axes[0].set(ylabel="Bauwerk",
                xlabel='Entlastungsrate [%]')
    axes[0].axvline(x=10, linestyle='--', linewidth=0.5)
    axes[0].axvline(x=40, linestyle='--', linewidth=0.5)

    # plot enlastunghäufigkeit
    colors2 = get_color_by_thresholds(mwb["NUED"], 20, 50)
    mwb.plot.barh(ax=axes[1], y='NUED', color=colors2, legend=None)
    axes[1].set(xlabel='Entlastungshäufigkeit [d/a]')
    axes[1].axvline(x=20, linestyle='--', linewidth=0.5)
    axes[1].axvline(x=50, linestyle='--', linewidth=0.5)

    # move legende to bottom righthand corner
    plt.show()


def export_all_to_excel(res, excel="kosim_tabellen.xlsx"):
    with pd.ExcelWriter(xcelPath, engine="xlsxwriter") as writer:
        for key in res:
            try:
                res[key].to_excel(writer, key)
            except ValueError:
                pass


def cond_between(minVal, maxVal, colorformat):
    """helper function for returning xlsxwriter conditional formating dicts
    """
    formDict =  {'type': 'cell',
                 'criteria': 'between',
                 'minimum': minVal,
                'maximum': maxVal,
                'format': colorformat}
    return formDict


def cond_not_between(minVal, maxVal, colorformat):
    """helper function for returning xlsxwriter conditional formating dicts
    """
    formDict =  {'type': 'cell',
                 'criteria': 'not between',
                 'minimum': minVal,
                'maximum': maxVal,
                'format': colorformat}
    return formDict


def cond_mt(val, colorformat):
    """helper function for returning xlsxwriter conditional formatting dicts
    for max conditions
    """
    formDict =  {'type': 'cell',
                 'criteria': 'greater than',
                 'value': val,
                 'format': colorformat}
    return formDict


def cond_lt(val, colorformat):
    """helper function for returning xlsxwriter conditional formatting dicts
    for less than conditions
    """
    formDict =  {'type': 'cell',
                 'criteria': 'less than',
                 'value': val,
                 'format': colorformat}
    return formDict


def cond_formula(criteria, colorformat):
    """helper function for returning xlsxwriter cond. formatting dicts
    for formula conditions i.e. cond. format dependet on another cell
    """
    formDict =  {'type': 'formula',
                 'criteria': criteria,
                 'format': colorformat}
    return formDict


def get_col_widths(dataframe):
    """ helper function to auto set col widths
    """
    # First we find the maximum length of the index column   
    idx_max = max([len(str(s)) for s in dataframe.index.values] + [len(str(dataframe.index.name))])
    # Then, we concatenate this to the max of the lengths of column name and its values for each column, left to right
    return [idx_max] + [max([len(str(s)) for s in dataframe[col].values] + [len(col)]) for col in dataframe.columns]


# TODO move this to the top of the file ?
mwbwShort = OrderedDict(
    [("BEZEICHNUNG_1", "BW-Name"), ("AUA128", "Au-A128"), ("QF24", "Qf24"),
     ("QR", "qr"), ("NA198", "Auslastung-KA"), ("VOLUMEN", "Volumen"),
     ("VBECKENPROHEKTAR", "Volumen pro Hektar"), ("E0", "e0"),
     ("NUED", "Überlauftage"), ("TUE", "Überlaufdauer"), ("MMIN", "m,min"),
     ("MVORH", "m,vorh"), ("X", "X"), ("QF", "Qf"),
     ("TYPMISCHWASSERBAUWERKASSTRING", "Bauwerkstyp"), ("SFUEIN128", "SFue128"),
     ("SPEZFRACHT", "spez SFue"), ("SPEZVOL", "spez Volumen")]
)


thresholds = {"QF": [0.03, 0.3], "QR": [0.2, 2.0], "NA198": [3.0, 9.0],
              "SPEZVOL": [10, 30], "E0": [10, 40], "NUED": [20, 50],
              "TUE": [20, 500]
             }

thresholds_rue = { "E0": [10, 40], "NUED": [20, 50], "TUE": [20, 500]
                 }


def create_mw_bw_short_tab(res):
    """create the short table for mw-bauwerk data
    """
    df = res["mischwasserbauwerke"]
    # print(list(df.columns))
    df["QF"] = df["QF24"] / df["AUA128"]
    # calculate spezific volume
    df["SPEZFRACHT"] = df["SFUEIN128"] / df["AUA128"]
    df["SPEZVOL"] = df["VOLUMEN"] / df["AUA128"]
    df = df[["BEZEICHNUNG_1", "AUA128", "QF24", "QR", "NA198", "VOLUMEN",
             "VBECKENPROHEKTAR", "E0", "NUED", "TUE", "MMIN", "MVORH",
             "X", "QF", "TYPMISCHWASSERBAUWERKASSTRING", "SFUEIN128",
             "SPEZFRACHT", "SPEZVOL"]]
    df = df.round(decimals=3)
    # change column names

    return df


def create_mw_einzelpruef_tab(res):
    """create short table for a Einzelnachweis of different MW-Bauwerke
    """
    df = res["mischwasserbauwerke"]

    # geschwindigkeit für Stauraumkanal
    df["GESCHW"] = df["QKRIT"] / (df["VVORH"] / df["STAURAUMLAENGE"])
    # geschwindigkeit für durchlaufbecken
    # calculate area
    df["A_beck"] = df["BREITE"] * df["TIEFE"]
    bw = "TYPMISCHWASSERBAUWERKASSTRING"
    DBs = (df[bw] == 'DBH') | (df[bw] == 'DBN')
    df.loc[DBs, "GESCHW"] = (df.loc[DBs, "QKRIT"] / 1000) / df.loc[DBs, "A_beck"]

    df = df[["TYPMISCHWASSERBAUWERKASSTRING",
             "VMIN", "VMINA102", "VVORH", "MMIN", "MVORH", "QA",
             "QKRIT", "QDRMAX", "TE", "E0", "NUED", "CUE", "CKUE",
             "CBUE", "SFUE", "SFUEIN128", "GESCHW", "LAENGE", "BREITE",
             "TIEFE", "STAURAUMLAENGE"]]
    df = df.round(decimals=3)

    return df


def plaus_excel(res, excelPath="kosim_plaus.xlsx"):
    """create excel table of einzelnachweise and plausibility

    Values taken from RP Merkblatt:

    Versieglungsgrad [-]                   0,28-0,5
    Einwohnerdichte [E/ha]                 35-110
    Wasserverbrauch [l/E*d]                85-150
    Fremdwasserspende [l/s*ha]             0,03-0,3
    Regenwasser an RÜB-Drosseln [l/s*ha]   0,2-2,0
    Auslastungswert Kläranlage [-]         3,0-9,0
    Spezifisiches Speichervolumen [l/s*ha] 10-30
    Entlastungsrate [%]                    10-40
    Entlastungshäufigkeit [d/a]            20-50
    Entlastungsdauer [h/a]                 20-500
    Mischverhältnis [-]                    > m min
    """
    with pd.ExcelWriter(excelPath, engine="xlsxwriter") as writer:
        workbook = writer.book
        # Add a format. Light red fill with dark red text.
        red = workbook.add_format({'bg_color': '#FFC7CE',
                                   'font_color': '#9C0006'})

        # Add a format. Orange fill with dark orange text.
        orange = workbook.add_format({'bg_color': '#FFE5B4',
                                     'font_color': '#B37400'})

        # Add bold underline format
        bold = workbook.add_format({'bold': True, 'underline': True})

        # slice gebiets data
        geb = res["gebiete"]
        numVals = len(geb) + 1  # add 1 to account for header
        geb.to_excel(writer, sheet_name="Gebiete")
        worksheet = writer.sheets["Gebiete"]
        worksheet.conditional_format("L2:L{}".format(numVals),
                                     cond_not_between(35, 110, red))

        # slice mw-Bauwerk data
        df = create_mw_bw_short_tab(res)
        df = df.rename(columns=mwbwShort)

        # calculate number of rows
        numVals = len(df) + 1  # add 1 to account for header

        # write to excel
        df.to_excel(writer, sheet_name="MW-Bauwerke")
        worksheet = writer.sheets["MW-Bauwerke"]
        # set col widths
        # TODO run through values in dictionary
        # TODO create dictionary of parameters, thresholds, etc.
        # TODO use bawerktype to determine if conditional formatting should be
        # applied 
        for i, width in enumerate(get_col_widths(df)):
            worksheet.set_column(i, i, width)

        worksheet.conditional_format("O2:O{}".format(numVals),
                                     cond_lt(0.03, orange))
        worksheet.conditional_format("O2:O{}".format(numVals),
                                     cond_mt(0.30, red))
        worksheet.conditional_format("E2:E{}".format(numVals),
                                     cond_lt(0.2, orange))
        worksheet.conditional_format("E2:E{}".format(numVals),
                                     cond_mt(2.0, red))
        worksheet.conditional_format("F2:F{}".format(numVals),
                                     cond_lt(3.0, orange))
        worksheet.conditional_format("F2:F{}".format(numVals),
                                     cond_mt(9.0, red))
        worksheet.conditional_format("H2:H{}".format(numVals),
                                     cond_lt(10.0, orange))
        worksheet.conditional_format("H2:H{}".format(numVals),
                                     cond_mt(30.0, red))
        worksheet.conditional_format("I2:I{}".format(numVals),
                                     cond_lt(10.0, orange))
        worksheet.conditional_format("I2:I{}".format(numVals),
                                     cond_mt(40.0, red))
        worksheet.conditional_format("J2:J{}".format(numVals),
                                     cond_lt(20.0, orange))
        worksheet.conditional_format("J2:J{}".format(numVals),
                                     cond_mt(50.0, red))
        worksheet.conditional_format("K2:K{}".format(numVals),
                                     cond_lt(20.0, orange))
        worksheet.conditional_format("K2:K{}".format(numVals),
                                     cond_mt(500.0, red))
        worksheet.conditional_format("M2:M{}".format(numVals),
                                     {'type':'formula',
                                      'criteria': '=$M2<$L2',
                                      'format': red})
        # write threshold values
        worksheet.write_string(numVals + 1, 0, 'Untergrenze')
        worksheet.write_string(numVals + 2, 0, 'Obergrenze')
        worksheet.write_string(numVals + 3, 0, 'Parameter Beschreibung')

        worksheet.write("O{}".format(numVals + 2), 0.03)
        worksheet.write("O{}".format(numVals + 3), 0.30)
        worksheet.write("O{}".format(numVals + 4), 'Fremdwasserspende [l/s*ha]')

        worksheet.write("E{}".format(numVals + 2), 0.2)
        worksheet.write("E{}".format(numVals + 3), 2.0)
        worksheet.write("E{}".format(numVals + 4), 'Regenwasserspende an RUEB-Drosseln [l/s*ha]')

        worksheet.write("F{}".format(numVals + 2), 3.0)
        worksheet.write("F{}".format(numVals + 3), 9.0)
        worksheet.write("F{}".format(numVals + 4), 'Auslastungswert KA [-]')

        worksheet.write("H{}".format(numVals + 2), 10.0)
        worksheet.write("H{}".format(numVals + 3), 30.0)
        worksheet.write("H{}".format(numVals + 4), 'Spezifisches Speichervolumen [m^3/ha]')

        worksheet.write("I{}".format(numVals + 2), 10.0)
        worksheet.write("I{}".format(numVals + 3), 40.0)
        worksheet.write("I{}".format(numVals + 4), 'Entlastungsrate [%]')

        worksheet.write("J{}".format(numVals + 2), 20.0)
        worksheet.write("J{}".format(numVals + 3), 50.0)
        worksheet.write("J{}".format(numVals + 4), 'Entlastungshaeufigkeit [d/a]')

        worksheet.write("K{}".format(numVals + 2), 20.0)
        worksheet.write("K{}".format(numVals + 3), 500.0)
        worksheet.write("K{}".format(numVals + 4), 'Entlastungsdauer [h/a]')

        worksheet.write("M{}".format(numVals + 4), 'Mischverhaeltnis [-]')

        # insert legend
        worksheet.write_string((numVals + 4), 0, 'Legende', bold)
        worksheet.write_string((numVals + 5), 0, 'Größer als Grenzwert', red)
        worksheet.write_string((numVals + 6), 0, 'Niedriger als Grenzwert',
                               orange)

        # slice mw-Bauwerk data
        einzel = create_mw_einzelpruef_tab(res)

        # calculate number of rows
        numVals = len(einzel) + 1  # add 1 to account for header

        # write to excel
        einzel.to_excel(writer, sheet_name="Einzelnachweis")
        worksheet = writer.sheets["Einzelnachweis"]

        # set column widths automagically
        for i, width in enumerate(get_col_widths(df)):
            worksheet.set_column(i, i, width)

        # mischverhältnis cond
        worksheet.conditional_format("G2:G{}".format(numVals),
                                     cond_formula('=$G2<$F2', red))
        # min volume cond
        worksheet.conditional_format("E2:E{}".format(numVals),
                                     cond_formula('=$E2<$C2', red))
        # entleerungszeit Te condition
        frml = 'AND($K2>10, $K2<=15)'
        worksheet.conditional_format("K2:K{}".format(numVals),
                                     cond_formula(frml, orange))
        worksheet.conditional_format("K2:K{}".format(numVals),
                                     cond_formula('=$K2>15', red))
        # Klärbedingung cond. Duchlaufbecken qa < 10 m/h
        frml = 'AND(OR($B2="DBN", $B2="DBH"), $H2>10)'
        worksheet.conditional_format("H2:H{}".format(numVals),
                                     cond_formula(frml, red))
        # Geschwindigkeit im Durchlaufbecken
        frml = 'AND(OR($B2="DBN", $B2="DBH"), $S2>0.05)'
        worksheet.conditional_format("S2:S{}".format(numVals),
                                     cond_formula(frml, red))
        # Klärbedingung cond. SKUE
        frml = 'AND($B2="SKUE", $S2>0.3)'
        worksheet.conditional_format("S2:S{}".format(numVals),
                                     cond_formula(frml, red))


        # writer.save()


def parse_kdbf_dir(dirIn):
    """parse all kdbfs in a directory and aggregate the results

    Params
    ------
    dirIn (str): input directory path as string

    Returns
    -------
    res (dict): dictionary of results in pandas.dataframes format
    """
    res = {}
    for db in get_filetype_in_dir(dirIn):
        simName = get_filename(db)
        # TODO: aggregate vals
        concat_dfs_by_index(res, "schacht", scht)


def read_im_input_file(fIn):
    """read input file and convert to unicode if needed
    """
    encIn = ['utf8', 'ascii', 'latin1']

    for enc in encIn:
        try:
            with io.open(fIn, 'r', encoding=enc) as src:
                outlets = [str("{}".format(i.strip())) for i in src.readlines()]
        except UnicodeDecodeError:
            print(("Opening file with {} codec failed, trying another".format(enc)))
            pass

    return outlets


def aggregate_results(resDF):
    """ aggregate results from parsed values

    Params
    ------
    resDF (dict): results dictionary from parse_results function

    Returns
    -------
    aggRes (dict): dictionary of results in pandas.dataframes format
    """
    aggRes = {}
    # aggregate shacht results
    sVals = ["Ueberstauvolumen", "Durchfluss", "Einstaudauer", "Wasserstand"]
    aggRes["schacht"] = resDF["schacht"].pivot(index="Knoten", columns="sim",
                                               values=sVals)

    # aggregate haltung results
    hVals = ["Durchfluss", "Geschwindigkeit", "WasserstandOben",
             "WasserstandUnten"]
    aggRes["haltung"] = resDF["haltung"].pivot(index="Kante", columns="sim",
                                               values=hVals)

    # aggreate outlet results
    oVals = ["Durchfluss", "Wasserstand"]
    aggRes["outlet"] = resDF["outlet"].pivot(index="Name", columns="sim",
                                             values=oVals)

    return aggRes


def res_dict_to_excel(resDict, xcelPath):
    """export result dictionary of panda dfs to excel
    """
    with pd.ExcelWriter(xcelPath, engine="xlsxwriter") as writer:
        for key in resDict:
            try:
                resDict[key].to_excel(writer, key)
            except ValueError:
                pass


if __name__ == "__main__":
    res = parse("../test/data/muster-mw.kdbf")
    # plot_zb(res)
    # plot_mbw_fracht(res)
    # plot_mbw_spez_fracht_and_vol(res)
    # plot_entlastungswerte(res)
    plaus_excel(res)
