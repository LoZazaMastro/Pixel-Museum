"""Persistent user choice: Nintendo 64 uses its original transparent photograph."""
from pathlib import Path
import hashlib


def apply(entries, root):
    root = Path(root)
    local = 'assets/images/user-nintendo-64-console-transparent.png'
    expected = '62c581ce8206acee885cee7b6821ef694dd699dc1eb9837b24bbc58026e83e64'
    if hashlib.sha256((root / local).read_bytes()).hexdigest() != expected:
        raise ValueError('Nintendo 64 original transparent photograph changed')
    owner = next(entry for entry in entries if entry['id'] == 'nintendo-64')
    url = 'https://upload.wikimedia.org/wikipedia/commons/2/27/Nintendo-64-Console-FL.png'
    image = dict(url=url, original_url=url,
                 source_page='https://commons.wikimedia.org/wiki/File:Nintendo-64-Console-FL.png',
                 title='Nintendo 64 console', creator='Evan-Amos',
                 credit='Evan-Amos / Public domain', license='Public domain',
                 license_url='https://creativecommons.org/publicdomain/mark/1.0/',
                 width=4110, height=2760, cover_art=True, cover_role=True,
                 story_paragraph=-1, recovery_local_source=local,
                 verification=dict(sha256=expected, native_dimensions=[4110, 2760],
                                   processing='Unmodified original RGBA PNG; console only, no controller, cable, background, added frame or enlargement.'))
    index = next((i for i, old in enumerate(owner['images']) if old['url'] == url), None)
    if index is None:
        index = len(owner['images'])
        owner['images'].append(image)
    elif owner['images'][index] != image:
        raise ValueError('Conflicting Nintendo 64 image-only metadata')
    owner['preferred_image'] = index
    owner['models'] = []
    adaptive = _apply_adaptive(entries, root)
    gamecube = _apply_gamecube(entries, root)
    return dict(gamecube=gamecube, adaptive=adaptive, status='PASS_USER_N64_IMAGE_ONLY', entry_id=owner['id'],
                preferred_image=index, sha256=expected,
                existing_story_media_preserved=True)


def _apply_adaptive(entries, root):
    local = 'assets/images/user-xbox-adaptive-controller-transparent.png'
    expected = '1eef49fcb8635de88b96d04ea901c3ce47f3bd487919a5d51cc077086e5a83b5'
    if hashlib.sha256((root / local).read_bytes()).hexdigest() != expected:
        raise ValueError('Xbox Adaptive Controller approved transparent asset changed')
    owner = next(entry for entry in entries if entry['id'] == 'daily-12-03')
    url = 'https://ukstories.microsoft.com/wp-content/uploads/2018/05/AdptvCntlr_ANL_Tlt_Alt_RGB-5afc6066b891e.jpg'
    image = dict(url=url, original_url=url,
                 source_page='https://ukstories.microsoft.com/features/the-xbox-adaptive-controller-in-pictures/',
                 title='Xbox Adaptive Controller', creator='Microsoft / Xbox',
                 credit='Microsoft / Xbox; background removed for museum display',
                 license='Original Microsoft product photograph rights retained; background-only edited derivative',
                 license_url='', width=1622, height=970, cover_art=True, cover_role=True,
                 story_paragraph=-1, recovery_local_source=local,
                 verification=dict(sha256=expected, native_dimensions=[1622,970],
                    source_dimensions=[10826,6471],
                    processing='Official Microsoft product photograph; surrounding white background removed with imagegen. Transparent edited derivative; not an unmodified source original. Original photograph preserved in research. No frame or enlargement.'))
    index = next((i for i, old in enumerate(owner['images']) if old['url'] == url), None)
    if index is None:
        index = len(owner['images'])
        owner['images'].append(image)
    elif owner['images'][index] != image:
        raise ValueError('Conflicting Xbox Adaptive Controller transparent metadata')
    owner['preferred_image'] = index
    return dict(status='PASS_USER_ADAPTIVE_TRANSPARENT_HERO', entry_id=owner['id'],
                preferred_image=index, sha256=expected, existing_story_media_preserved=True)


def _apply_gamecube(entries, root):
    local = 'assets/images/user-gamecube-console-only-transparent.png'
    expected = 'ed2c072b39d717e57a3935b81b215d794afc8009073c23f71edff5cc0522924d'
    if hashlib.sha256((root / local).read_bytes()).hexdigest() != expected:
        raise ValueError('GameCube original console-only photograph changed')
    owner = next(entry for entry in entries if entry['id'] == 'workbook-09-14-nintendo-gamecube')
    url = 'https://upload.wikimedia.org/wikipedia/commons/7/72/Lone_GameCube.png'
    image = dict(url=url, original_url=url,
                 source_page='https://commons.wikimedia.org/wiki/File:Lone_GameCube.png',
                 title='Nintendo GameCube console', creator='Alphathon',
                 credit='Alphathon / CC BY-SA 3.0',
                 license='Creative Commons Attribution-ShareAlike 3.0',
                 license_url='https://creativecommons.org/licenses/by-sa/3.0/',
                 width=1632, height=1224, cover_art=True, cover_role=True,
                 story_paragraph=-1, recovery_local_source=local,
                 verification=dict(sha256=expected, native_dimensions=[1632,1224],
                    processing='Unmodified original transparent PNG; console only with no attached controller, cable or memory card. No generated edit, crop, frame or enlargement.'))
    index = next((i for i, old in enumerate(owner['images']) if old['url'] == url), None)
    if index is None:
        index = len(owner['images'])
        owner['images'].append(image)
    elif owner['images'][index] != image:
        raise ValueError('Conflicting GameCube console-only metadata')
    owner['preferred_image'] = index
    owner['models'] = []
    return dict(status='PASS_USER_GAMECUBE_ORIGINAL_IMAGE_ONLY', entry_id=owner['id'],
                preferred_image=index, sha256=expected, existing_story_media_preserved=True)
