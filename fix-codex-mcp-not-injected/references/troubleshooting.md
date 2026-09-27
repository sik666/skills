# 修复 Codex MCP 服务已启用但当前会话未注入

## 适用场景

适用于下面这类情况：

- VS Code 的 MCP 面板里已经看到某个 MCP 服务器是启用状态
- 但当前 Codex 会话里拿不到这个 MCP 的工具
- UI 看起来正常，实际调用不到
- 同时伴随 `listen EACCES`、`npx not found`、`server enabled but unusable` 之类问题

这次排查对象是：

- MCP 服务：`drawio`
- 启动命令：`npx @next-ai-drawio/mcp-server@latest`

## 关键结论

“MCP 服务在 UI 里显示为已启用”只说明：

- 配置项已经注册成功
- 开关状态是启用

它**不说明**：

- MCP 服务器进程已经成功启动
- VS Code 里的 Codex app-server / MCP 桥接已经正常
- 当前这一次会话已经动态拿到了新工具

## 这次实际遇到的 3 个问题

### 1. MCP 配置已注册，但启动命令起不来

检查命令：

```bash
codex mcp get drawio
codex mcp list
```

当时配置是：

```text
command: npx
args: @next-ai-drawio/mcp-server@latest
```

但实际系统里没有 `npx`：

```bash
command -v node
command -v npm
command -v npx
```

当时状态是：

- 有 `node`
- 没有 `npm`
- 没有 `npx`
- `node` 版本还是旧的 `v12.22.9`

直接验证：

```bash
timeout 12s npx @next-ai-drawio/mcp-server@latest
```

报错：

```text
timeout: failed to run command ‘npx’: No such file or directory
```

### 2. Codex 扩展自己的 IPC 桥接目录权限错了

Codex 扩展日志报：

```text
listen EACCES: permission denied /tmp/codex-ipc/ipc-1000.sock
```

检查：

```bash
ls -ld /tmp/codex-ipc
stat -c '%A %a %U:%G %n' /tmp/codex-ipc
```

当时状态是：

- `/tmp/codex-ipc` 属主是 `xuke:xuke`
- 当前用户是 `haodong`
- 权限是 `775`

这意味着 `haodong` 无法在这里正常创建自己的 Codex IPC socket。

### 3. 即使前两项修好，当前会话也不一定动态拿到新工具

这是最容易误判的一点：

- MCP 服务是会话外配置
- 工具注入通常发生在会话初始化阶段
- 你在会话已经开始之后再修环境、再启用 MCP，当前这次会话不一定热更新出工具

所以：

- 服务启用成功 != 当前对话已经可调用该工具

## 这次的修复方法

### 1. 清掉错误属主的 `/tmp/codex-ipc`

最直接做法：

```bash
sudo rm -rf /tmp/codex-ipc
```

删除后，让当前用户重新启动 Codex / VS Code 扩展，由它自己创建：

```text
/tmp/codex-ipc
/tmp/codex-ipc/ipc-1000.sock
```

修复后应看到：

- 属主变成当前用户
- socket 由当前用户创建

### 2. 升级 Node 并补齐 `npm` / `npx`

这台机器上有 NodeSource 源，所以最简单的是直接升级 `nodejs`：

```bash
sudo apt-get update
sudo apt-get install -y nodejs
```

安装后验证：

```bash
command -v node
command -v npm
command -v npx
node --version
npm --version
npx --version
```

这次修完后的状态是：

- `node`: `/usr/bin/node`
- `npm`: `/usr/bin/npm`
- `npx`: `/usr/bin/npx`
- `node --version`: `v20.20.2`

### 3. 直接验证 MCP 服务器能否启动

不要只看 UI 开关，要真正跑一下：

```bash
timeout 20s npx @next-ai-drawio/mcp-server@latest --help
```

或者：

```bash
timeout 20s npx @next-ai-drawio/mcp-server@latest
```

如果服务正常，会看到类似：

```text
[MCP-DrawIO] [INFO] Starting MCP server for Next AI Draw.io (embedded mode)...
[MCP-DrawIO] [INFO] MCP server running on stdio
```

### 4. 重载 VS Code / 新开 Codex 会话

当前会话如果是在修复前创建的，通常要重建会话才能拿到工具注入。

推荐动作：

1. `Developer: Reload Window`
2. 关闭当前 Codex 会话
3. 新开一个 Codex 会话
4. 再测试 MCP 工具

## 这次修复后的关键验证点

### MCP 配置仍然存在

```bash
codex mcp list
codex mcp get drawio
```

### drawio 服务器可以启动

验证成功输出应至少包含：

```text
MCP server running on stdio
```

### `/tmp/codex-ipc` 已由当前用户创建

```bash
ls -ld /tmp/codex-ipc /tmp/codex-ipc/ipc-1000.sock
stat -c '%A %a %U:%G %n' /tmp/codex-ipc /tmp/codex-ipc/ipc-1000.sock
```

修好后应看到属主变成当前用户，而不是别的用户遗留目录。

### Codex 扩展日志不再持续报 `EACCES`

看日志：

```bash
tail -n 80 ~/.vscode-server/data/logs/*/exthost*/openai.chatgpt/Codex.log
```

修复后应能看到类似：

```text
[IpcRouter] I am the router
```

这表示 Codex 的本地 IPC 路由已经恢复。

## 高价值判断标准

下面这几个判断比 UI 开关更可靠：

1. `npx` 是否真的存在
2. MCP 启动命令是否真的能跑通
3. `/tmp/codex-ipc` 是否属于当前用户
4. Codex 扩展日志里是否停止报 `listen EACCES`
5. 是否重新开了一个会话去拿新的 tool injection

## 一句话结论

看到 MCP 开关打开，只能说明“配置启用了”。  
要真正可用，至少还必须满足：

- 启动命令能执行
- Codex 本地 IPC 桥正常
- 新会话重新完成工具注入
