# Collection assets

The complete app media is distributed in the release package, together with individual source and license records. To restore it for a local build, extract the full release and run:

```sh
python3 tools/restore-source-data.py --package /path/to/PPSA70421
```

This copies the packaged assets into this checkout. It does not change the original package. Images, recordings and other third-party works retain their respective terms; the application source license does not relicense them.
