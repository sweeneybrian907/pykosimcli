#!usr/bin/env python
# -*- coding: utf-8 -*-

import os
import io
import shutil
import tempfile
import pandas as pd

"""context wrapper class for Kosim .klzc files
"""

class klzc(object):
    """
    klzc file class
    """
    def __init__(self, filePath):
        self.filePath = os.path.abspath(filePath)

    def __enter__(self):
        """context manager method for returning parsed file
        """
        self.conn = open(self.filePath, "r")

        # parse file
        with self.conn as f:
            for group in self.get_blocks(f):
                yield pd.read_csv(io.StringIO("".join(group)), sep=",")

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """context manager teardown
        """
        # close connection
        self.conn.close()

    def get_blocks(self, seq):
        """get blocks of data that start with HEADER*
        """
        data = []
        for line in seq:
            # Here the `startswith()` logic can be replaced with other
            # condition(s) depending on the requirement.
            if "HEADER" in line:
                if data:
                    yield data
                    data = []
            data.append(line)

        if data:
            yield data


if __name__ == '__main__':
    import sys
    import pandas as pd

    fIn = klzc(sys.argv[1])

    with fIn as f:
        for i, group in enumerate(f, start=1):
            print ("Group #{}".format(i))
            print(group)

