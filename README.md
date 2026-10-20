# 身边原理 · 科普视频自动化流水线

面向抖音的 **2–5 分钟** 竖屏科普：改 `episode.yaml` → 男声旁白 → 程序化 Blender 3D → 字幕合成 → 成片。

## 成片规格

- 分辨率：1080×1920（竖屏）
- 旁白：`edge-tts` / `zh-CN-YunjianNeural`
- 画面：默认 **2D 示意动画**（按旁白分镜）；可用 `--mode 3d` 切回 Blender
- 一键命令见下文

## 环境准备

### 1. Python 依赖

```powershell
cd D:\副业
python -m pip install -r requirements.txt
```

### 2. FFmpeg

需能在终端运行 `ffmpeg` 与 `ffprobe`。

Windows 可用：

```powershell
winget install --id Gyan.FFmpeg -e
```

安装后**重新打开终端**，或把 `ffmpeg.exe` 所在目录加入 PATH。  
Linux 一般已在 PATH 中（`ffmpeg` / `ffprobe`）。若不在 PATH，编辑 `config.yaml`：

```yaml
paths:
  ffmpeg: "C:/ffmpeg/bin/ffmpeg.exe"
  ffprobe: "C:/ffmpeg/bin/ffprobe.exe"
```

### 3. Blender 4.x

本机已可用便携版（从 Microsoft Store 包复制，供命令行调用）：

`D:\副业\tools\blender-4.5\blender.exe`

路径已写入 `config.yaml` 的 `paths.blender`。若你重装/换机，请改成新的 `blender.exe` 绝对路径。该路径在当前系统不存在时，会自动改找 PATH 里的 `blender`。

**2D 出片不需要 Blender。** Linux 上安装中文字体后再跑 2D，例如：

```bash
sudo apt install fonts-noto-cjk ffmpeg
python -m pip install -r requirements.txt
python -m pipeline.run_episode --id 001-air-conditioner --mode 2d
```

画面字体按「微软雅黑 → Noto Sans CJK → DejaVu」查找。没有雅黑时，字幕族名会改成本机的 Noto Sans CJK SC。

也可自行安装：https://www.blender.org/download/ （国内若官方 403，可用 Microsoft Store「Blender 4.5 LTS」）。

## 一键出片（首集：空调原理）

默认 2D 出片（推荐，按旁白内容示意）：

```powershell
cd D:\副业
python -m pipeline.run_episode --id 001-air-conditioner
```

3D 原理动画（Blender，输出到独立文件，不覆盖 2D）：

```powershell
python -m pipeline.run_episode --id 001-air-conditioner --reuse-audio --mode 3d
```

- 2D 成片：`episodes/001-air-conditioner/output/final.mp4`
- 3D 成片：`episodes/001-air-conditioner/output/final_3d.mp4`
- 3D 分镜缓存：`episodes/001-air-conditioner/renders_3d/`

已有旁白、只重出画面（更快）：

```powershell
python -m pipeline.run_episode --id 001-air-conditioner --reuse-audio --mode 2d
```

成功后查看：

- `episodes/001-air-conditioner/output/final.mp4` — 成片
- `episodes/001-air-conditioner/output/subtitles.srt` — 字幕
- `episodes/001-air-conditioner/output/douyin_copy.txt` — 标题/简介/话题草稿

## 目录说明

| 路径 | 作用 |
|------|------|
| `config.yaml` | 分辨率、音色、Blender/FFmpeg 路径 |
| `episodes/*/episode.yaml` | 单集旁白与分镜 |
| `templates/2d/` | 2D 分镜，模块名对应 `template_2d`，需提供 `draw_scene` |
| `templates/blender/` | 3D 场景模板 |
| `pipeline/` | TTS / 字幕 / 渲染 / 合成 |
| `docs/series_bible.md` | 系列调性 |
| `docs/douyin_publish.md` | 发布文案模板 |

## 分集队列

`episodes/` 按目录名排序。每日自动发布取这里尚未出片的下一集。

当前下一集：**`episodes/012-water-purifier`**（净水器，`template_2d: water_purifier_scenes`）。001–011 已有成稿，不要改它们的文案。

## 新增一集怎么做

1. 复制上一集目录（例如把 `011-air-fryer` 拷成 `012-water-purifier`）
2. 改 `episode.yaml` 的标题、旁白、`template_2d`
3. 在 `templates/2d/` 增加同名场景模块，并导出 `draw_scene`。只有 `--mode 3d` 才要在 `templates/blender/` 注册 `SCENE_BUILDERS`
4. 运行：`python -m pipeline.run_episode --id 012-water-purifier --mode 2d`

文案节奏参考：`templates/script_style.md`。

## 流水线步骤

1. 读取分集 YAML  
2. 逐段 `edge-tts` 生成 mp3，并拼接整轨  
3. 按句生成 SRT  
4. Blender headless 按音频时长渲染各分镜  
5. FFmpeg 拼接画面、烧字幕、混音导出  

## 注意

- 首集是**科普示意风**，不是写实广告片；优先保证可脚本化批量出片
- 渲染较耗时；调试文案时请先用 `--tts-only`
- 抖音发布前用真机预览字幕安全区（`config.yaml` 里 `subtitle.margin_v`）
