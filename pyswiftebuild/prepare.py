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
		data = dependency.data
		version = dependency.version
		dependencies.append({
			'basedOn': None,
			'packageRef': {
				'identity': data['identity'] if 'identity' in data else data['package'].lower(),
				'kind': data['kind'] if 'kind' in data else 'remoteSourceControl',
				'location': data['location'] if 'location' in data else data['repositoryURL'],
				'name': data['package'] if 'package' in data else data['identity'],
			},
			'state': {
				'checkoutState': data['state'],
				'name': 'sourceControlCheckout'
			},
			'subpath': f'{dependency.name}-{dependency.state.revision}'
		})

	workspaceState = {
		'object': {
			'artifacts': [],
			'dependencies': dependencies,
		},
		'version': 6
	}

	with open(os.path.join(workdir, '.build/workspace-state.json'), 'w') as stateFile:
		json.dump(workspaceState, stateFile, indent=2)
