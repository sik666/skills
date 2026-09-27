# 文件权限问题引起的插件问题原因和解决方法

## 适用场景

适用于下面这类看起来像“插件坏了”，但本质上是用户、属主、软链接、路径或 Git 安全策略导致的开发环境问题：

- VS Code 里 Git 仓库突然识别不了
- `clangd` 插件提示未安装，或者看起来没有启动
- 明明有 `compile_commands.json`，但跳转、补全、诊断不工作
- 换一个用户 SSH 连接后，同一项目又恢复正常
- 项目通过软链接访问，实际路径和显示路径不一致

## 这次遇到的典型问题

### 1. Git 提示 dubious ownership，VS Code 识别不了仓库

典型现象：

- VS Code 源码管理面板不显示仓库状态
- 弹窗提示仓库可能不安全
- 命令行 `git status` 报：

```text
fatal: detected dubious ownership in repository at '...'
```

核心原因：

- 当前登录用户不是仓库目录或 `.git` 目录的属主
- Git 认为这个仓库属于“其他用户”，默认拒绝信任
- VS Code 内置 Git 扩展同样受这个限制

快速验证：

```bash
git -C /path/to/repo status
stat -c '%A %a %U:%G %n' /path/to/repo /path/to/repo/.git
whoami
```

解决方法：

把仓库加入当前用户的 `safe.directory`：

```bash
git config --global --add safe.directory /真实/仓库路径
```

如果你平时是通过软链接进入仓库，建议把“显示路径”和“真实路径”都加进去：

```bash
git config --global --add safe.directory /home/haodong/data/inference/proj_1/llama.cpp
git config --global --add safe.directory /mnt/data_0/xuke/from_haodong_data/inference/proj_1/llama.cpp
```

验证：

```bash
git config --global --get-all safe.directory
git -C /path/to/repo status -sb
```

## 2. `compile_commands.json` 存在，但 `clangd` 不工作

典型现象：

- 项目根目录下明明有 `compile_commands.json`
- `clangd` 无法跳转、补全、诊断不准
- 日志里出现：

```text
Failed to find compilation database for ...
ASTWorker building file ... with command clangd fallback
```

核心原因：

- `compile_commands.json` 里的 `directory`、`file`、`command` 记录的是旧的绝对路径
- 当前工作区打开的是软链接路径或另一套真实路径
- `clangd` 匹配当前文件时拿不到同一套绝对路径，于是退回 fallback 模式

这类问题经常出现在：

- 项目从一个分区迁移到另一个分区
- `/home/...` 实际软链接到 `/mnt/...`
- 构建目录是旧路径生成的

快速验证：

```bash
pwd
realpath .
realpath /path/to/repo
python3 - <<'PY'
import json
with open('/path/to/repo/compile_commands.json') as f:
    data = json.load(f)
for item in data[:5]:
    print(item.get('directory'))
    print(item.get('file'))
    print('---')
PY
```

如果当前实际工作路径是：

```text
/mnt/data_0/xuke/from_haodong_data/inference/proj_1
```

但 `compile_commands.json` 里写的是：

```text
/home/haodong/data/inference/proj_1
```

那就是典型路径错位。

解决方法：

批量替换旧前缀到当前真实路径前缀：

```bash
perl -0pi -e 's#/旧/前缀#/新/前缀#g' /path/to/repo/compile_commands.json
```

例如：

```bash
perl -0pi -e 's#/home/haodong/data/inference/proj_1#/mnt/data_0/xuke/from_haodong_data/inference/proj_1#g' \
  /home/haodong/data/inference/proj_1/llama.cpp/compile_commands.json
```

验证：

```bash
rg -n '/旧/前缀|/新/前缀' /path/to/repo/compile_commands.json | sed -n '1,20p'
```

## 3. VS Code 弹出 “The clangd language server is not installed”

典型现象：

- VS Code 右下角或通知栏提示 `clangd` 未安装
- 但服务器上其实已经装了 `/usr/bin/clangd`
- 同一台机器换另一个用户打开项目却正常

核心原因：

