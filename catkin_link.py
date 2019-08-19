#!/usr/bin/env python3

from __future__ import print_function
import os
import argparse
import sys
import subprocess

def is_catkin_ws(ws_root):
    catkin_tools_folder = os.path.join(abs_ws_root, ".catkin_tools")
    build_space = os.path.join(abs_ws_root, "build")
    src_space = os.path.join(abs_ws_root, "src")
    return os.path.exists(catkin_tools_folder) and os.path.exists(build_space) and os.path.exists(src_space)

def symlink_compile_commands_for_pkg(build_space, src_space, pkg_name):
    compile_commands_name = "compile_commands.json"
    compile_commands_file = os.path.join(build_space, pkg_name, compile_commands_name)
    
    if not os.path.exists(compile_commands_file):
        return
    
    pkg_in_src_space = os.path.join(src_space, pkg_name)
    if not os.path.exists(pkg_in_src_space):
        return

    target = os.path.join(pkg_in_src_space, compile_commands_name)
    p = subprocess.run(["ln", "-sf", compile_commands_file, target])
    if p.returncode != 0:
        print("Could not symlink '{0}' to '{1}' - returncode '{2}'".format(compile_commands_file, target, p.returncode),
              file=sys.stderr)
        
def symlink_compile_commands_for_all_pkgs(ws_root):
    build_space = os.path.join(ws_root, "build")
    src_space = os.path.join(ws_root, "src")
    dirs = os.listdir(build_space)
    
    # ignore hidden files
    dirs = filter(lambda d: d[0] != ".", dirs)
    # skip catkin folders
    folders_to_ignore = ["catkin_tools_prebuild"]
    dirs_to_symlink = filter(lambda d: d not in folders_to_ignore, dirs)

    for d in dirs_to_symlink:
        symlink_compile_commands_for_pkg(build_space, src_space, d)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("ws_root", help="the workspace root")
    
    args = vars(ap.parse_args())
    abs_ws_root = os.path.abspath(args["ws_root"])
    
    if not is_catkin_ws(abs_ws_root):
        print("Given argument '{0}' is not a catkin workspace - aborting".format(abs_ws_root))
        
    symlink_compile_commands_for_all_pkgs(abs_ws_root)
