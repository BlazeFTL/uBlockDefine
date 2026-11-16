import json
import os
import pathlib
import sys

ROOT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).parent
DEFAULT_ID = 'ublockdefine@define.fork'

repo = os.environ.get('GITHUB_REPOSITORY', '').strip()
if not repo:
    sys.exit('GITHUB_REPOSITORY is not set')

addon_id = os.environ.get('ADDON_ID', '').strip() or DEFAULT_ID
if 'raymondhill' in addon_id:
    sys.exit(f'ADDON_ID must not be upstream id: {addon_id}')

path = ROOT / 'platform/firefox/manifest.json'
manifest = json.loads(path.read_text(encoding='utf-8'))
gecko = manifest['browser_specific_settings']['gecko']
gecko['id'] = addon_id
gecko['update_url'] = f'https://github.com/{repo}/releases/download/updates/updates.json'
path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(f"OK   [update_url] id={addon_id} url={gecko['update_url']}")
