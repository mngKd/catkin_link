#!/usr/bin/env python3
from __future__ import print_function
import os
import argparse
import sys
import subprocess
import re
from collections import defaultdict


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


def symlink_compile_commands_for_pkg(pkg_build_space, pkg_src_space):
    compile_commands_name = "compile_commands.json"
    compile_commands_file = os.path.join(pkg_build_space,
                                         compile_commands_name)

    if not os.path.exists(compile_commands_file):
        print(("Compile commands file '{0}' for pkg '{1}' does not "
               "exist - skipping".format(compile_commands_file,
                                         os.path.basename(pkg_build_space))))
        return

    target = os.path.join(pkg_src_space, compile_commands_name)
    proc = subprocess.run(["ln", "-sf", compile_commands_file, target])
    if proc.returncode != 0:
        print("Could not symlink '{0}' to '{1}' - returncode '{2}'".format(
            compile_commands_file, target, proc.returncode), file=sys.stderr)


def symlink_compile_commands_for_all_pkgs(build_space, pkgs_with_path):
    for pkg_name, pkg_src_space in pkgs_with_path.items():
        pkg_build_space = os.path.join(build_space, pkg_name)
        symlink_compile_commands_for_pkg(pkg_build_space, pkg_src_space)


def get_build_space(ws_root):
    cur_dir = os.getcwd()

    build_space = None

    try:
        os.chdir(ws_root)
        ret = subprocess.run(["/usr/bin/catkin", "locate", "-b"],
                             stdout=subprocess.PIPE,
                             universal_newlines=True)
        build_space = ret.stdout.strip()
    finally:
        os.chdir(cur_dir)

    return build_space


def get_content_of_file(file_path):
    if not os.path.exists(file_path):
        return None

    content = None
    with open(file_path, 'r') as file_obj:
        content = file_obj.read()
    return content


def is_catkin_pkg(cmake_lists_file):
    content = get_content_of_file(cmake_lists_file)
    if not content:
        return False

    catkin_pkg_re = re.compile(r"^\s*?find_package\s*?\(\s*?catkin\s+",
                               re.MULTILINE)

    return re.search(catkin_pkg_re, content)


def get_pkg_name(cmake_lists_file):
    content = get_content_of_file(cmake_lists_file)
    if not content:
        return None

    project_re = re.compile(r"^\s*?project\s*?\(\s*?([\w_-]+)\s*?\)",
                            re.MULTILINE)
    match = re.search(project_re, content)

    if not match:
        return None

    return match.group(1)


def get_pkgs_in_ws(src_space):
    pkg_name_with_path = defaultdict(str)

    for root, dirs, files in os.walk(src_space, followlinks=True):
        # are we in a package?
        if "CMakeLists.txt" in files:
            cmake_lists_file = os.path.join(root, "CMakeLists.txt")

            if not is_catkin_pkg(cmake_lists_file):
                continue

            pkg_name = get_pkg_name(cmake_lists_file)

            if not pkg_name:
                print(("Can not retrieve package name from '{0}' "
                       "- skipping").format(cmake_lists_file))
                continue

            pkg_name_with_path[pkg_name] = os.path.abspath(root)
            dirs[:] = []

    return pkg_name_with_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ws_root", help="the workspace root")

    args = vars(ap.parse_args())
    abs_ws_root = os.path.abspath(args["ws_root"])

    if not is_catkin_ws(abs_ws_root):
        print(("Given argument '{0}' is not a catkin workspace -"
               " aborting".format(abs_ws_root)))

    build_space = get_build_space(abs_ws_root)
    if not build_space:
        print("Can not get build space - aborting", file=sys.stderr)
    src_space = os.path.join(abs_ws_root, "src")

    pkgs_with_path = get_pkgs_in_ws(src_space)
    symlink_compile_commands_for_all_pkgs(build_space, pkgs_with_path)


if __name__ == "__main__":
    main()
