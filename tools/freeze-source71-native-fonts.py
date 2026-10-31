"""Preserve the complete native SOURCE71 pair before sidecar-v2 changes."""
from pathlib import Path
source = Path(__file__).with_name('freeze-source57-native-fonts.py')
text = source.read_text(encoding='utf8')
replacements = {
    'source57': 'source71', 'pre-alias': 'pre-sidecar-v2',
    'f8a884b849deaa85845a9b37cdb6a31e6224047aa54b393f70a4ac565281867d': 'd9bcc815820c53fef97efbc0b279cd6ef03047bcfd98f577906fbe5383e7989d',
    'eccc4d9df1f1a41ee02392f91422f984985c0dd0bd272fced73e8971b73c5773': '95e461787332ea4473508793f1018b75d30908cf18d7842a10d1207397e7a8c1',
    '0808fffad3e0b7f652826f9d8ab803c7fa22bd06f57dc92fb308d060041a0805': '8c16ac2c317ab6af4e57e9300ce29df2c59b52e248f9a4ac8ba68b084d020156',
    'd1817b6260cc7b7fbea6ec2037a55d68774e76c184a075ff4301bf1cca13bccf': '69a769c4e20fb551107fc0c20f8f3143d1e5fb70a7289e29bac7c2332e514949',
}
for old, new in replacements.items():
    text = text.replace(old, new)
text = text.replace('records = {}', "paths.update(('src/museum/object_artwork_cache.hpp','tests/object-scene/bake-artwork-cache.cpp','tools/model_artwork_cache.py','tools/prepare-model-artwork-cache.py','build/research/grouped-source71/verification.json'))\nrecords = {}")
exec(compile(text, str(source), 'exec'), {'__file__': str(source)})
