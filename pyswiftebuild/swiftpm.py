# SPDX-FileCopyrightText: 2025 Legiayayana
#
# SPDX-License-Identifier: EUPL-1.2

import subprocess
import json
import logging
import os.path
from typing import Set


class BuildArtifact():
	name: str
	is_library: bool


	def __init__(self, name: str, is_library: bool):
		self.name = name
		self.is_library = is_library


	def __hash__(self): return self.name.__hash__()


class BuildDependencyState():
	revision: str
	version: str | None
	branch: str | None
	url: str
	tarball: str
	ebuild: str


	def __init__(self, name: str, url: str, state):
		if url.endswith('.git'):
			url = url[:-4]
		self.url = url
		self.revision = state['revision']
		self.version = state['version'] if 'version' in state else None
		self.branch = state['branch'] if 'branch' in state else None
		self.tarball = f'{self.url}/archive/{self.version or self.revision}.tar.gz'
		self.ebuild = f'{name}@{self.version or self.revision}'


	def __hash__(self): return self.tarball.__hash__()


class BuildDependency():
	name: str
	state: BuildDependencyState


	def __init__(self, name: str, state: BuildDependencyState):
		self.name = name
		self.state = state

	def __hash__(self): return f'{self.name}-{self.state.tarball}'.__hash__()


def get_package_json(path: str):
	call = subprocess.run(['swift', 'package', 'dump-package'], capture_output=True, cwd=path)
	text = call.stdout.decode('utf8').strip()
	if call.returncode != 0:
		raise f'could not successfully call swift package dump-package: {text}'
	return json.loads(text)


def get_tool_version(path: str) -> str:
	call = subprocess.run(['swift', 'package', 'tools-version'], capture_output=True, cwd=path)
	text = call.stdout.decode('utf8').strip()
	if call.returncode != 0:
		raise f'could not successfully call swift package tools-version: {text}'
	return text


def get_package_resolved(path: str):
	resolved_path = os.path.join(path, 'Package.resolved')
	if not os.path.exists(resolved_path):
		call = subprocess.run(['swift', 'package', 'resolve'], capture_output=True, cwd=path)
		text = call.stdout.decode('utf8').strip()
		if call.returncode != 0:
			raise f'could not successfully call swift package resolve: {text}'
		logging.warning(f'called swift package resolve, ensure that the build directory has Package.resolved when compiling')
	if not os.path.exists(resolved_path):
		logging.warning(f'could not locate {resolved_path}, assuming it\'s empty')
		return {}
	with open(resolved_path, 'r') as resolved:
		return json.load(resolved)


def get_artifacts(path: str) -> [BuildArtifact]:
	package = get_package_json(path)
	artifacts: Set[BuildArtifact] = set()

	for target in package['targets']:
		if target['type'] != 'executable': continue
		artifacts.add(BuildArtifact(target['name'], False))

	for product in package['products']:
		if 'executable' in product['type']:
			artifacts.add(BuildArtifact(product['name'], False))
		if 'library' in product['type']:
			library_type = product['type']['library']
			if library_type == 'automatic' or library_type is None:
				logging.warning(f'library product {product['name']} does not produce build artifacts as it is an automatic library. set libraryType to either .static or .dynamic.')
				continue
			elif library_type == 'dynamic':
				artifacts.add(BuildArtifact(f'lib{product['name']}.so', True))
			else:
				artifacts.add(BuildArtifact(f'lib{product['name']}.a', True))

	return artifacts


def get_dependencies(path: str) -> [BuildDependency]:
	package = get_package_resolved(path)
	dependencies: Set[BuildDependency] = set()

	for dependency in package['pins']:
		if dependency['kind'] != 'remoteSourceControl': continue
		name = dependency['identity']
		state = BuildDependencyState(name, dependency['location'], dependency['state'])
		dependencies.add(BuildDependency(name, state))

	return dependencies
