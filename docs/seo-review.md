# SEO release and review record

## Scope

- Chinese: https://kmno4-zx.github.io/agentic-rl-lab/
- English: https://kmno4-zx.github.io/agentic-rl-lab/en/
- Sitemap: https://kmno4-zx.github.io/agentic-rl-lab/sitemap.xml
- Publication date: 2026-09-26
- First processing check: 2026-09-28
- First trend review: 2026-10-24 (28 days after publication)

Each language contains the homepage, experiment catalog, four guides, 14 articles and 11 quick starts. English notes preserve original experiment code, equations and figures. Translation source hashes make content drift a build failure rather than silently publishing stale translations.

## Engineering acceptance

Run `npm run docs:build` and `npm run docs:check`, then verify the completed GitHub Pages deployment. The checker covers both search indexes, all internal links and anchors, locale counterparts, unique titles and descriptions, canonical URLs, structured data and complete sitemap coverage. Check the live site after deployment, including language switching, mobile navigation, filtering and both languages' search results.

Google and Bing verification tags are intentionally public and remain in the shared site configuration. They are not API credentials. The project is hosted below `/agentic-rl-lab/`; a `robots.txt` placed here would not control the host. No artificial crawler restrictions are added.

## Launch verification, 2026-09-26

- The [bilingual Pages deployment](https://github.com/KMnO4-zx/agentic-rl-lab/actions/runs/36214428591) completed successfully. The default branch received the [Chinese and English README entry points](https://github.com/KMnO4-zx/agentic-rl-lab/commit/6f919b6b228c13f10498c37e879cc9dd9be6b022).
- Build checks passed for 63 HTML files (62 indexable pages plus the 404), 4,379 internal links/assets and 826 searchable sections. Every sitemap URL has a canonical page, a language counterpart and a last-modified date.
- A live HTTP audit verified all 62 public URLs, their language and canonical metadata, the sitemap, primary CSS/JavaScript and social card. Missing pages return HTTP 404.
- Browser checks passed for desktop and mobile layouts, article language switching, Chinese and English search, topic/keyword filtering, reset behavior and edit links. The checked production browser session reported zero errors and zero warnings.
- Local Lighthouse 13.5.0 mobile audits measured the following. These are lab measurements, not real-user Core Web Vitals or search rankings. Large original experiment figures remain available at full resolution and load lazily.

| Page | Performance | Accessibility | Best practices | SEO |
| --- | ---: | ---: | ---: | ---: |
| English homepage | 97 | 100 | 100 | 100 |
| English GRPO article | 95 | 100 | 100 | 100 |

## Search engine setup

- **Google:** URL-prefix ownership verified through the deployed HTML meta tag. The sitemap submission was accepted. Its initial report showed `Couldn't fetch`; a live Google URL inspection then confirmed `Crawl allowed: Yes` and `Page fetch: Successful` at 11:22 Asia/Shanghai. The sitemap was resubmitted. Check the report again after processing; do not treat submission acceptance as successful sitemap processing or indexing.
- **Bing:** ownership verified. The sitemap was accepted and showed `Processing`, with no reported errors or warnings at that point. All 62 Chinese/English URLs were also accepted through URL Submission; the dashboard showed 62 submitted URLs at 11:25 Asia/Shanghai.
- **Baidu:** pending the owner's profile completion, phone/email verification and platform declaration. No identity information or verification codes were filled on the owner's behalf.

Google's performance/indexing reports were still preparing data; Bing reported that initial reports may take up to 48 hours. The Chinese homepage was not yet indexed in Google's launch inspection. This is a new-site baseline, not a count of indexed pages across the whole site.

If Google's sitemap report continues to show a fetch error, follow its [sitemap troubleshooting instructions](https://support.google.com/webmasters/answer/7451001?hl=en): inspect the exact URL, confirm live fetch and robots access, then check for a persistent server or processing issue. Avoid repeatedly resubmitting an unchanged sitemap once processing succeeds.

## Baseline and follow-up

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
