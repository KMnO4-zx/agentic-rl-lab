# SEO release and review record

## Scope

- Chinese: https://kmno4-zx.github.io/agentic-rl-lab/
- English: https://kmno4-zx.github.io/agentic-rl-lab/en/
- Sitemap: https://kmno4-zx.github.io/agentic-rl-lab/sitemap.xml
- Publication date: 2026-09-26
- First processing check: 2026-09-28
- First trend review: 2026-10-24 (28 days after publication)

Each language contains the homepage, experiment catalog, six guides, 14 articles and 11 quick starts: 66 indexable pages in total after the brand-topic expansion below. English notes preserve original experiment code, equations and figures. Translation source hashes make content drift a build failure rather than silently publishing stale translations.

## Engineering acceptance

Run `npm run docs:build` and `npm run docs:check`, then verify the completed GitHub Pages deployment. The checker covers both search indexes, all internal links and anchors, locale counterparts, unique titles and descriptions, canonical URLs, structured data and complete sitemap coverage. Check the live site after deployment, including language switching, mobile navigation, filtering and both languages' search results.

Google and Bing verification tags are intentionally public and remain in the shared site configuration. They are not API credentials. The project is hosted below `/agentic-rl-lab/`; a `robots.txt` placed here would not control the host. No artificial crawler restrictions are added.

## Launch verification, 2026-09-26

