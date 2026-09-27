# 修复容器编译 `compile_commands.json` 路径供 `clangd` 使用

## 适用场景

下面这类工程经常会遇到 `clangd` 无法正确索引的问题：

- 代码是在 Docker 或 dev container 里编译的
- 生成出来的 `compile_commands.json` 记录了容器内路径
- 宿主机上的源码路径和容器路径不一致
- `clangd` 可以读到 `compile_commands.json`，但提示找不到源文件、找不到头文件、或者工作目录不存在

典型症状包括：

- `failed to set CWD to /workspace/...`
- `file not found`
- `sdkconfig.h file not found`
- 明明存在 `compile_commands.json`，但跳转、补全、诊断都不正常

## 核心原因

`compile_commands.json` 里记录的是编译时的真实路径。

如果它是在容器里生成的，那么常见内容会像这样：

- `directory`: `/workspace/project/build`
- `file`: `/workspace/project/src/main.c`
- `command`: 里有大量 `-I/workspace/...`

但宿主机实际路径可能是：

- `/home/haodong/data/project/...`

这时宿主机上的 `clangd` 看到的是一份“路径真实但环境不真实”的编译数据库，所以会失效。

## 解决思路

把 `compile_commands.json` 里的容器路径前缀批量替换成宿主机路径前缀。

默认映射规则是：

- `/workspace` -> 你传入的 `--workspace`

如果你还有其它容器前缀需要修，比如：

- `/opt/project`
- `/src`

也可以通过额外参数继续补映射。

## 文件

本目录包含：

- `README.md`
- `fix_compile_commands.py`

## 一键用法

先进入含有 `compile_commands.json` 的目录，然后执行：

```bash
python ./fix_compile_commands.py --workspace /你的/workspace --in-place
```

例如：

```bash
cd /home/haodong/data/esp32/esp-idf/examples/get-started
python /mnt/data_0/skills/修复容器编译compile_commands路径供clangd使用/fix_compile_commands.py \
  --workspace /home/haodong/data/esp32 \
  --file ./compile_commands.json \
  --in-place
```

执行后会：

1. 自动备份原文件为 `compile_commands.json.bak`
2. 原地重写 `compile_commands.json`
3. 把所有 `/workspace/...` 改成你指定的宿主机路径

## 常用命令

### 1. 原地修复当前目录的 `compile_commands.json`

```bash
python /mnt/data_0/skills/修复容器编译compile_commands路径供clangd使用/fix_compile_commands.py \
  --workspace /home/haodong/data/esp32 \
  --in-place
```

### 2. 指定输入文件但输出到新文件

```bash
python /mnt/data_0/skills/修复容器编译compile_commands路径供clangd使用/fix_compile_commands.py \
  --workspace /home/haodong/data/esp32 \
  --file ./compile_commands.json \
  --output ./compile_commands.fixed.json
```

### 3. 追加其它路径映射

```bash
python /mnt/data_0/skills/修复容器编译compile_commands路径供clangd使用/fix_compile_commands.py \
  --workspace /home/haodong/data/esp32 \
  --in-place \
  --map /opt/project=/home/haodong/data/project \
  --map /src=/home/haodong/src
```

## 参数说明

- `--workspace`
  传宿主机上的 workspace 根目录。脚本默认把容器里的 `/workspace` 映射到这里。

- `--file`
  指定 `compile_commands.json` 路径。默认是当前目录下的 `compile_commands.json`。

- `--in-place`
  原地修改输入文件，并自动生成 `.bak` 备份。

- `--output`
  输出到新文件，而不是覆盖原文件。

- `--map OLD=NEW`
  追加额外路径前缀映射。可以传多次。

## 推荐排查顺序

修完路径后，如果 `clangd` 还是不完全正常，按这个顺序继续看：

1. `compile_commands.json` 的 `directory`、`file`、`-I` 是否已经都是宿主机可访问路径
2. 工程生成目录是否真实存在，比如 `build/config`
3. 本机是否安装了对应交叉编译器
4. 当前 `clangd` 版本是否过老，不支持某些编译参数

## 限制说明

这个脚本解决的是“路径前缀不一致”问题，不负责自动修复下面这些问题：

- 本机没有交叉编译器
- `clangd` 版本太老，不认识某些 GCC/目标架构参数
- 头文件本身没有生成，比如工程还没 build 完

如果修完路径后还有诊断噪音，通常还需要继续做下面其中一项：

- 给 `clangd` 增加 `.clangd` 配置，过滤不兼容参数
- 安装并暴露交叉编译器路径
- 在宿主机重新生成一份 `compile_commands.json`

## 快速判断是不是这个问题

可以直接看 `compile_commands.json` 前几项：

```bash
python - <<'PY'
import json
with open("compile_commands.json", "r", encoding="utf-8") as f:
    data = json.load(f)
for item in data[:3]:
    print(item.get("directory"))
    print(item.get("file"))
    print(item.get("command", "")[:300])
    print("-" * 60)
PY
```

如果看到的是 `/workspace/...`、`/app/...`、`/src/...` 这一类容器内路径，而宿主机上不存在这些路径，那么大概率就是这个问题。
