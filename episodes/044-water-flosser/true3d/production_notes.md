# 044 冲牙器｜真三维成片

批准：2026-11-21 12:56（Asia/Shanghai），用于当晚 18:05 档。
发布：尚未发布。批准不是上线记录，本目录也不包含成片 MP4。

## 成片规格

- 191.200 秒，1080×1920，30 fps，5736 帧。
- 旁白 `zh-CN-YunjianNeural`，语速 `+0%`，句间 280 ms。PCM 实测口播 190.952 秒。脚本见 `script.txt`，时间戳见 `narration_timings.json`。
- 画面是 Three.js 0.181.2 的真实网格：水箱、吸水管、电机、偏心轮、连杆、活塞、进出水单向阀、喷嘴、牙面接触。相机有透视和轨道运动。
- HyperFrames 0.9.74 负责无头 Chromium 采样。FFmpeg 只做混音、烧字幕和编码。
- 兼容档：H.264 Constrained Baseline、无 B 帧、yuv420p、AAC 48 kHz 立体声、faststart。实测约 -16.06 LUFS、-1.77 dBTP。
- 已批准成片的 SHA-256 记在 `approval.json`，文件本身不进 git。

## 和 2D 稿的关系

`episode.yaml` 里的 `scenes` 仍是早先的 2D 后备稿，画面模块是 `water_flosser_scenes`。那一版把脉冲讲成「喷嘴细所以一股一股」，批准稿没有沿用这个简化。晚上要出的是本目录的脚本和三维画面。`--mode 2d` 仍然只渲染 2D，不会偷偷改成三维。

## 健康边界

脉冲水流、可接触部位的食物残渣和牙菌斑辅助清洁，依据 ADA / MouthHealthy 与 ADA 牙间清洁说明。活塞、连杆、单向阀只作为专利里的代表性结构，不代表所有型号。没有压力、疗效或覆盖率数字。不能代替刷牙和专业护理；疼痛或持续出血应停用并咨询牙医。来源见 `sources.json`。
