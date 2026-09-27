#!/usr/bin/env python3
"""Generate cross-platform research queries for a topic."""

from __future__ import annotations

import argparse


PRESETS = {
    "general": {
        "en": [],
        "zh": [],
    },
    "mobile-agent": {
        "en": [
            "mobile agent",
            "smartphone agent",
            "Android agent",
            "GUI agent",
            "on-device agent",
        ],
        "zh": [
            "端侧 agent",
            "手机智能体",
            "安卓智能体",
            "手机 GUI agent",
        ],
    },
    "systems": {
        "en": [
            "systems",
            "kernel",
            "benchmark",
            "deployment",
        ],
        "zh": [
            "系统",
            "内核",
            "部署",
            "性能",
        ],
    },
}


ACADEMIC_DOMAINS = [
    "usenix.org",
    "dl.acm.org",
    "ieeexplore.ieee.org",
    "openreview.net",
    "arxiv.org",
]

CN_DOMAINS = [
    "zhihu.com/question",
    "zhuanlan.zhihu.com",
    "mp.weixin.qq.com",
    "xiaohongshu.com",
    "infoq.cn",
    "36kr.com",
    "cloud.tencent.com",
]

FORUM_DOMAINS = [
    "reddit.com",
    "news.ycombinator.com",
    "theverge.com",
    "techcrunch.com",
    "venturebeat.com",
]


def dedupe(items: list[str]) -> list[str]:
    seen = set()
    out = []
    for item in items:
        if item not in seen:
            out.append(item)
            seen.add(item)
    return out


def expand_topic(base: str, extras: list[str]) -> list[str]:
    if not base:
        return []
    lowered = base.lower()
    items = [base]
    for extra in extras:
        if extra.lower() in lowered:
            continue
        items.append(f"{base} {extra}")
    return dedupe(items)


def make_queries(topic: str, topic_en: str, preset: str) -> dict[str, list[str]]:
    extra_en = PRESETS[preset]["en"]
    extra_zh = PRESETS[preset]["zh"]

    en_terms = expand_topic(topic_en, extra_en)
    zh_terms = expand_topic(topic, extra_zh)

    academic = []
    for term in dedupe(en_terms + [f"{t} paper" for t in en_terms]):
        academic.append(term)
        for domain in ACADEMIC_DOMAINS:
            academic.append(f"site:{domain} {term}")

    official = []
    base_official_terms = dedupe(en_terms + zh_terms)
    for term in base_official_terms:
        official.extend(
            [
                f"{term} GitHub",
                f"{term} official docs",
                f"{term} install",
                f"{term} deployment",
                f"{term} benchmark",
            ]
        )

    cn = []
    for term in zh_terms:
        for domain in CN_DOMAINS:
            cn.append(f"site:{domain} {term}")
        cn.append(f"搜狗 微信 {term}")

    forum = []
    for term in en_terms:
        for domain in FORUM_DOMAINS:
            forum.append(f"site:{domain} {term}")

    return {
        "academic": dedupe(academic),
        "official": dedupe(official),
        "cn-community": dedupe(cn),
        "forums-media": dedupe(forum),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate research queries for a topic.")
    parser.add_argument("topic", help="Primary topic, usually in Chinese if relevant")
    parser.add_argument(
        "--topic-en",
        default="",
        help="English form of the topic for English-language search",
    )
    parser.add_argument(
        "--preset",
        choices=sorted(PRESETS),
        default="general",
        help="Add domain-specific search expansions",
    )
    args = parser.parse_args()

    queries = make_queries(args.topic, args.topic_en.strip(), args.preset)

    for section, items in queries.items():
        print(f"[{section}]")
        for item in items:
            print(item)
        print()


if __name__ == "__main__":
    main()
