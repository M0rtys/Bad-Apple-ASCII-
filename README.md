# Bad Apple 字符画全屏播放器

一个使用 Python 编写的全屏 ASCII 字符画视频播放器。使用 OpenCV 读取视频、NumPy 转换灰度像素、Pygame-CE 绘制字符画，并可通过 FFmpeg 提取和播放视频音轨。

> 本项目只提供播放器程序，不附带 Bad Apple 原版视频或音乐。请自行准备有权使用的媒体文件。

## 功能

- 全屏字符画播放，支持窗口调试模式
- 自动按显示器尺寸计算字符网格
- 可调整字号、对比度、亮度和黑白反转
- 可选音频提取与播放
- 循环播放、暂停/继续、从头播放
- 支持 OpenCV 能读取的视频格式（推荐 MP4/H.264）

## 环境要求

- Windows 10/11（其他平台可能可用，但快捷键和全屏体验未逐一测试）
- Python 3.11 或 3.12 64 位建议优先使用
- Python 3.14 若依赖没有对应 wheel，建议安装 Python 3.12 并使用独立虚拟环境

## 安装

在项目文件夹打开 PowerShell：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

如果电脑没有 Python 3.12，先从 [Python 官网](https://www.python.org/downloads/) 安装 64 位版本。也可以将 `py -3.12` 改为 `python`，但需确认当前解释器版本。

## 准备视频

将自己的视频放到项目目录，例如：

```text
BadApple-ASCII-Player-CN/
├── bad_apple_fullscreen.py
├── requirements.txt
├── README.md
└── bad_apple.mp4   # 自行准备，不要提交版权媒体
```

## 运行

全屏播放（默认循环并尝试播放音频）：

```powershell
python bad_apple_fullscreen.py bad_apple.mp4
```

更密集的字符画：

```powershell
python bad_apple_fullscreen.py bad_apple.mp4 --font-size 9 --contrast 1.3
```

窗口模式（排查问题时使用）：

```powershell
python bad_apple_fullscreen.py bad_apple.mp4 --windowed
```

静音：

```powershell
python bad_apple_fullscreen.py bad_apple.mp4 --mute
```

不循环：

```powershell
python bad_apple_fullscreen.py bad_apple.mp4 --no-loop
```

反转黑白：

```powershell
python bad_apple_fullscreen.py bad_apple.mp4 --invert
```

## 快捷键

| 按键 | 功能 |
|---|---|
| `Esc` 或 `Q` | 退出 |
| `Space` | 暂停 / 继续 |
| `R` | 从头播放 |

## 参数

| 参数 | 默认值 | 说明 |
|---|---:|---|
| `--font-size` | `12` | 字符字号，范围 6–40 |
| `--contrast` | `1.25` | 对比度 |
| `--brightness` | `0` | 亮度偏移 |
| `--fps` | `0` | 目标帧率；0 使用源视频帧率 |
| `--invert` | 关闭 | 反转黑白 |
| `--no-loop` | 关闭 | 关闭循环 |
| `--mute` | 关闭 | 不播放音频 |
| `--windowed` | 关闭 | 使用窗口模式 |

## 常见问题

### `No module named pygame`

确认已激活项目虚拟环境，然后运行：

```powershell
python -m pip install -r requirements.txt
```

本项目使用 `pygame-ce` 发行包，但代码导入名称仍然是 `pygame`。不要同时安装 `pygame` 和 `pygame-ce`。

### 安装依赖时出现 `Failed to build wheel`

升级 pip：

```powershell
python -m pip install --upgrade pip setuptools wheel
```

若 Python 版本太新且依赖没有预编译 wheel，建议使用 Python 3.12 64 位创建虚拟环境。

### 没有声音

- 确认视频本身带有音轨。
- 确认未使用 `--mute`。
- 检查 Windows 音量混合器。
- 音轨提取依赖 `imageio-ffmpeg`；提取失败时程序会尝试静音播放。

### 播放卡顿

- 将 `--font-size` 调大（例如 14 或 16），减少字符数量。
- 关闭其他占用 CPU 的程序。
- 尝试 `--fps 24`。
- 全屏字符逐行绘制对终端/窗口渲染性能要求较高，性能取决于屏幕分辨率、字号和视频帧率。

## 项目结构

```text
BadApple-ASCII-Player-CN/
├── bad_apple_fullscreen.py
├── requirements.txt
├── README.md
├── LICENSE
└── .gitignore
```

## 许可

源代码以 MIT License 发布，详见 [LICENSE](LICENSE)。

请注意：MIT 许可只适用于本仓库作者拥有权利的代码，不授予 Bad Apple 原曲、视频、角色或其他第三方素材的使用权。
