# Source Map

Use this file to decide where to search and how much trust to assign to each source class.

## Priority Order

1. Primary sources
   - Paper PDFs, official venue pages, arXiv, OpenReview, ACM, IEEE, USENIX
   - Official documentation, platform APIs, release notes, project websites
   - Source repositories and issue trackers

2. Secondary technical sources
   - Engineering blogs
   - Technical media such as InfoQ, 36Kr, cloud vendor blogs, company posts

3. Community sources
   - Zhihu answers and columns
   - WeChat public articles
   - Xiaohongshu notes
   - Reddit threads
   - Hacker News discussions
   - Personal blogs and newsletters

## How To Use Each Class

### Primary Sources

Use first when:
- the user asks what a paper or system actually does
- the topic is architecture, kernels, compilers, models, benchmarks, APIs, or deployment requirements
- current feature support matters

Treat as strongest evidence for:
- technical mechanisms
- evaluation setup
- supported platforms
- installation paths
- release state

### Secondary Technical Sources

Use for:
- industry framing
- market/adoption trends
- cross-project comparison
- context that official docs omit

Require back-checking when they make:
- performance claims
- launch claims
- compatibility claims
- roadmap claims

### Community Sources

Use for:
- operator pain points
- install friction
- user sentiment
- practical caveats
- which products people are actually trying

Do not use alone for:
- architecture claims
- exact feature support
- security guarantees
- deployment status that affects spending or planning

## Platform Notes

### Papers And Venues

Search official venue sites first. If the venue page is sparse, use arXiv/OpenReview to get abstract, PDF, and code links.

### GitHub

Check:
- recent commits
- release cadence
- install docs
- Android/iOS/device prerequisites
- issues around permissions, adb, root, OEM limits

### Zhihu

Good for practitioner interpretation and ecosystem overviews. Search both:
- `site:zhihu.com/question`
- `site:zhuanlan.zhihu.com`

### WeChat

Direct indexing is inconsistent. Use:
- `site:mp.weixin.qq.com`
- Sogou Weixin search terms
- titles of known media or labs

Treat article popularity as weak signal until cross-checked.

### Xiaohongshu

Useful for product-side deployment anecdotes and creator summaries. Search:
- `site:xiaohongshu.com`

Expect sparse indexing and weak technical depth.

### Reddit / Hacker News

Useful for:
- install friction
- early adoption
- benchmark skepticism
- practical tooling comparisons

Always verify any technical claim elsewhere.

## Evidence Labels

Use these labels in writeups:

- `Verified fact`
- `Inference`
- `Community signal`
- `Unverified claim`

## Fast-Moving Topics

For AI agents, mobile systems, kernels, product launches, vendor APIs, or anything tied to releases:
- prefer sources from the last 12 months
- include exact dates
- distinguish preview/beta/private access from public availability
