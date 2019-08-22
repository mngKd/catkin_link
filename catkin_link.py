#!/usr/bin/env python3
from __future__ import print_function
import os
import argparse
import sys
import subprocess
# import yaml
import re


def get_active_profile(profile_file):
    if not os.path.exists(profile_file):
        # is this a default workspace?
        default_profile = os.path.join(os.path.dirname(profile_file),
                                       "default")
        if os.path.exists(default_profile):
            return "default"

        # sth. is wrong with the workspace
        print(("Profile file '{0}' does not exist and neither the default "
               "profile folder '{1}' - sth. is wrong").format(profile_file,
                                                              default_profile),
              file=sys.stderr)
        sys.exit(1)

    # read profile.yaml file
    content = []
    with open(profile_file, 'r') as file_obj:
        content = file_obj.read().replace('\n', '')

    re_str = re.compile(r"^active:\s*?([\w_-]+)")
    match = re.search(re_str, content)

    if not match:
        print("Can not retrieve profile from '{0}'".format(profile_file),
              file=sys.stderr)
        sys.exit(1)

    active_profile = match.group(1)
    return active_profile


def is_catkin_ws(ws_root):
    catkin_tools_folder = os.path.join(ws_root, ".catkin_tools")
    build_space = os.path.join(ws_root, "build")
    src_space = os.path.join(ws_root, "src")
    return (os.path.exists(catkin_tools_folder) and
            os.path.exists(build_space) and
            os.path.exists(src_space))


def symlink_compile_commands_for_pkg(build_space, src_space, pkg_name):
    compile_commands_name = "compile_commands.json"
    compile_commands_file = os.path.join(build_space, pkg_name,
                                         compile_commands_name)

    if not os.path.exists(compile_commands_file):
        print(("Compile commands file '{0}' for pkg '{1}' does not "
               "exist - skipping".format(compile_commands_file, pkg_name)))
        return

    pkg_in_src_space = os.path.join(src_space, pkg_name)
    if not os.path.exists(pkg_in_src_space):
        return

    target = os.path.join(pkg_in_src_space, compile_commands_name)
    proc = subprocess.run(["ln", "-sf", compile_commands_file, target])
    if proc.returncode != 0:
        print("Could not symlink '{0}' to '{1}' - returncode '{2}'".format(
            compile_commands_file, target, proc.returncode), file=sys.stderr)


def symlink_compile_commands_for_all_pkgs(build_space, src_space):
    dirs = os.listdir(build_space)

    # ignore hidden files
    dirs = filter(lambda d: d[0] != ".", dirs)
    # skip catkin folders
    folders_to_ignore = ["catkin_tools_prebuild"]
    dirs_to_symlink = filter(lambda d: d not in folders_to_ignore, dirs)

    for pkg in dirs_to_symlink:
        symlink_compile_commands_for_pkg(build_space, src_space, pkg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ws_root", help="the workspace root")

    args = vars(ap.parse_args())
    abs_ws_root = os.path.abspath(args["ws_root"])

    if not is_catkin_ws(abs_ws_root):
        print(("Given argument '{0}' is not a catkin workspace -"
               " aborting".format(abs_ws_root)))

    profile_folder = os.path.join(abs_ws_root, ".catkin_tools", "profiles")
    if not os.path.exists(profile_folder):
        print("Can not find profile folder '{0}' - aborting".format(
            profile_folder))

    profile_file = os.path.join(profile_folder, "profiles.yaml")
    active_profile = get_active_profile(profile_file)
    print("Active profile:", active_profile)

    build_space = os.path.join(abs_ws_root, "build")
    if active_profile != "default":
        build_space = os.path.join(build_space, active_profile)
    src_space = os.path.join(abs_ws_root, "src")

    symlink_compile_commands_for_all_pkgs(build_space, src_space)


if __name__ == "__main__":
    main()
