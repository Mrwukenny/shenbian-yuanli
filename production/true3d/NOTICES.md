# 真三维依赖与授权

本仓库**没有**收录 OpenMontage 的源代码。044 的网格、场景、旁白、封面和原创和弦垫是身边原理自己的制作文件。OpenMontage 以 AGPLv3 提供动画工作流；如果另行取得并分发那个程序，适用它自己的许可证。这里不把它的技能文件或运行时拷进 git。

| 组件 | 版本 | 许可证 | 怎么用 |
|------|------|--------|--------|
| three | 0.181.2 | MIT | `npm ci` 后由 `setup.py` 复制 `three.module.js`，复制件不提交 |
| hyperframes | 0.9.74 | Apache-2.0 | 外部渲染器。只通过 CLI 调用，不把包内文件提交进 git |
| gsap | 3.15.1 | [Standard no-charge license](https://gsap.com/standard-license/) | 合成时间线。同样只在本地 `node_modules` |
| @fontsource/noto-sans-sc | 5.3.1 | OFL-1.1 | 画面里的中文 woff2 |
| Noto Sans CJK | 发行版字体包 | OFL-1.1 | `sudo apt install fonts-noto-cjk`，给 ASS 烧录用 |
| edge-tts | 见仓库 `requirements.txt` | 上游包许可证 | 免费在线语音，不是付费生成 API |
| Pillow / numpy / FFmpeg | 系统或 pip | 各自许可证 | 封面、混音、编码 |

不要把 `node_modules`、虚拟环境、API key、浏览器缓存或整段成片 MP4 提交上来。HyperFrames 的云渲染、HeyGen 登录和付费音色都不要用于这条流水线。
