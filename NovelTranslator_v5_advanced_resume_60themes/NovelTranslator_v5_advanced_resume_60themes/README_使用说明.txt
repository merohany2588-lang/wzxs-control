小说翻译器 Novel Translator - V5 高级布局 + 60主题 + 实时写入 + 断点续译版

V5 修复重点：
1. 修复 Google 免费引擎中文语言码错误：
   旧版传 zh，deep-translator 需要 zh-CN。
2. 修复 OPUS-MT 初始化错误：
   旧版使用 transformers pipeline('translation')，你的 transformers 环境不支持该 task。
   V5 改为 AutoTokenizer + AutoModelForSeq2SeqLM 直接调用 Marian/OPUS 模型。
3. 新增实时写入：
   每完成一段，立即追加写入 *_译文.txt 和 *_中英对照.txt。
4. 新增断点续译：
   每完成一段都会更新 output/.../checkpoint.json。
   任务终止或软件关闭后，再次选择同一文件、同一语言方向，会自动继续未完成任务。
5. 新增 60 套主题：
   在“主题中心”下拉选择并应用。
6. 保留 V4 彩色选项卡和策略中心。

建议：
- 免费接口不稳定，长篇小说建议 API 优先 + OPUS-MT 兜底。
- OPUS-MT 模型目录必须是真实 MarianMT/OPUS-MT 模型目录。
- 如果 OPUS-MT 仍失败，请确认目录内有 config.json、tokenizer 文件、pytorch_model.bin 或 model.safetensors。
