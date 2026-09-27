# Venues And Query Patterns

Use this file when the user asks for systematic coverage across conferences, code platforms, Chinese platforms, or foreign forums.

## Systems And Architecture Venue List

Start from these when the topic touches operating systems, distributed systems, computer architecture, storage, databases, compilers, or performance:

- OSDI
- NSDI
- SOSP
- ASPLOS
- EuroSys
- FAST
- ATC / USENIX ATC
- DAC
- ISCA
- MICRO
- HPCA
- SIGMOD
- SIGCOMM
- PPoPP
- SC
- TACO
- TCAD

## Topic Families

### Mobile / Device Agent

Search with combinations of:
- mobile agent
- smartphone agent
- GUI agent
- Android agent
- on-device agent
- phone-native agent
- mobile automation agent
- multimodal agent smartphone
- app control agent

Chinese expansions:
- 端侧 agent
- 手机智能体
- 安卓智能体
- 手机 GUI agent
- 端侧大模型智能体
- 手机自动化智能体

### Systems / Kernel / Memory

Search with combinations of:
- Linux memory
- MGLRU
- reclaim
- prepaging
- working set
- anonymous page
- file-backed page
- Android memory management

Chinese expansions:
- Linux 冷热页
- 安卓内存管理
- MGLRU
- 页回收
- 预热
- 工作集

## Platform Query Patterns

### Primary Literature

Use plain queries plus venue/domain filters:

- `<topic> paper`
- `<topic> arXiv`
- `<topic> OpenReview`
- `<topic> site:usenix.org`
- `<topic> site:dl.acm.org`
- `<topic> site:ieeexplore.ieee.org`

### Open Source / Product

- `<topic> GitHub`
- `<topic> Android app`
- `<topic> deployment`
- `<topic> install`
- `<topic> release`
- `<topic> benchmark`

### Chinese Platforms

- `site:zhihu.com/question <topic-cn>`
- `site:zhuanlan.zhihu.com <topic-cn>`
- `site:mp.weixin.qq.com <topic-cn>`
- `搜狗 微信 <topic-cn>`
- `site:xiaohongshu.com <topic-cn>`
- `site:infoq.cn <topic-cn>`
- `site:36kr.com <topic-cn>`
- `site:cloud.tencent.com <topic-cn>`

### Foreign Forums / Media

- `site:reddit.com <topic-en>`
- `site:news.ycombinator.com <topic-en>`
- `site:theverge.com <topic-en>`
- `site:techcrunch.com <topic-en>`
- `site:arstechnica.com <topic-en>`
- `site:venturebeat.com <topic-en>`

## Search Sequence

For each topic, run this sequence:

1. Broad query in English
2. Broad query in Chinese
3. Domain-filtered academic query
4. GitHub / official-doc query
5. Chinese community query
6. Foreign forum query

Stop expanding when new results are no longer adding unique facts.

## What To Extract

From each result, extract:

- source type
- publication date
- concrete claim
- evidence strength
- install/deployment requirements
- whether it is research, prototype, or production
