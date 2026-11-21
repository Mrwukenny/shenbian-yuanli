# 真三维出片

从 044 起，发布标准改为 Three.js + HyperFrames 的真三维。**目前只有 044 冲牙器做完并获批。** 045–047 仍是 2D 稿，没有三维工程。001–043 不要改成这套流程。

044 的源文件在 `episodes/044-water-flosser/true3d/`。`episode.yaml` 的 `scenes` 仍是 2D 后备，`--mode 2d` 不会读取真三维页面。

批准时间是 2026-11-21 12:56（Asia/Shanghai），给当晚 18:05 用。`approval.json` 里 `publication_status` 仍是 `not_published`。把源文件推进仓库不等于已经发到抖音。

## 安装

在仓库根目录：

```bash
npm ci --prefix production/true3d
python3 production/true3d/setup.py
sudo apt install fonts-noto-cjk ffmpeg
python3 -m pip install -r requirements.txt numpy
```

`npm ci` 安装并锁定：

- `three@0.181.2`（MIT）
- `hyperframes@0.9.74`（Apache-2.0）
- `gsap@3.15.1`（Standard no-charge license）
- `@fontsource/noto-sans-sc@5.3.1`（OFL-1.1）

`setup.py` 把 three、gsap 和两份简体中文 woff2 复制到 `episodes/044-water-flosser/true3d/assets/`。该目录下的字体和脚本不提交。系统里的 Noto CJK 只给 ASS 烧字幕用。

不要使用 HyperFrames 的云渲染、HeyGen 账号或付费音色。授权说明见 `NOTICES.md`。

## 只检查，不渲完整片

```bash
node production/true3d/test_kinematics.mjs
node production/true3d/qa_frame.mjs
```

运动学检查连杆长度和两个单向阀不会同时打开。`qa_frame.mjs` 用本机 Chrome 打开页面，在 8 秒、68 秒、80 秒各画一帧，并确认来回 seek 的像素一致。截图写到 `episodes/044-water-flosser/true3d/artifacts/`，这个目录不进 git。

抽几张静帧（仍然不是 191 秒成片）。还没生成 `mix.wav` 时，静帧也能拍；CLI 可能提示匿名用量统计，可用 `hyperframes telemetry disable` 关掉，它不上传成片。全片编码仍要先有混音：

```bash
node production/true3d/node_modules/hyperframes/bin/hyperframes.mjs snapshot \
  episodes/044-water-flosser/true3d \
  --at 8,68,80 --no-end --no-browser-gpu \
  -o episodes/044-water-flosser/true3d/artifacts/snapshots
```

## 声音、封面、短样片、全片

旁白与混音（会访问 edge-tts，不走付费 API）。批准的时间戳已经在 `narration_timings.json`，不要随手覆盖。

```bash
python3 episodes/044-water-flosser/true3d/bin/generate_voice.py
python3 episodes/044-water-flosser/true3d/bin/prepare_media.py
```

`generate_voice.py` 只在加上 `--update-timings` 时才改写批准时间戳。`prepare_media.py` 会按当前旁白重写字幕，确认时长仍是 39 句、约 191.2 秒再保留。

封面要用 QA 先导出透明机身图。已提交的 `covers/*.jpg` 是批准稿，默认不覆盖。

```bash
python3 episodes/044-water-flosser/true3d/bin/make_covers.py --force
```

两秒样片，用来确认编码，不要当成成片：

```bash
node production/true3d/node_modules/hyperframes/bin/hyperframes.mjs render \
  episodes/044-water-flosser/true3d \
  --start 8 --end 10 --fps 30 --quality draft --no-browser-gpu \
  -o episodes/044-water-flosser/true3d/renders/sample-8-10.mp4
```

全片约 5736 帧。本仓库不提交 MP4。画面渲完后再烧字幕：

```bash
node production/true3d/node_modules/hyperframes/bin/hyperframes.mjs render \
  episodes/044-water-flosser/true3d \
  --fps 30 --quality delivery --crf 18 --workers 1 --no-browser-gpu \
  -o episodes/044-water-flosser/true3d/renders/visual.mp4

python3 episodes/044-water-flosser/true3d/bin/export_film.py \
  --visual episodes/044-water-flosser/true3d/renders/visual.mp4
```

`export_film.py` 写出 master 和 Constrained Baseline 兼容档，都要求 yuv420p、AAC、faststart，并且 `moov` 在 `mdat` 前面。

## 还没有三维的集

对 045、046、047 不要跑上面的渲染命令。它们只有 `episode.yaml` 和 `templates/2d/`。
