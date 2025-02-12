# SPDX-FileCopyrightText: 2025 Legiayayana
#
# SPDX-License-Identifier: EUPL-1.2

import argparse
import json
import logging
import os
import os.path
import sys
from pathlib import Path

from pyswiftebuild import ebuild as swift_ebuild, prepare as swift_prepare

def main(prog_name: str, *argv: str) -> int:
	argp = argparse.ArgumentParser(prog=os.path.basename(prog_name), epilog='If neither --distdir or --install is provided, this tool will generate an ebuild.')
	argp.add_argument('--workdir',
					  type=Path,
					  help='Main directory of the swift package (i.e. has Package.swift).')
	argp.add_argument('--state',
                      action="store_true",
					  help='When enabled, will set up workspace state for building.')
	args = argp.parse_args(argv)

	if args.workdir is None:
		args.workdir = os.getcwd()

	if args.state:
		swift_prepare.construct_build_env(args.workdir)
	else:
		swift_ebuild.build_src_template(args.workdir)

def entry_point() -> None:
	try:
		from rich.logging import RichHandler
	except ImportError:
		logging.basicConfig(
			format='[{levelname:>7}] {message}',
			level=logging.INFO,
			style='{')
	else:
		logging.basicConfig(
			format='{message}',
			level=logging.INFO,
			style='{',
			handlers=[RichHandler(show_time=False, show_path=False)])

	sys.exit(main(*sys.argv))
