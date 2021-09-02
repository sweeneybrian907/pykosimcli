#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import os
import argparse
import argcomplete


def parse_cli(*args):
    """command line parser function
    """
    # create cli parser app
    parser = argparse.ArgumentParser(description="CL-Utility for Kosim model plausibility tests")

    # kosim = parser.add_parser(dest="pykosim", help='run plaus tests on Kosim models')

    parser.add_argument('fileIn', type=str, help='kdbf file path')
    parser.add_argument('--plot', action='store_true', default=False)
    parser.add_argument('--xcel', type=str, nargs='?', default=None,
                            help='opt:excel file path for plaus output')

    # add autocompletion
    argcomplete.autocomplete(parser)
    return parser.parse_args(*args)


def main(*args):
    """utility for creating plausibiltty plots of qstrg, pegel, and bauwerk
    datasets from hydro_as-2d output
    """
    import pykosimcli.parsedb as pk

    args = parse_cli(*args)
    print(args)

    res = pk.parse(os.path.abspath(args.fileIn))

    # generate graphs
    if args.plot:
        try:
            pk.plot_zb(res)
        except ValueError:
            print('Daten zum Zentralbecken fehlen, ZB Grafik nicht darstellbar')
        pk.plot_mbw_fracht(res)
        pk.plot_mbw_spez_fracht_and_vol(res)
        pk.plot_entlastungswerte(res)

    if args.xcel is not None:
        pk.plaus_excel(res, os.path.abspath(args.xcel))


if __name__ == "__main__":
    import sys

    main(sys.argv[1:])
