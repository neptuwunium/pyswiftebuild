# SPDX-FileCopyrightText: 2025 Legiayayana
#
# SPDX-License-Identifier: EUPL-1.2

import subprocess
import json
import logging
import os.path
from typing import Set, Any
from enum import Enum

type JSONData = dict[str, Any]

class ArtifactType(Enum):
	executable = 'exe'
	shared = 'so'
	static = 'a'


class BuildArtifact():
	name: str
	artifact_type: ArtifactType
	ebuild: str


	def __init__(self, name: str, artifact_type: ArtifactType):
		self.name = name
		self.artifact_type = artifact_type
		self.ebuild = f'"{artifact_type.value} {name}"'


	def __hash__(self): return self.name.__hash__()


	def __eq__(self, other):
		if isinstance(other, BuildArtifact):
			return self.name == other.name


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
		self.tarball = f'{self.url}/archive/{self.revision}.tar.gz'
		self.ebuild = f'"{name} {self.url} {self.revision}"'


	def __hash__(self): return self.tarball.__hash__()


	def __eq__(self, other):
		if isinstance(other, BuildArtifact):
			return self.tarball == other.tarball


class BuildDependency():
	name: str
	state: BuildDependencyState
	data: JSONData
	version: int


	def __init__(self, name: str, state: BuildDependencyState, data: JSONData, version: int):
		self.name = name
		self.state = state
		self.data = data
		self.version = version

	def __hash__(self): return f'{self.name}-{self.state.tarball}'.__hash__()


def get_package_json(path: str) -> JSONData:
	call = subprocess.run(['swift', 'package', 'dump-package'], capture_output=True, cwd=path)
	text = call.stdout.decode('utf8').strip()
	if call.returncode != 0:
		raise RuntimeError(f'could not successfully call swift package dump-package: {call.stderr.decode('utf8').strip()}')
	return json.loads(text)


def get_tool_version(path: str) -> str:
	call = subprocess.run(['swift', 'package', 'tools-version'], capture_output=True, cwd=path)
	text = call.stdout.decode('utf8').strip()
	if call.returncode != 0:
		raise RuntimeError(f'could not successfully call swift package tools-version: {call.stderr.decode('utf8').strip()}')
	return text


def get_package_resolved(path: str) -> JSONData:
	resolved_path = os.path.join(path, 'Package.resolved')
	if not os.path.exists(resolved_path):
		call = subprocess.run(['swift', 'package', 'resolve'], capture_output=True, cwd=path)
		text = call.stdout.decode('utf8').strip()
		if call.returncode != 0:
			raise RuntimeError(f'could not successfully call swift package resolve: {call.stderr.decode('utf8').strip()}')
		logging.warning(f'# called swift package resolve, ensure that the build directory has Package.resolved when compiling')
	if not os.path.exists(resolved_path):
		logging.warning(f'# could not locate {resolved_path}, assuming it\'s empty')
		return {}
	with open(resolved_path, 'r') as resolved:
		return json.load(resolved)


def get_artifacts(path: str) -> [BuildArtifact]:
	package = get_package_json(path)
	artifacts: Set[BuildArtifact] = set()

	for product in package['products']:
		if 'executable' in product['type']:
			artifacts.add(BuildArtifact(product['name'], ArtifactType.executable))
		if 'library' in product['type']:
			library_types = product['type']['library']
			if not isinstance(library_types, list):
				library_types = [library_types]

			for library_type in library_types:
				if library_type == 'automatic' or library_type is None:
					logging.warning(f'# library product {product['name']} does not produce build artifacts as it is an automatic library. set libraryType to either .static or .dynamic.')
					continue
				elif library_type == 'dynamic':
					artifacts.add(BuildArtifact(f'lib{product['name']}.so', ArtifactType.shared))
				else:
					artifacts.add(BuildArtifact(f'lib{product['name']}.a', ArtifactType.static))

	return artifacts


def get_dependencies(path: str) -> [BuildDependency]:
	package = get_package_resolved(path)
	dependencies: Set[BuildDependency] = set()
	version = package['version']

	pins = package['pins'] if version >= 2 else package['object']['pins']

	for dependency in pins:
		if version >= 2:
			if dependency['kind'] != 'remoteSourceControl':
				logging.error(f'# {dependency['identity']} is not remoteSourceControl, it is {dependency['kind']} which this can\'t handle (yet.)')
				continue
			name = dependency['identity']
			state = BuildDependencyState(name, dependency['location'], dependency['state'])
		else:
			name = dependency['package']
			state = BuildDependencyState(name, dependency['repositoryURL'], dependency['state'])
		dependencies.add(BuildDependency(name, state, dependency, version))

	return dependencies
