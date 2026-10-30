---
name: fix-codex-invalid-encrypted-reasoning
description: Diagnose and repair Codex session resumes that fail with /responses HTTP 400 "invalid encrypted reasoning", while preserving paginated rollout byte offsets.
---

# 修复 Codex 会话的 invalid encrypted reasoning

适用于旧会话续聊收到 `CC Switch ... /responses ... HTTP 400 ... invalid encrypted reasoning`，而新会话能正常回答的情况。这个报错来自上游对重放的加密推理内容的校验；**JSONL 能解析并不代表其中的 `encrypted_content` 能被当前上游接受**。模型系列或服务端状态变化都可能影响兼容性，不能仅凭报错断言密钥变化或文件格式损坏。[OpenAI Docs](https://developers.openai.com/api/docs/guides/reasoning#preserve-reasoning-across-calls)说明加密推理是 opaque 的跨轮状态，兼容性受模型系列限制。

## 定位与确认

1. 从截图时间、标题和 `~/.codex/session_index.jsonl` 确认 thread ID；再核对 `~/.codex/state_5.sqlite` 的 `threads.rollout_path`、相关 JSONL 的 `session_meta`、fork 来源与失败事件。标题或最近路径可能只指向最后一个片段，不能据此直接修改该文件。限制搜索范围，避免把整份会话中的凭据或用户消息打印出来。
2. 检查目标 JSONL 全行可解析、失败确实是上游 `invalid encrypted reasoning`，并定位最近一次 `compacted` 之后的 `response_item` / `reasoning` / `encrypted_content`。如果报错不同或没有这类记录，先继续诊断。
3. 用 `codex exec fork --ephemeral --skip-git-repo-check --json -m MODEL THREAD_ID '诊断测试：只回复 OK，不调用工具。'` 复现。`--ephemeral` 避免把测试轮次写入用户会话；此操作仍会向当前 provider 发一次请求。如果复现失败原因不同，不要执行下面的替换。

## 修复与验证

分页历史可能通过**字节偏移**引用旧 rollout。直接删行或缩短 JSONL 会使后续分叉报 `cutoff byte offset is past the source rollout`。先备份准确的源文件，再用 [scripts/repair_rollout.py](scripts/repair_rollout.py) 对**最近一次 compaction 之后**的加密推理记录做等长替换。只修改已经停止追加的历史片段；如果目标正被写入，先关闭该会话。脚本默认只预览；`--apply` 必须指定私有备份目录。它保留每行长度、文件总长度、时间戳和 ordinal，把不可见的推理记录替换成空的 commentary 事件；用户和助手的正文及其他记录不变。此替换已在 Codex `0.162.0-alpha.17.2` 的该类会话验证过；其他版本仍须按结果验证。

```bash
python3 scripts/repair_rollout.py /path/to/affected-rollout.jsonl
python3 scripts/repair_rollout.py /path/to/affected-rollout.jsonl \
  --apply --backup-dir /path/to/private-backup-directory
```

再次运行相同的 ephemeral fork 测试。若仍报错，先从备份恢复该文件，再检查实际重放范围，包括 compaction 和 fork lineage；不要盲目清理祖先会话或多个文件。验证正文未变、JSONL 全行有效、每行及总字节数不变，并报告备份位置和被替换条数。原会话被 VS Code 持有 active writer 时，命令行 `resume` 不能直接验证；让用户关闭旧标签页并从历史重新打开，才能载入磁盘修复结果。
