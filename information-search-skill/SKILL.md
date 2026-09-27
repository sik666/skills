---
name: information-search-skill
description: Research workflow for collecting and synthesizing information across primary literature, official documentation, open-source repositories, Chinese community platforms, foreign forums, and technical media. Use when Codex needs to investigate a topic, verify the current landscape, find papers/projects/articles across sources such as OSDI/NSDI/SOSP/ASPLOS/EuroSys/FAST/ISCA/MICRO/HPCA/SIGCOMM/USENIX, GitHub, Zhihu, WeChat, Xiaohongshu, Reddit, Hacker News, or major tech media, and produce a source-backed survey instead of a single quick lookup.
---

# Information Search Skill

Use this skill to do broad but disciplined topic research. Start from primary sources, then widen to code, products, and community discussion. Keep facts, inferences, and community signals clearly separated.

## Workflow

1. Classify the request.
   - If the topic is fast-moving, deployment-oriented, product-oriented, legal, medical, financial, or asks for "current/latest", always verify with current web sources.
   - If the topic is academic or technical, start with primary sources before reading commentary.

2. Build the first-pass source stack.
   - Read [references/source-map.md](references/source-map.md) for source priorities, trust levels, and platform-specific cautions.
   - Read [references/venues-and-queries.md](references/venues-and-queries.md) when the topic involves papers, systems work, architecture, or the user names specific conferences or Chinese platforms.
   - Use `scripts/build_queries.py` to generate bilingual query seeds when the topic is broad or the user wants coverage across many platforms.

3. Search in this order unless the user explicitly asks otherwise.
   - Primary literature: official venue pages, arXiv, OpenReview, ACM, IEEE, USENIX.
   - Official implementation sources: GitHub, product docs, Android/iOS/vendor docs, project websites.
   - Technical media and engineering blogs: InfoQ, 36Kr, company engineering blogs, developer portals.
   - Community and opinion sources: Zhihu, WeChat articles, Xiaohongshu, Reddit, Hacker News, independent blogs.

4. Read selectively.
   - Prefer official abstracts, paper PDFs, README/install docs, release notes, and benchmark pages.
   - On community platforms, treat popularity as signal, not proof.
   - If a claim appears only on community or media sources, label it as unverified unless corroborated elsewhere.

5. Synthesize with explicit labels.
   - `Verified fact`: supported by primary or official sources.
   - `Inference`: reasoned conclusion from multiple sources.
   - `Community signal`: recurring viewpoint from social/community platforms.
   - `Gap`: important unknowns or weak evidence.

## Output Standard

For broad research, default to this structure:

1. `Current state`
2. `Representative papers / projects / products`
3. `What is actually deployed today`
4. `Open problems or missing pieces`
5. `Sources`

When the user asks for recommendations, call out:
- what is research-only
- what is demo/prototype
- what is production-ready
- what depends on privileged access, OEM integration, or private preview APIs

## Source Discipline

- Prefer direct links to the source you actually used.
- Use exact dates when "latest", "today", or "current" matters.
- Avoid over-quoting. Summarize in your own words.
- If a platform is hard to index from the web, say so and use the best available path rather than pretending the evidence is complete.
- Do not let secondary articles outrank paper PDFs, official docs, or source code for technical claims.

## Practical Rules For Platform Coverage

- For papers and systems topics, always search both English and Chinese terms.
- For open-source deployment status, always pair papers with GitHub or official docs.
- For Chinese community coverage, include Zhihu and WeChat article search even if recall is imperfect.
- For user-perceived product state, include at least one community/forum source and one official or technical source.
- For mobile and agent topics, distinguish:
  - benchmark/academic prototype
  - PC-side controller for a phone
  - phone-native runtime
  - OEM/system-integrated assistant

## Quick Use

Example:

```bash
python3 scripts/build_queries.py "端侧 agent 部署" --topic-en "on-device agent deployment" --preset mobile-agent
```

Then search the highest-signal queries first and prune duplicates.