这类提示不一定表示系统里真的没有 `clangd`。更常见的是：

- `clangd` 扩展没有正确解析到要使用哪个二进制
- 当前工作区没有显式指定 `clangd.path`
- 当前工作区没把 `compile_commands.json` 和 `query-driver` 指清楚
- 之前 Git/路径问题导致工作区状态混乱，扩展没有正常 attach

先确认系统层面到底有没有 `clangd`：

```bash
command -v clangd
clangd --version
ls -l /usr/bin/clangd /usr/local/bin/clangd $HOME/.local/bin/clangd 2>/dev/null
```

如果这里都正常，就不要再把重点放在“是不是没安装”，而应该去看工作区配置。

推荐解决方法：

在项目根目录下添加 `.vscode/settings.json`，显式指定：

- `clangd.path`
- `clangd.arguments`
- `--compile-commands-dir`
- `--query-driver`

示例：

```json
{
  "clangd.enable": true,
  "clangd.path": "/usr/bin/clangd",
  "clangd.arguments": [
    "--background-index",
    "--compile-commands-dir=/mnt/data_0/xuke/from_haodong_data/inference/proj_1/llama.cpp",
    "--query-driver=/home/xuke/Android/Sdk/ndk/**/clang*",
    "--header-insertion=never"
  ]
}
```

如果项目是 Android NDK、交叉编译、或者特殊 toolchain，这一步尤其重要。

## 4. 父目录打开了很多嵌套仓库，插件行为异常

典型现象：

- 打开的是一个大工作区父目录
- 里面嵌套多个 `.git`
- Git、`clangd`、索引、工作区切换行为都显得不稳定

核心原因：

- 真正的仓库根在子目录
- `compile_commands.json` 也在子目录
- VS Code 打开父目录时，扩展需要在多仓库、多路径、多配置之间做选择
- 这会放大路径错位、属主不一致、工作区配置缺失的问题

建议做法：

直接把真正的仓库根作为 VS Code 打开的根目录，而不是父目录。

例如不要打开：

```text
/home/haodong/data/inference/proj_1
```

而是直接打开：

```text
/home/haodong/data/inference/proj_1/llama.cpp
```

## 推荐排查顺序

遇到“插件有问题”时，不要上来就重装插件，先按这个顺序排：

1. 当前用户是谁：`whoami`
2. 仓库和 `.git` 属主是谁：`stat`
3. Git 是否报 dubious ownership：`git status`
4. 当前打开路径和真实路径是否一致：`pwd` + `realpath`
5. `compile_commands.json` 里的绝对路径是否还是旧路径
6. 系统是否真的找得到 `clangd`：`command -v clangd`
7. VS Code 工作区是否显式指定了 `clangd.path` 和 `compile_commands`
8. 是否打开了错误的父目录，而不是实际仓库根

## 一组高频修复命令

### Git 安全仓库

```bash
git config --global --add safe.directory /真实/仓库路径
git config --global --add safe.directory /软链接/显示路径
```

### 修复 `compile_commands.json` 旧路径前缀

```bash
perl -0pi -e 's#/旧/前缀#/新/前缀#g' /path/to/compile_commands.json
```

### 检查 `clangd` 是否真的安装

```bash
command -v clangd
clangd --version
```

### 重新加载 VS Code 工作区

完成修复后建议：

1. 用真正的仓库根重新打开 VS Code
2. 执行 `Developer: Reload Window`
3. 打开 `Output -> clangd` 看是否正常加载编译数据库

## 核心结论

这类问题很多时候不是插件本身坏了，而是下面几项之一：

- 用户和仓库属主不一致，触发 Git 安全限制
- `compile_commands.json` 的绝对路径和当前真实路径不一致
- VS Code 打开的不是实际仓库根
- `clangd` 扩展没有被明确告知该用哪个二进制和哪个编译数据库

判断是否是“权限问题在作祟”，不要靠感觉，直接查：

- `git status`
- `stat`
- `realpath`
- `command -v clangd`
- `clangd` 日志

这几项比重装插件有效得多。
