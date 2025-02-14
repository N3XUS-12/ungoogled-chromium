#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Copyright (c) 2019 The ungoogled-chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Prune binaries from the source tree"""

import argparse
from pathlib import Path

from _common import ENCODING, get_logger, add_common_params
import sys
import os
import stat

# List of paths to prune if they exist, excluded from domain_substitution and pruning lists
# These allow the lists to be compatible between cloned and tarball sources
CONTINGENT_PATHS = (
    # Sources
    'third_party/angle/third_party/VK-GL-CTS/src/',
    'third_party/llvm/',
    'third_party/rust-src/',
    # Binaries
    'buildtools/linux64/',
    'buildtools/reclient/',
    'third_party/android_rust_toolchain/',
    'third_party/apache-linux/',
    'third_party/checkstyle/',
    'third_party/dawn/third_party/ninja/',
    'third_party/dawn/tools/golang/',
    'third_party/depot_tools/external_bin/',
    'third_party/devtools-frontend/src/third_party/esbuild/',
    'third_party/google-java-format/',
    'third_party/libei/',
    'third_party/llvm-build-tools/',
    'third_party/ninja/',
    'third_party/screen-ai/',
    'third_party/siso/',
    'third_party/updater/chrome_linux64/',
    'third_party/updater/chromium_linux64/',
    'tools/luci-go/',
    'tools/resultdb/',
    'tools/skia_goldctl/linux/',
)


def prune_files(unpack_root, prune_list):
    """
    Delete files under unpack_root listed in prune_list. Returns an iterable of unremovable files.

    unpack_root is a pathlib.Path to the directory to be pruned
    prune_list is an iterable of files to be removed.
    """
    unremovable_files = set()
    for relative_file in prune_list:
        file_path = unpack_root / relative_file
        try:
            file_path.unlink()
        # read-only files can't be deleted on Windows
        # so remove the flag and try again.
        except PermissionError:
            os.chmod(file_path, stat.S_IWRITE)
            file_path.unlink()
        except FileNotFoundError:
            unremovable_files.add(Path(relative_file).as_posix())
    return unremovable_files


def _prune_path(path):
    """
    Delete all files and directories in path.

    path is a pathlib.Path to the directory to be pruned
    """
    for node in sorted(path.rglob('*'), key=lambda l: len(str(l)), reverse=True):
        if node.is_file() or node.is_symlink():
            try:
                node.unlink()
            except PermissionError:
                node.chmod(stat.S_IWRITE)
                node.unlink()
        elif node.is_dir() and not any(node.iterdir()):
            try:
                node.rmdir()
            except PermissionError:
                node.chmod(stat.S_IWRITE)
                node.rmdir()


def prune_dirs(unpack_root):
    """
    Delete all files and directories in pycache and CONTINGENT_PATHS directories.

    unpack_root is a pathlib.Path to the source tree
    """
    for pycache in unpack_root.rglob('__pycache__'):
        _prune_path(pycache)
    for cpath in CONTINGENT_PATHS:
        _prune_path(unpack_root / cpath)


def _callback(args):
    if not args.directory.exists():
        get_logger().error('Specified directory does not exist: %s', args.directory)
        sys.exit(1)
    if not args.pruning_list.exists():
        get_logger().error('Could not find the pruning list: %s', args.pruning_list)
    prune_dirs(args.directory)
    prune_list = tuple(filter(len, args.pruning_list.read_text(encoding=ENCODING).splitlines()))
    unremovable_files = prune_files(args.directory, prune_list)
    if unremovable_files:
        get_logger().error('%d files could not be pruned.', len(unremovable_files))
        get_logger().debug('Files could not be pruned:\n%s',
                           '\n'.join(f for f in unremovable_files))
        sys.exit(1)


def main():
    """CLI Entrypoint"""
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path, help='The directory to apply binary pruning.')
    parser.add_argument('pruning_list', type=Path, help='Path to pruning.list')
    add_common_params(parser)
    parser.set_defaults(callback=_callback)

    args = parser.parse_args()
    args.callback(args)


if __name__ == '__main__':
    main()
