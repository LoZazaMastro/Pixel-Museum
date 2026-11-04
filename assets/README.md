# Collection assets

Original media is distributed through GitHub Releases with source and attribution records. First-time installation downloads the image collection and checks for the current cumulative database before opening the museum. The Windows installer performs this step during setup; the PS5 application performs it during the introduction.

To restore the bundled media for a local build, extract the current PlayStation 5 release and run the following command.

```sh
python3 tools/restore-source-data.py --package /path/to/PPSA70421
```

The pinned collection archives and their SHA-256 values are listed in `content/collection-packs.json`. Keep that manifest and `content/collection-archive-index.json` together. These archives supply `assets/images/manifest.json` and the original image cache. Their installation identity is shared across application updates.

Database supplements are listed individually in `website/database-update.json`, with their destination paths, byte counts and SHA-256 values. The update is cumulative and reuses matching local files. The application bundle retains its baseline revision; the downloaded database has its own activation marker. Images, recordings and other third-party works retain their respective rights and terms.
