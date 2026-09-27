# 修复 VS Code Remote SSH `AsyncPipeFailed` 连接失败

Last updated: 2026-05-15

## 适用场景

VS Code 通过 Remote SSH 连接某个 Linux 用户失败，但同一台机器上的其它用户可以正常连接。

典型报错：

```text
无法获取远程环境
无法连接到远程扩展主机服务器
CodeError(AsyncPipeFailed(Os { code: 2, kind: NotFound, message: "No such file or directory" }))
```

本次现场情况：

- 连接 `haodong` 用户失败
- 当前 `xuke` 用户的 VS Code SSH 连接正常
- `haodong` 的旧 VS Code server 进程仍在
- 旧 server 绑定的 `/tmp/code-...` Unix socket 已经不存在

## 核心原因

VS Code Remote SSH 在远端用户目录下启动一个 server，并通过 `/tmp/code-...` 这类 Unix socket 和它通信。

如果出现下面这种不一致状态：

- 远端用户的 VS Code server 进程还活着
- 进程参数里记录的 `--socket-path=/tmp/code-...`
- 但这个 socket 文件已经被删除或消失

那么本地 VS Code 可能会尝试复用这个“半活”的旧 server，最终连接 socket 时失败，于是报：

```text
AsyncPipeFailed
No such file or directory
```

这不是工程代码问题，也不是普通 SSH 登录一定有问题，而是 VS Code Remote server 的运行时状态坏了。

## 关键路径

远端 VS Code server 目录：

```text
/home/<user>/.vscode-server
```

常见 server 安装目录：

```text
/home/<user>/.vscode-server/cli/servers/Stable-<commit>/
```

常见日志目录：

```text
/home/<user>/.vscode-server/data/logs/
```

常见 CLI 日志：

```text
/home/<user>/.vscode-server/.cli.<commit>.log
/home/<user>/.vscode-server/cli/servers/Stable-<commit>/log.txt
```

常见 socket 路径：

```text
/tmp/code-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

## 排查命令

把 `<user>` 替换成出问题的远端用户，例如 `haodong`。

### 1. 看 VS Code server 进程

```bash
ps -eo pid,user,ppid,stat,lstart,cmd \
  | rg -i '<user>|\.vscode-server|code-server|server-main|command-shell'
```

重点看是否存在类似进程：

```text
sh /home/<user>/.vscode-server/.../server/bin/code-server ... --socket-path=/tmp/code-...
node /home/<user>/.vscode-server/.../server/out/server-main.js ... --socket-path=/tmp/code-...
/home/<user>/.vscode-server/code-<commit> command-shell ...
```

### 2. 检查进程里的 socket 是否真实存在

从进程参数里复制 `--socket-path` 后检查：

```bash
ls -l /tmp/code-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

如果返回：

```text
没有那个文件或目录
```

同时 VS Code server 进程还活着，就很符合本问题。

也可以列出当前所有 VS Code socket：

```bash
ls -l /tmp/code-* 2>&1
```

正常连接中的用户通常会有自己的 socket，例如：

```text
srwxrwxr-x 1 xuke xuke 0 ... /tmp/code-2f8b8fee-...
```

### 3. 看日志里的相关错误

```bash
find /home/<user>/.vscode-server/data/logs -maxdepth 2 -type f \
  \( -name 'remoteagent.log' -o -name 'ptyhost.log' \) -print0 \
  | xargs -0 rg -n 'AsyncPipeFailed|No such file|Unexpected SIGPIPE|Could not find pty|No ptyHost heartbeat|not compatible'
```

本次看到过的相关日志包括：

```text
Unexpected SIGPIPE
No ptyHost heartbeat
Could not find pty ... on pty host
```

这些日志说明远端 VS Code server 或 ptyHost 曾经异常断连。真正触发本次无法连接的是旧 server 进程还在，但 socket 已经不存在。

## 最小修复

只杀掉出问题用户的 VS Code Remote server 残留进程，不动工程文件。

```bash
sudo pkill -TERM -u <user> -f '/home/<user>/.vscode-server' || true
sudo pkill -TERM -u <user> -f 'command-shell --cli-data-dir /home/<user>/.vscode-server/cli' || true
```

如果没有 sudo，但可以登录到该用户本身，直接以该用户执行：

```bash
pkill -TERM -f "$HOME/.vscode-server" || true
pkill -TERM -f "command-shell --cli-data-dir $HOME/.vscode-server/cli" || true
```

