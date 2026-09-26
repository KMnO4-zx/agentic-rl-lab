# SEO release and review record

## Scope

- Chinese: https://kmno4-zx.github.io/agentic-rl-lab/
- English: https://kmno4-zx.github.io/agentic-rl-lab/en/
- Sitemap: https://kmno4-zx.github.io/agentic-rl-lab/sitemap.xml
- Publication date: 2026-09-26
- First trend review: 2026-10-24 (28 days after publication)

Each language contains the homepage, experiment catalog, four guides, 14 articles and 11 quick starts. English notes preserve original experiment code, equations and figures. Translation source hashes make content drift a build failure rather than silently publishing stale translations.

## Engineering acceptance

Run `npm run docs:build` and `npm run docs:check`, then verify the completed GitHub Pages deployment. The checker covers both search indexes, all internal links and anchors, locale counterparts, unique titles and descriptions, canonical URLs, structured data and complete sitemap coverage. Check the live site after deployment, including language switching, mobile navigation, filtering and both languages' search results.

Google and Bing verification tags are intentionally public and remain in the shared site configuration. They are not API credentials. The project is hosted below `/agentic-rl-lab/`; a `robots.txt` placed here would not control the host. No artificial crawler restrictions are added.

## Baseline and follow-up

Search performance has not been measured before site verification. Missing historical data must be recorded as unavailable, not as zero.

Use Google Search Console and Bing Webmaster Tools to record the following separately for Chinese and English URLs:

| Metric | Launch baseline | 28-day review |
| --- | --- | --- |
| Sitemap processing status | Record after submission | Check errors and coverage |
| Indexed pages and exclusion reasons | Await search engine processing | Record count and reasons |
| Search impressions | Unavailable before verification | Last 28 days |
| Search clicks and click-through rate | Unavailable before verification | Last 28 days |
| Non-brand queries | Unavailable before verification | Query, landing page, impressions, clicks |
| Country and device | Unavailable before verification | Segment useful traffic |

Start with GRPO, GSPO, DAPO, ALFWorld and the learning path. Evaluate query-page fit before changing titles. Add substantive missing explanations when actual queries expose a gap. Treat rankings as noisy observations; publishing a sitemap or passing an audit does not guarantee indexing or traffic.

For public sharing, link to the relevant article or quick start. Repository README links provide persistent entry points. Social posts and community messages should be written around actual experiments when there is a concrete result to share.
