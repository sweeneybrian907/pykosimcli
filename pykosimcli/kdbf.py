#!usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
import tempfile
import platform
import fdb

"""Kosim 7 Database class: firebird / Interbase
"""


class kdbf(object):
    """
    db engine class - wrapper for opening and closing kdbf-databases
    """
    def __init__(self, filePath):
        self.filePath = os.path.abspath(filePath)

    def __enter__(self):
        """context manager method for easier handling using with statements
        """
        # load embedded api
        # fbdir = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                             # "firebird"))
        # fbdir = fbdir.replace(":", "")
        # fbdir = fbdir.replace("\\", "/")
        # fbdir = "/" + fbdir
        # print("adding fblib directory {} to path".format(fbdir))
        # os.environ["PATH"] = "{}
        # TODO: loading of firebird client in windows using above code not
        # possible. At present client libraries need to be added to the 
        # system path or a firebird server needs to be installed on the machine
        # to add the client to the path:
        # export PATH=<path to firebird dir in pykosim>:$PATH

        if platform.system() == "Windows":
            fdb.load_api("fbembed.dll")
        else:
            pass

        # path to kdbf
        pth = os.path.abspath(self.filePath)

        if pth.endswith('.kdbf'):
            if platform.system() == "Windows":
                self.tempdir = tempfile.mkdtemp()
                print("creating tempdir at {}".format(self.tempdir))
                shutil.copy(pth, self.tempdir)
                tempPth = os.path.join(self.tempdir, os.path.basename(pth))
                self.conn = fdb.connect(tempPth, user='sysdba',
                                        password='masterkey')
            else:
                self.tempdir = False
                tempPth = pth
                self.conn = fdb.connect(tempPth, user='sysdba',
                                        password='masterkey',
                                        charset="latin1")
        else:
            print('Unknown file type')
            raise AttributeError

        return self.conn

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """context manager teardown
        """
        # close connection
        self.conn.commit()
        self.conn.close()
        # TODO erase temp file and directory
        if self.tempdir:
            shutil.rmtree(self.tempdir)


def check_and_create_dir(root, dirName):
    """check if a directory exists and create if it doesn't

    Args:
        root (str): parent directory of dirName
        dirName (str): path to directory

    Returns:
        dir (str): returns path to directory as os.path.abspath
    """
    if os.path.exists(os.path.abspath(os.path.join(root, dirName))):
        return os.path.abspath(os.path.join(root, dirName))
    else:
        path = os.path.abspath(os.path.join(root, dirName))
        os.mkdir(path)
        return path


# --- sql queries to databases ---
MWB = """SELECT *
FROM MISCHWASSERBAUWERKBESTAND AS bes
INNER JOIN MISCHWASSERBAUWERKPROZESSMJW AS MJW
ON bes.ID = MJW.ID
INNER JOIN MISCHWASSERBAUWERKPROZESSSGMJW AS gmjw
ON bes.ID = gmjw.ID"""


RWB = """SELECT *
FROM REGENWASSERBEHANDLUNGBESTAND AS bes
JOIN REGENWASSERBEHANDLUNGPROZESSMJW AS MJW
ON bes.ID = MJW.ID
FULL OUTER JOIN REGENWASSERBEHANDLUNGBILANZSG AS zsg
ON BES.ID = zsg.ID"""


ZB = """SELECT *
FROM SRC_A128
WHERE SRC_A128.BEZEICHNUNG = 'A128_Fiktives Zentralbecken'"""


GEB = """SELECT * FROM GEBIETBESTAND"""
TRANS = """SELECT * FROM TRANSPORTBESTAND"""
GROSSEL = """SELECT * FROM EINZELEINLEITERBESTAND"""


KDBFselect = {"mischwasserbauwerke": MWB,
              "regenwasserbauwerke": RWB,
              "zentralbecken": ZB,
              "gebiete": GEB,
              "transport": TRANS,
              "grosseinleiter": GROSSEL
             }


if __name__ == '__main__':
    # TODO reduced testing set, still need to write unit tests. 
    # This is only for fast prototyping !!!!!!!

    import sys
    import pandas as pd

    kdbf = kdbf(sys.argv[1])

    with kdbf as db:
        print(pd.read_sql_query(GEB, db))
        print(db.database_name)
