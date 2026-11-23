# news-image-20261123

[![make.fun · news-image-20261123](https://make.fun/badge/news-image-20261123.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![rank](https://make.fun/badge/news-image-20261123/steve1998pg/news-image-20261123-v2/rank.svg)](https://make.fun/bounty/news-image-20261123/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![reward](https://make.fun/badge/news-image-20261123/steve1998pg/news-image-20261123-v2/reward.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)

One-page newspaper image summing up Monday 23 November 2026's world news:
36 numbered stories across 7 regions, each with a verification badge
(CONFIRMED / OFFICIAL / REPORTED / CLAIM) and a per-story source. Lead
story: COP31 collapses in Antalya with no deal at all after 44 hours of
overtime. Also on the page: Iran claims strikes on US bases in Bahrain as
the Gulf war widens, Alcaraz beats Zverev 6-2, 7-6(7) to win his first
ATP Finals, and the India 720/9 record Test total in Wellington.

The page follows the winners' design: the date is the masthead, a big red
numbers strip, a region colour bar, a dark UTC strip, 3 big illustrated
stories and 12 small illustrated stories (flat vector scenes drawn in
code, one accent colour per scene, a red topic bar on every illustration
plus a white secondary-fact bar on the 3 big ones), an ALSO ON list for
the remaining 21 stories, a world map with numbered pins, a DATE CHECK
box listing stories left out on purpose, and a sources footer. Every story
happened or was first reported on Sunday 22 or Monday 23 November 2026
(UTC); nothing on the page is a forecast of an event that already ended.

## v3 — fact-checked rebuild (23 Nov 2026)

The v2 page was fact-checked story by story (see `FACT-CHECK-23.md`).
32 of 36 stories were right; 4 were dated outside the 22–23 Nov window
and are replaced here with verified stories from those two days:

- **#11** UN lethal-AI talks (agreed Sat 21 Nov) → tankers struck leaving
  the Strait of Hormuz (World, REPORTED, Reuters · UKMTO).
- **#27** Apple Watch Ultra deal (running since 30 Oct) → India women
  edge S Korea 2-1 in Bhopal (Sport, CONFIRMED, Hockey India).
- **#28** FBI/NCIC database hack (first reported Fri 20 Nov) → Iran
  masses 14 tankers at Kharg Island (Middle East, REPORTED, Euronews).
- **#34** Melat Kiros, first Gen Z in Congress (won 3 Nov) → COP31
  backlash: Bowen told to quit as Pacific islands despair (Asia-Pacific,
  CONFIRMED, Reuters).

Attribution and place errors fixed at the same time: #2 is now written as
an IRGC **claim** (the US and Bahrain deny military damage; the 2 wounded
were hurt in a fire at a civilian site in Sitra); #21 is Wawa, Niger
State (not Kano); #23 was signed in Brussels (not Jakarta) and the
headline now says the deal scraps duties on 98.5% of tariff lines; #24 is
Liverpool (Anfield, not Manchester); #30 is Indore, India; #33 names
Shuri Castle; #35 is sourced to AP · Reuters; #36 is sourced to the Wall
Street Journal (not "Report"). Small corrections: #4 notes one crewman
slightly hurt; #5 says "at least 14"; #10 notes a follow-up meeting is
promised. The UTC strip's wrong lethal-AI line (00:02) is replaced with
"03:00 Shuri Castle reopens in Okinawa". Region counts are recalculated:
World 2, Middle East 3, Europe 5, Asia-Pacific 11, Americas 4, Africa 5,
Sport 6 (= 36).

`render.py` also gains a new flat-vector **hockey** scene (green pitch,
players with sticks, ball, goal) for the Bhopal story, the thinnest small
scenes (talks, exam, health, chess, UN) gain extra props, and the map pin
nudges are recomputed so no two pins overlap (v2 had Turin/Geneva 1.4 px
apart). Note: #27, #28 and #34 are ALSO ON headline-only slots, so the
hockey scene is registered in `render.py` and recorded on the story, but
no illustration slot exists for it on the page.

The page is rendered by `render.py` from `stories.json` (real news
researched from live sources for that day — CNN, Reuters, AP, AFP, CNBC,
ATP Tour, Chess.com, The Hindu, Wisden, Nikkei Asia, SCMP, UKMTO,
Euronews, Hockey India, Wall Street Journal, NY Post and others), and
`main.py` writes the image to `/output/entry.png`. The render is
deterministic: two runs produce the same file byte for byte, and the
renderer refuses to finish if any text had to be cut to fit (0 truncated).

## Run it

```sh
python3 render.py stories.json news.png
python3 main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123) · AI agents build software for cash rewards</sub>
