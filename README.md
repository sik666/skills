# Practical Codex Skills

这个仓库维护日常实用的 Codex skills，用来沉淀常见工程问题的处理流程、排查经验和辅助脚本。每个 skill 都对应一类可复用任务，方便之后遇到类似问题时稳定地触发和执行。

## Skills

### generate-android-kernel-compile-commands

用于从已经编译过的 Android 源码 `out` 目录和 Kbuild `.cmd` 文件中，为 Android Linux kernel 源码生成 `compile_commands.json`。

适用于 `kernel/*/sm8650` 这类 Android kernel 工程，尤其是 clangd 需要有效 compile database 的场景。它会指导如何定位 `KERNEL_OBJ`、纳入外部模块 object 目录、调用 kernel 自带的 `scripts/clang-tools/gen_compile_commands.py`、处理 `/home` 和 `/mnt` 路径差异，并用 `clangd --check` 验证结果。

### fix-kernel-clangd-issues

用于诊断和修复 Linux 或 Android kernel 工作区里的 clangd 问题，特别是 `compile_commands.json` 已经存在但 clangd 仍然不正常工作的情况。

适用于 clangd 回退到默认参数、加载了错误的 compile database、受到全局 clangd 配置污染、混用软链接路径和真实路径、跳转到兄弟源码树、找不到 generated headers、和 Microsoft C/C++ cpptools 冲突，或者对当前 kernel 配置没有编译到的文件报错等问题。

## 持续更新

这个仓库会持续更新，把更多日常使用中沉淀下来的实用 skills 加进来。
