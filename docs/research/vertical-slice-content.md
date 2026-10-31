# Pixel Museum: First Rooms

This is a selector for an installable first exhibition, not a replacement for the full research catalogue. The configuration is `content/vertical-slice.json`; it retains the existing, sourced English articles and their complete paragraphs. Start at **Game Boy**, then allow chronological navigation through all sixteen stops.

The selection favours identifiable people, decisions and objects rather than a wall of disconnected dates. It includes the television-game prototype team, Jerry Lawson's engineering team, Roberta Williams and Carol Shaw; games that connect technology with a different kind of play; and four licensed, bundled console models. The writing ranges from short object labels to four-paragraph feature narratives. It is not a claim that every short label is a complete biography or exhaustive history.

| Year | Entry ID | Exhibition purpose | Media |
| --- | --- | --- | --- |
| 1958 | `tennis-for-two` | Scientific equipment becomes shared public play | Two photographs; Brookhaven's reconstruction film |
| 1968 | `brown-box` | Ralph Baer, Bill Harrison and Bill Rusch develop television-game prototypes | Two hardware/archive images; Smithsonian source |
| 1976 | `channel-f` | Jerry Lawson and a multidisciplinary team make interchangeable software a household object | Console, Lawson portrait and cartridge images; Lawson interview |
| 1980 | `roberta-williams` | A drawing changes how a player enters an adventure | Two Mystery House screenshots; creator source |
| 1982 | `carol-shaw` | A small cartridge holds a long, learnable river | Two portraits; papers and creator interview |
| 1984 | `karateka` | Animation reference and prototypes make design decisions visible | Digital Eclipse artwork and official film |
| 1984 | `tetris` | A simple rule set travels across machines and borders | Hardware photograph; original authored narrative |
| 1989 | `game-boy` | Portable play connects hardware, software and everyday routines | Two photographs; licensed 3D object |
| 1993 | `doom` | Distribution, movement and multiplayer reshape PC play | Two screenshots; John Romero film selected by The Strong |
| 2000 | `playstation-2` | A console shares the living room with DVD culture and an existing game collection | Hardware photograph; licensed 3D object; Sony history |
| 2011 | `nintendo-3ds` | A familiar handheld gains depth and new inputs | Original Aqua Blue photograph; licensed 3D object; Nintendo specifications |
| 2012 | `journey` | Movement and waiting become ways for strangers to communicate | Two screenshots; creator presentation and launch account |
| 2013 | `papers-please` | A small inspection desk exposes a larger political system | Two screenshots; Lucas Pope's official trailer and press kit |
| 2017 | `switch` | One machine moves between handheld and television play | Hardware photograph; licensed 3D object |
| 2018 | `celeste` | Short retries, precise movement and assist options support a personal journey | Two screenshots; official launch trailer |
| 2023 | `preserving-play` | Documents, prototypes, restoration and emulation keep history accessible | Restored PDP-1 photograph; Digital Eclipse documentary trailer |

## Live remote checks

On 20 October 2026, each of the **27 selected image URLs** returned HTTP 200 to a fresh GET request and decoded as an actual image. These checks did not read the museum's local image cache. Images range from 320 × 432 to 1920 × 1736; some archive and portrait thumbnails are deliberately modest in resolution. Gallery zoom must respect the available detail.

All **five distinct YouTube IDs** passed a fresh YouTube oEmbed check; title and channel matched their intended primary/archive sources. All thumbnail URLs also returned real images. The preservation entry intentionally reuses the Karateka film with a different curatorial context. This tests source availability and identity, not PS5 decoder or stream playback; native playback still needs the build's separate console check.

| YouTube ID | Verified title | Verified channel |
| --- | --- | --- |
| `u6mu5B-YZU8` | First Video Game? | Brookhaven Lab |
| `IrS2pipZaH0` | The Making of Karateka - Trailer - Digital Eclipse Gold Master Series 01 | Digital Eclipse |
| `6y3sK4xKcVs` | DOOM by John Romero | The Strong Museum |
| `_QP5X6fcukM` | Papers, Please - Trailer | Lucas Pope |
| `FqBj2IGg6Uw` | Celeste Launch Trailer | Maddy Thorson |

The selector contains the exact requests, response types, decoded dimensions, checked time, oEmbed titles/channels, source catalogue hash, entry counts and model asset hashes. There were no failed selected media requests in this run. Availability is a dated observation, not a permanent guarantee: preserve the application's missing/offline states.

## Packaging and credits

Use the Game Boy, PlayStation 2, Nintendo 3DS and Switch model records already attached to their entries. Preserve each asset's individual creator credit, licence, required notices and source page. In particular, the Game Boy and PlayStation 2 licences contain noncommercial conditions; the application's own source licence does not replace those conditions. This document does not relicense any artwork or model.

The PlayStation/PVM model is deliberately excluded from the first physical-console slice pending measurement of its approximately 1.94 GiB GPU footprint. No new replacement model is silently inserted. The clean Atari Lynx can be a seventeenth stop after the native model merge and matching history entry are present; `optional_after_native_merge` records that possibility without making the current selector refer to an absent entry.

Keep article sources and media credits reachable from every stop. Commons photographs have their recorded public-domain or Creative Commons terms. IGDB game images and Digital Eclipse artwork remain remote editorial references with copyright retained by their respective rights holders; do not relabel them as open-licensed images or bundle them as application-owned assets. YouTube films continue to use the original online sources.

## Boundaries

This small first exhibition is intentionally weighted towards the strongest available illustrated stories. It is not a balanced world history by itself: the broader catalogue provides additional regions, creators and decades. It also does not add new prose, manufacture missing interviews, move release dates to match a model variant, or mutate the full catalogue. Source availability, native media playback and physical-console performance are separate checks.
