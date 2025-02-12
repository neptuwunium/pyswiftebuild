# SPDX-FileCopyrightText: 2025 Legiayayana
#
# SPDX-License-Identifier: EUPL-1.2

import datetime

from pyswiftebuild import swiftpm

def build_src_template(workdir: str) -> str:
	SWIFT_CHECKOUTS=''
	for dependency in swiftpm.get_dependencies(workdir):
		SWIFT_CHECKOUTS = f'{SWIFT_CHECKOUTS}\n\t{dependency.state.ebuild}'
	if len(SWIFT_CHECKOUTS) > 0:
		SWIFT_CHECKOUTS = f'\nSWIFT_CHECKOUTS=(\n\t{SWIFT_CHECKOUTS.strip()}\n)\n'

	SWIFT_ARTIFACTS=''
	for artifact in swiftpm.get_artifacts(workdir):
		SWIFT_ARTIFACTS = f'{SWIFT_ARTIFACTS}\n\t{artifact.ebuild}'
	if len(SWIFT_ARTIFACTS) > 0:
		SWIFT_ARTIFACTS = f'\nSWIFT_ARTIFACTS=(\n\t{SWIFT_ARTIFACTS.strip()}\n)\n'

	ebuild = f"""
# Copyright {datetime.date.today().year} Gentoo Authors
# Distributed under the terms of the GNU General Public License v2
EAPI=8

SWIFT_PV="{swiftpm.get_tool_version(workdir)}"
{SWIFT_CHECKOUTS}{SWIFT_ARTIFACTS}
inherit swift

DESCRIPTION=""
HOMEPAGE=""
LICENSE=""
SLOT="0"

SRC_URI="
	${{SWIFT_URIS}}
"
KEYWORDS="~amd64"
	"""

	print(ebuild)

	return ebuild
