# 输出正确文本文件点击跳转格式

这个说明用于约束以后在回答里引用本地文本文件时，必须输出成“可点击并且能准确跳到指定行”的格式。

## 目标

当需要引用某个本地文本文件的某一行时，输出后应满足这两个条件：

1. 用户可以直接点击
2. 点击后可以跳转到正确文件的正确行号

## 两种可点击跳转样式

以后把可点击跳转样式分成两类：

1. 具体型
2. 清爽型

---

## 具体型

### 目标

适合在需要明确暴露真实绝对路径、兼容普通 Markdown 链接渲染、或者用户明确要求“必须看到完整路径”的场景使用。

### 正确格式

统一使用下面这种 Markdown 链接格式：

```md
[显示名称](绝对路径#L行号)
```

例如：

```md
[kernel/Makefile](/home/haodong/data/LubanCat_Linux_rk3588_SDK_20260113/kernel/Makefile#L1267)
```

再例如：

```md
[drivers/of/platform.c](/home/haodong/data/LubanCat_Linux_rk3588_SDK_20260113/kernel/drivers/of/platform.c#L174)
```

### 各部分含义

- `[]` 里放显示给用户看的名字
- `()` 里必须放本地文件的绝对路径
- 行号必须写成 `#L数字`
- 例如第 141 行就写成 `#L141`

### 必须遵守的规则

1. 尽量使用绝对路径，不要使用相对路径
2. 必须带 `#L行号`，否则通常只能打开文件，不能准确跳到那一行
3. 显示名称可以简短，但路径必须准确
4. 对于普通文本文件、源码文件、配置文件，都优先使用这一种格式

### 推荐写法

推荐：

```md
[kernel/Makefile](/home/haodong/data/LubanCat_Linux_rk3588_SDK_20260113/kernel/Makefile#L1267)
```

推荐：

```md
[drivers/tty/serial/8250/8250_dw.c](/home/haodong/data/LubanCat_Linux_rk3588_SDK_20260113/kernel/drivers/tty/serial/8250/8250_dw.c#L540)
```

### 适用特点

1. 能准确显示真实文件位置
2. 普通 Markdown 环境兼容性好
3. 缺点是绝对路径较长，视觉上不够清爽

---

## 清爽型

### 目标

适合当前这个前端/插件环境。  
特点是界面只显示相对路径或简短路径，看起来更干净，由前端把它自动识别成可点击跳转引用。

### 正确格式

统一使用下面这种纯文本引用格式：

```text
`@路径:行号[:列号]`
```

例如：

```text
`@arch/arm64/boot/dts/rockchip/rk3588-lubancat-5io.dts:19`
```

再例如：

```text
`@drivers/of/platform.c:174`
```

如果需要列号，也可以写成：

```text
`@scripts/link-vmlinux.sh:141:1`
```

### 各部分含义

- 必须放在反引号里
- 必须以 `@` 开头
- 路径优先写工作区内相对路径
- 行号写成 `:数字`
- 如果前端支持，还可以继续附加 `:列号`

### 必须遵守的规则

1. 路径必须是当前工作区内真实存在的文件
2. 优先使用相对路径，不要写冗长的绝对路径
3. 行号必须真实存在
4. 这种格式本质上依赖前端/插件识别能力
5. 在当前环境下，清爽型通常优先于具体型

### 推荐写法

推荐：

```text
`@arch/arm64/boot/dts/rockchip/rk3588s.dtsi:5622`
```

推荐：

```text
`@drivers/tty/serial/8250/8250_dw.c:540`
```

### 适用特点

1. 显示更简洁
2. 更适合聊天界面阅读
3. 不会暴露冗长绝对路径
4. 依赖插件或前端对该语法的识别

---

## 不要使用的写法

不要只写纯路径，因为通常不能直接点击：

```text
/home/haodong/data/LubanCat_Linux_rk3588_SDK_20260113/kernel/Makefile:1267
```

不要写成我之前错误使用过的行号格式：

```md
`@kernel/Makefile:1267`
```

不要漏掉 `#L`：

```md
[kernel/Makefile](/home/haodong/data/LubanCat_Linux_rk3588_SDK_20260113/kernel/Makefile)
```

## 一次引用多个位置时

如果要引用多个文件位置，每个位置各写一个独立链接，便于分别点击。对于当前前端，两个清爽型引用不能放在同一物理行，也不能用两个空格加换行（Markdown hard line break）连接；否则可能只识别最后一个。

```md
[drivers/of/platform.c](/home/haodong/data/LubanCat_Linux_rk3588_SDK_20260113/kernel/drivers/of/platform.c#L174)
[drivers/of/base.c](/home/haodong/data/LubanCat_Linux_rk3588_SDK_20260113/kernel/drivers/of/base.c#L617)
```

或者在清爽型环境里写成：

```text
`@drivers/of/platform.c:174`

`@drivers/of/base.c:617`
```

不要这样写：

```text
`@drivers/of/platform.c:174`  
`@drivers/of/base.c:617`
```

不要这样写：

```text
`@drivers/of/platform.c:174` `@drivers/of/base.c:617`
```

## 默认执行约定

以后只要需要输出“本地文本文件 + 行号”的引用，按下面顺序判断：

1. 如果当前环境支持 `@路径:行号` 这类插件渲染，优先使用清爽型
2. 如果当前环境不支持，或者用户明确要求显示真实绝对路径，则使用具体型
3. 如果用户特别强调“简洁清爽”，默认使用清爽型
4. 如果用户特别强调“准确暴露真实路径”，默认使用具体型

默认优先模板：

清爽型：

```text
`@相对路径:行号`
```

具体型：

```md
[文件名或相对识别名](绝对路径#L行号)
```

除非用户明确要求别的格式，否则不要混用风格。
