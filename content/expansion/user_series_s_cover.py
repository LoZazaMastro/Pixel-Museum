"""User-selected, unmodified Series S transparent product artwork."""
from pathlib import Path
import hashlib


def apply(entries, root):
    root = Path(root)
    local = 'assets/images/user-xbox-series-s-console-controller.png'
    expected = '7bc71babdae5151fda0ffc73623e8ce052ca8985c59bfe548d065cbe19974ed3'
    if hashlib.sha256((root / local).read_bytes()).hexdigest() != expected:
        raise ValueError('User-selected Series S artwork changed')
    owner = next(entry for entry in entries if entry['id'] == 'xbox-series-s')
    url = 'https://museum.local/user/xbox-series-s-console-controller.png'
    image = dict(url=url, original_url=url, source_page=url,
                 title='Xbox Series S and controller', creator='Microsoft',
                 credit='Microsoft product artwork; exact transparent PNG supplied and selected by the user.',
                 license='Original rights retained; user-supplied product artwork.',
                 width=857, height=676, cover_art=True, cover_role=True,
                 story_paragraph=-1, recovery_local_source=local,
                 verification=dict(sha256=expected, native_dimensions=[857, 676],
                                   processing='Exact user-supplied transparent PNG, no retouching, frame or enlargement.'))
    index = next((index for index, old in enumerate(owner['images']) if old['url'] == url), None)
    if index is None:
        index = len(owner['images'])
        owner['images'].append(image)
    elif owner['images'][index] != image:
        raise ValueError('Conflicting user-selected Series S artwork metadata')
    owner['preferred_image'] = index
    owner['models'] = []
    return dict(status='PASS_USER_SELECTED_IMAGE_ONLY_HERO', entry_id=owner['id'],
                preferred_image=index, sha256=expected, existing_story_media_preserved=True)
