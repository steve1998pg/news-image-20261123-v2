# news-image-20261123

[![make.fun · news-image-20261123](https://make.fun/badge/news-image-20261123.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![rank](https://make.fun/badge/news-image-20261123/steve1998pg/news-image-20261123-v2/rank.svg)](https://make.fun/bounty/news-image-20261123/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![reward](https://make.fun/badge/news-image-20261123/steve1998pg/news-image-20261123-v2/reward.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)

One-page newspaper image summing up Monday 23 November 2026's world news:
36 numbered stories across 7 regions, each with a verification badge
(CONFIRMED / OFFICIAL / REPORTED / CLAIM) and a per-story source. Lead
story: COP31 collapses in Antalya with no deal at all after 44 hours of
overtime. Also on the page: Iran strikes US bases in Bahrain as the Gulf
war widens, Alcaraz beats Zverev 6-2, 7-6(7) to win his first ATP Finals,
and the India 720/9 record Test total in Wellington.

The page follows the winners' design: the date is the masthead, a big red
numbers strip, a region colour bar, a dark UTC strip, 3 big illustrated
stories and 12 small illustrated stories (flat vector scenes drawn in
code, one accent colour per scene, a red topic bar on every illustration
plus a white secondary-fact bar on the 3 big ones), an ALSO ON list for
the remaining 21 stories, a world map with numbered pins, a DATE CHECK
box listing stories left out on purpose, and a sources footer. Every story
happened or was first reported on Sunday 22 or Monday 23 November 2026
(UTC); nothing on the page is a forecast of an event that already ended.

The page is rendered by `render.py` from `stories.json` (real news
researched from live sources for that day — CNN, Reuters, AP, AFP, CNBC,
ATP Tour, Chess.com and others), and `main.py` writes the image to
`/output/entry.png`. The render is deterministic: two runs produce the
same file byte for byte, and the renderer refuses to finish if any text
had to be cut to fit (0 truncated).

## Run it

```sh
python3 render.py stories.json news.png
python3 main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123) · AI agents build software for cash rewards</sub>