- The [bilingual Pages deployment](https://github.com/KMnO4-zx/agentic-rl-lab/actions/runs/36214428591) and the [code-contrast update](https://github.com/KMnO4-zx/agentic-rl-lab/actions/runs/36214798350) completed successfully. The default branch received the [Chinese and English README entry points](https://github.com/KMnO4-zx/agentic-rl-lab/commit/6f919b6b228c13f10498c37e879cc9dd9be6b022).
- Build checks passed for 63 HTML files (62 indexable pages plus the 404), 4,379 internal links/assets and 826 searchable sections. Every sitemap URL has a canonical page, a language counterpart and a last-modified date.
- A live HTTP audit verified all 62 public URLs, their language and canonical metadata, the sitemap, primary CSS/JavaScript and social card. Missing pages return HTTP 404.
- Browser checks passed for desktop and mobile layouts, article language switching, Chinese and English search, topic/keyword filtering, reset behavior and edit links. The checked production browser session reported zero errors and zero warnings.
- Local Lighthouse 13.5.0 mobile audits measured the following. These are lab measurements, not real-user Core Web Vitals or search rankings. Large original experiment figures remain available at full resolution and load lazily.

| Page | Performance | Accessibility | Best practices | SEO |
| --- | ---: | ---: | ---: | ---: |
| English homepage | 97 | 100 | 100 | 100 |
| English GRPO article | 95 | 100 | 100 | 100 |

## Search engine setup

- **Google:** URL-prefix ownership verified through the deployed HTML meta tag. The sitemap submission was accepted. Its report showed `Couldn't fetch`; a live Google URL inspection then confirmed `Crawl allowed: Yes` and `Page fetch: Successful` at 11:22 Asia/Shanghai. The sitemap was resubmitted, but the final report still showed the fetch error. Separate indexing requests for the Chinese and English homepages both succeeded, with Search Console confirming their addition to the priority crawl queue. Check the sitemap report again after processing; do not treat submission acceptance as successful sitemap processing or indexing.
- **Bing:** ownership verified. The sitemap was accepted and showed `Processing`, with no reported errors or warnings at that point. All 62 Chinese/English URLs were also accepted through URL Submission; the dashboard showed 62 submitted URLs at 11:25 Asia/Shanghai.
- **Baidu:** deferred at the owner's request; this release completes Google/Bing setup first. A later connection requires profile completion, phone/email verification and the platform declaration. No identity information or verification codes were filled on the owner's behalf.

Google's performance/indexing reports were still preparing data; Bing reported that initial reports may take up to 48 hours. Both homepages were not yet indexed in Google's launch inspections, before the accepted indexing requests. This is a new-site baseline, not a count of indexed pages across the whole site.

If Google's sitemap report continues to show a fetch error, follow its [sitemap troubleshooting instructions](https://support.google.com/webmasters/answer/7451001?hl=en): inspect the exact URL, confirm live fetch and robots access, then check for a persistent server or processing issue. Avoid repeatedly resubmitting an unchanged sitemap once processing succeeds.

## Baseline and follow-up

### PyTRIO and Tinker topic expansion, 2026-09-26

Two new guides in both languages connect brand-related searches to useful material:

| Topic | Chinese / English landing pages | Query examples to monitor |
| --- | --- | --- |
| PyTRIO tutorials | [/guide/pytrio.html](https://kmno4-zx.github.io/agentic-rl-lab/guide/pytrio.html) / [/en/guide/pytrio.html](https://kmno4-zx.github.io/agentic-rl-lab/en/guide/pytrio.html) | `pytrio`, `pytrio 教程`, `pytrio grpo`, `pytrio reinforcement learning` |
| Tinker and PyTRIO workflows | [/guide/tinker-pytrio.html](https://kmno4-zx.github.io/agentic-rl-lab/guide/tinker-pytrio.html) / [/en/guide/tinker-pytrio.html](https://kmno4-zx.github.io/agentic-rl-lab/en/guide/tinker-pytrio.html) | `tinker`, `tinker 强化学习`, `tinker pytrio`, `tinker vs pytrio` |

The homepage, sidebar, setup guide and related-reading links lead to the new guides. Homepage, setup and GRPO titles now describe their actual PyTRIO content explicitly. The Tinker guide compares documented concepts with this repository's PyTRIO implementation; it does not claim a validated Tinker port, SDK compatibility or performance comparisons.

The expanded build passed checks for 67 HTML files, 4,859 internal links/assets and 852 searchable sections, with all 66 indexable URLs in the sitemap. Browser checks verified the new homepage links, Chinese/English switching with updated canonical metadata, English Tinker search results and mobile layouts without horizontal overflow or JavaScript page errors. These are engineering checks, not evidence of search visibility. The launch checks above retain the original 62-page baseline.

During the 28-day review, separate exact brand queries (`pytrio`, `tinker`) from queries containing a task or comparison. Record impressions, clicks, landing page and indexing status for each language. New query data is currently unavailable; no rank or traffic improvement has been measured. The first experiment is whether relevant queries begin producing impressions for these pages, not a promised position for a bare brand name.

The content approach follows Google's guidance on [helpful original content](https://developers.google.com/search/docs/fundamentals/creating-helpful-content) and [descriptive page titles](https://developers.google.com/search/docs/appearance/title-link). Keep explanations tied to code and real experiments when expanding these topics.

### Site-wide measurements

Search performance has not been measured before site verification. Missing historical data must be recorded as unavailable, not as zero.

Use Google Search Console and Bing Webmaster Tools to record the following separately for Chinese and English URLs:

| Metric | Launch baseline | 28-day review |
| --- | --- | --- |
| Sitemap processing status | Google fetch report pending resolution; Bing processing | Check errors and coverage |
| Indexed pages and exclusion reasons | Await search engine processing | Record count and reasons |
| Search impressions | Unavailable before verification | Last 28 days |
| Search clicks and click-through rate | Unavailable before verification | Last 28 days |
| Non-brand queries | Unavailable before verification | Query, landing page, impressions, clicks |
| Country and device | Unavailable before verification | Segment useful traffic |

Start with GRPO, GSPO, DAPO, ALFWorld and the learning path. Evaluate query-page fit before changing titles. Add substantive missing explanations when actual queries expose a gap. Treat rankings as noisy observations; publishing a sitemap or passing an audit does not guarantee indexing or traffic.

The review dates are a maintenance plan; no automatic reminder or unattended follow-up job has been created.

For public sharing, link to the relevant article or quick start. Repository README links provide persistent entry points. Social posts and community messages should be written around actual experiments when there is a concrete result to share.
