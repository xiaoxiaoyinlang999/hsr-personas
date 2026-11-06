# hsr-personas

> 《崩坏：星穹铁道》全角色 AI 角色扮演人设库 —— 84 个角色 × 官方故事全文 × 语音全集 × 台词画像，一份档案就够把角色演活。

## 这是什么

每份档案由自动化管线从游戏数据快照生成，包含：

| 模块 | 内容 | 来源 |
|---|---|---|
| 角色卡 | 称号 / 命途 / 属性 / 派系 / 稀有度 / CV / 短信签名 / 实装版本 | wiki 数据 + 游戏数据 |
| 官方介绍 | 介绍全文 + 卷首语 + 角色定位 | wiki 数据 |
| 角色故事 | 官方 5~7 段全文 | 游戏数据 Avatar.Story |
| 语音全集 | 30~119 条，按「认知日常 / 关系评价 / 战斗」三组分类 | 游戏数据 archive 语音 |
| 台词画像 | 剧情台词量 / 平均句长 / 超短句占比 / 高频词 | 19.6 万条剧情对话统计 |
| 关系网络 | 「关于 XX」「队伍编成·XX」标题实锤的关联人物列表 | 语音标题提取 |
| AI 骨架 | 可直接用作 persona / system prompt 素材的角色卡 + 语言风格建议 + 对话规则 | 管线合成 |

示例角色：[三月七 · 存护](personas/三月七%20·%20存护.md)（4890 条剧情台词 / 113 条语音）、[云璃](personas/云璃.md)、[丹恒](personas/丹恒.md)。

## 怎么用

### 方式一：直接拿档案用
`personas/` 下每个 `.md` 都是自包含档案。把「AI 角色扮演骨架」+ 你需要的段落贴进任意 LLM 的 system prompt，或配合角色扮演框架（如 AstrBot persona、SillyTavern 卡片）使用。

### 方式二：自己重新生成
仓库 `data/` 自带最小数据集（角色故事、语音、wiki 卡、ID 映射，约 4.2 MB），clone 后直接跑：

```bash
python3 scripts/build_personas.py --clean_dir data --out_dir personas
```

`personas/` 中的「台词画像」段落由完整数据（含 30 MB 的剧情对话文本映射 `SR_Talk_CH.json`，未随仓库分发）生成；用自带数据重跑会得到缺该段落、其余完全一致的版本。需要台词画像时自备 `data/textmap/SR_Talk_CH.json`（说话人→台词的 JSON 对象，格式见脚本头部注释）再运行即可。

## 数据来源

- 游戏数据：社区维护的星穹铁道数据站静态快照（Avatar 故事 / 语音 / wiki 卡字段），对应 `data/` 下的 jsonl
- 剧情对话：`SR_Talk_CH` 文本映射（19.6 万条台词，4413 个说话人）——体积与版权原因未随仓库分发，自备后放入 `data/textmap/`
- 数据未随版本更新，如需最新版本内容请从数据站获取快照后替换 `data/` 重跑管线

## 角色头像

`data/icons/` 内置 84 张角色商店头像（约 11 MB），覆盖全部 80 份人设角色。文件名为数字角色 ID，与 `data/gd_Avatar.jsonl` 中该角色的 `Icon` 字段末段一致（如银狼 `Icon: avatarshopicon/Avatar/1221` → `data/icons/1221.png`）。可用 `python3 -c "import json; [print(o['name'], o['Icon'].split('/')[-1]) for o in map(json.loads, open('data/gd_Avatar.jsonl'))]"` 列出 ID 对照。

## 版权与免责声明

- **角色文本（故事、语音、介绍）与图片素材（头像）的著作权归 miHoYo / HoYoverse（COGNOSPHERE）所有。**
- 本仓库仅对官方公开资料做结构化整理与统计，**非官方产物，与 miHoYo/HoYoverse 无关**。
- 仅供学习交流与社区二创，**禁止商用**；如需删档请提 issue，会在确认后移除。
- 若构成侵权请通过 issue 联系，我们将及时处理。

## License

- `scripts/`：MIT
- `personas/`：内容版权归 miHoYo/HoYoverse，本仓库按上文声明使用

## 管线说明

1. 原始数据清洗（jsonl 拆解、Hash 文本映射还原中文）
2. 角色聚合：Avatar ID → 官方故事 + 语音分组
3. 台词画像：按说话人聚合统计句长分布与词频
4. 关系提取：正则匹配语音标题中的关系类目
5. 模板组装：合成「档案 + AI 骨架」双用途 markdown
