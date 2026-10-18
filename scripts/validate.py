#!/usr/bin/env python3
"""Check canonical asset/evidence integrity, then use Braidplane's own validator."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def asset(root, name):
    if not isinstance(name, str) or Path(name).is_absolute():
        raise ValueError('asset path must be repository-relative')
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError('missing or out-of-repository asset: ' + name)
    return path


def load(root, name):
    return json.loads(asset(root, name).read_text())


def validate_repository(root):
    manifest = load(root, 'manifest.json')
    if manifest['schema_version'] != 1:
        raise ValueError('unsupported manifest schema version')
    asset(root, manifest['fixture_server'])
    for path in manifest.get('shared_assets', []):
        load(root, path)
    recipes = manifest['recipes']
    if len(recipes) != 5 or len({r['slug'] for r in recipes}) != 5:
        raise ValueError('the initial collection requires five distinct recipes')
    for recipe in recipes:
        spec_path = asset(root, recipe['spec'])
        spec = json.loads(spec_path.read_text())
        digest = hashlib.sha256(spec_path.read_bytes()).hexdigest()
        if spec['metadata']['slug'] != recipe['slug']:
            raise ValueError('manifest/spec identity mismatch: ' + recipe['slug'])
        if len(recipe['assets']) != len(set(recipe['assets'])):
            raise ValueError('duplicate asset entry: ' + recipe['slug'])
        for path in recipe['assets']:
            asset(root, path)
        for key in ('docs', 'bindings', 'expected'):
            asset(root, recipe[key])
        load(root, recipe['expected'])
        bindings = load(root, recipe['bindings'])
        if bindings['pipeline'] != recipe['slug']:
            raise ValueError('binding template belongs to a different pipeline')
        refs = {s[s['kind']]['data_source_ref'] for s in spec['steps'] if s['kind'] in ('query', 'sink')}
        if {b['logical_ref'] for b in bindings['bindings']} != refs:
            raise ValueError('binding template omits or invents a logical ref')
        operations = {o['slug']: o for o in recipe.get('operations', [])}
        for step in spec['steps']:
            if step['kind'] not in ('query', 'sink'):
                continue
            config = step[step['kind']]
            ref = config.get('operation_ref')
            if ref:
                operation = operations[ref]
                if operation['data_source_ref'] != config['data_source_ref']:
                    raise ValueError('saved operation is bound to a different logical source')
                load(root, operation['statement'])
        validation = load(root, recipe['validation']['evidence'])
        execution = load(root, recipe['execution']['evidence'])
        if recipe['validation']['status'] != 'passed' or validation['result'] != 'passed' or validation['spec_sha256'] != digest:
            raise ValueError('missing or stale validation evidence: ' + recipe['slug'])
        if recipe['execution']['status'] != 'verified_local' or execution['execution_status'] != 'succeeded' or execution['spec_file_sha256'] != digest:
            raise ValueError('missing or stale execution evidence: ' + recipe['slug'])
        fixture_dir = Path(recipe['spec']).parent / 'fixtures'
        required_hashes = {path for path in recipe['assets'] if Path(path).is_relative_to(fixture_dir)}
        required_hashes.update(operation['statement'] for operation in recipe.get('operations', []))
        required_hashes.update(recipe['setup_assets'])
        required_hashes.add(recipe['expected'])
        if not required_hashes.issubset(execution['qualification_asset_hashes']):
            raise ValueError('missing qualification input hashes: ' + recipe['slug'])
        for path, expected_hash in execution['qualification_asset_hashes'].items():
            if hashlib.sha256(asset(root, path).read_bytes()).hexdigest() != expected_hash:
                raise ValueError('stale execution input/expected evidence: ' + path)
        if execution['pipeline_slug'] != recipe['slug'] or not execution['run_slug'] or not execution['executed_spec_hash']:
            raise ValueError('execution identity missing or contradictory')
        succeeded = {e['step'] for e in execution['events'] if e['type'] == 'step_succeeded' and e['status'] == 'succeeded'}
        if succeeded != {s['slug'] for s in spec['steps']} or execution['destination_comparison']['expected_output_match'] is not True:
            raise ValueError('execution lacks complete step/destination evidence')
    for path in root.rglob('*.md'):
        if '.git' in path.parts:
            continue
        page = asset(root, str(path.relative_to(root)))
        for link in re.findall(r'\]\(([^)]+)\)', page.read_text()):
            if '://' not in link and not link.startswith('#'):
                asset(root, str(path.parent.relative_to(root) / link.split('#', 1)[0]))
    return len(recipes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cli', default='braidplane', help='Compatible Braidplane executable')
    args = parser.parse_args()
    count = validate_repository(ROOT)
    subprocess.run([args.cli, 'pipeline', 'validate', '--dir', str(ROOT / 'recipes'), '--local'], check=True)
    print(f'Validated {count} canonical recipes and asset/evidence references; provider execution is separate.')


if __name__ == '__main__':
    main()
