# SPDX-FileCopyrightText: 2025 Legiayayana
#
# SPDX-License-Identifier: EUPL-1.2

import os
import os.path
import json
from pyswiftebuild import swiftpm

def construct_build_env(workdir: str):
	dependencies = []

	for dependency in swiftpm.get_dependencies(workdir):
		dependencies.append({
			'basedOn': None,
			'packageRef': {
				'identity': dependency.data['identity'],
				'kind': dependency.data['kind'],
				'location': dependency.data['location'],
				'name': dependency.data['identity'],
			},
			'state': {
				'checkoutState': dependency.data['state'],
				'name': 'sourceControlCheckout'
			},
			'subpath': f'{dependency.name}-{dependency.state.revision}'
		})

	workspaceState = {
		'object': {
			'artifacts': [],
			'dependencies': dependencies
		},
		'version': 6
	}

	with open(os.path.join(workdir, '.build/workspace-state.json'), 'w') as stateFile:
		json.dump(workspaceState, stateFile, indent=2)