等 1 秒后复查：

```bash
ps -eo pid,user,ppid,stat,lstart,cmd \
  | rg -i '<user>.*(\.vscode-server|code-server|server-main|command-shell|sleep 180)' || true
```

期望结果：没有该用户的 `.vscode-server`、`code-server`、`server-main`、`command-shell` 进程。

## 清理失败重试残留

VS Code Remote SSH 失败重试时，可能留下短命的 `sshd: <user>@notty`、`sh`、`sleep 180`。

如果确认这些是刚才 VS Code 失败连接留下的，可以清理：

```bash
sudo pkill -TERM -u <user> -f '^sleep 180$' || true
```

如果还有明显的 `sshd: <user>@notty` 失败连接残留，可以按 PID 精确杀掉：

```bash
sudo kill -TERM <pid1> <pid2> <pid3>
```

不要粗暴杀该用户所有进程，因为可能会影响对方桌面会话、后台任务或正在跑的训练/编译任务。

## 清理旧 pid 文件

如果对应版本目录里有旧的 `pid.txt`，可以删掉，避免下一次启动时被旧状态误导。

先找到最新版本目录：

```bash
find /home/<user>/.vscode-server/cli/servers -maxdepth 2 -type f \
  \( -name 'pid.txt' -o -name 'log.txt' \) \
  -printf '%TY-%Tm-%Td %TH:%TM %p\n' \
  | sort -r
```

删除出问题版本的 `pid.txt`：

```bash
sudo rm -f /home/<user>/.vscode-server/cli/servers/Stable-<commit>/pid.txt
```

本次处理过的例子：

```bash
sudo rm -f /home/haodong/.vscode-server/cli/servers/Stable-0958016b2af9f09bb4257e0df4a95e2f90590f9f/pid.txt
```

## 更重的修复：重装当前 VS Code server 缓存

如果杀掉残留进程后仍然连不上，可以删除当前 VS Code commit 对应的 server 缓存，让 VS Code 下次 SSH 连接时自动重装。

```bash
sudo rm -rf /home/<user>/.vscode-server/cli/servers/Stable-<commit>
sudo rm -f /home/<user>/.vscode-server/code-<commit>
```

本次对应例子：

```bash
sudo rm -rf /home/haodong/.vscode-server/cli/servers/Stable-0958016b2af9f09bb4257e0df4a95e2f90590f9f
sudo rm -f /home/haodong/.vscode-server/code-0958016b2af9f09bb4257e0df4a95e2f90590f9f
```

一般先不要删整个 `/home/<user>/.vscode-server`，因为里面还有扩展、用户数据、缓存。除非明确要彻底重置 VS Code 远端环境。

## 本次修复记录

时间：2026-05-15

故障用户：

```text
haodong
```

正常用户：

```text
xuke
```

发现的坏状态：

```text
haodong 旧 server 进程仍在：
/home/haodong/.vscode-server/cli/servers/Stable-0958016b2af9f09bb4257e0df4a95e2f90590f9f/...
--socket-path=/tmp/code-62efb24e-2d23-4d9c-b0c7-8fa55650aa50

但 socket 文件不存在：
/tmp/code-62efb24e-2d23-4d9c-b0c7-8fa55650aa50: No such file or directory
```

执行的修复：

```bash
sudo pkill -TERM -u haodong -f '/home/haodong/.vscode-server' || true
sudo pkill -TERM -u haodong -f 'command-shell --cli-data-dir /home/haodong/.vscode-server/cli' || true
sudo pkill -TERM -u haodong -f '^sleep 180$' || true
sudo rm -f /home/haodong/.vscode-server/cli/servers/Stable-0958016b2af9f09bb4257e0df4a95e2f90590f9f/pid.txt
```

结果：

```text
haodong 的 VS Code SSH 连接恢复正常。
```

## 判断是否已修好

重新用 VS Code SSH 连接该用户后：

1. VS Code 不再报 `AsyncPipeFailed`
2. `ps` 能看到该用户新的 `code-server` / `server-main.js`
3. `/tmp/code-...` 里存在新的 socket
4. 远端窗口能正常打开终端、扩展主机不再报无法连接

复查命令：

```bash
ps -eo pid,user,ppid,stat,lstart,cmd \
  | rg -i '<user>.*(\.vscode-server|code-server|server-main|command-shell)'

ls -l /tmp/code-* 2>&1
```

