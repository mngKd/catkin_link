#!/usr/bin/env python

from __future__ import print_function
import os
import argparse

def is_catkin_ws(ws_root):
    abs_ws_root = os.path.abspath(ws_root)
    catkin_tools_folder = os.path.join(abs_ws_root, '.catkin_tools')
    devel_space = os.path.join(abs_ws_root, 'devel')
    
    return os.path.exists(catkin_tools_folder) and os.path.exists(devel_space)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("ws_root", help="the workspace root")
    
    args = vars(ap.parse_args())
    is_ws = is_catkin_ws(args["ws_root"])
    print("Is '{0}' a catkin workspace: {1}".format(args["ws_root"], is_ws))
