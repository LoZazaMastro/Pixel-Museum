"""Validate the Games process profile exercised on the PS5 with the direct arena.

Keep metadata and the native allocator together. The earlier Media profile and
mixed Games/Media attributes are not valid substitutes for this configuration.
"""

def validate_native_profile(param):
    expected = {
        'titleId': 'PPSA70421',
        'conceptId': '70421',
        'applicationCategoryType': 0,
        'contentBadgeType': 1,
        'attribute': 1644167168,
        'attribute2': 0,
        'attribute3': 1048576,
        'downloadDataSize': 256,
        'amm': {
            'multimapVaRangeInGib': 512,
            'pagetableMemorySizeInMib': 256,
            'vaRangeInGib': 512,
        },
        'kernel': {
            'cpuPageTableSize': 268435456,
            'gpuPageTableSize': 268435456,
        },
        'gameIntent': {'permittedIntents': [{'intentType': 'launchActivity'}]},
    }
    for key, value in expected.items():
        assert param.get(key) == value, f'Incorrect native Games profile: {key}'
