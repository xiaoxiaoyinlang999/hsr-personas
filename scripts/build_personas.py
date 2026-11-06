#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_personas.py — 从清洗后的崩坏：星穹铁道数据生成 AI 角色扮演人设档案。

输入（clean/ 目录）：
  gd_角色技能.jsonl   — 游戏数据：角色故事(Story) + 语音(archive_*)【必选】
  角色.jsonl          — wiki 卡字段（称号/命途/介绍/卷首语/短信签名/CV…）【必选】
  gd_Avatar.jsonl     — ID→{name, path, element, rarity, ver} 映射【必选】
  textmap/SR_Talk_CH.json — 剧情对话（说话人→台词）【可选】缺失时跳过台词画像模块

输出：personas/<角色名>.md（每角色一份完整人设）

用法：
  python3 build_personas.py --clean_dir data --out_dir personas
  （仓库 data/ 自带必选数据；textmap/SR_Talk_CH.json 可选，缺失时自动跳过台词画像）

数据来源声明见 README.md。角色文本版权归 miHoYo/HoYoverse 所有。
"""
import argparse, collections, json, os, re, statistics

GAME_WORDS = ['游戏','玩家','无聊','好玩','通关','副本','存档','攻略','外挂','作弊','升级',
              '经验','NPC','账号','卡','刷','结算','道具','装备','剧情','任务','通关']

def load_jsonl(path):
    with open(path, encoding='utf-8') as f:
        return [json.loads(l) for l in f if l.strip()]

def collect_game_roles(path):
    """从 gd_角色技能.jsonl 收集每角色的故事与语音。"""
    roles = {}
    for o in load_jsonl(path):
        key = str(o.get('_key', ''))
        v = o.get('值')
        if not isinstance(v, list) or not v or not isinstance(v[0], dict):
            continue
        r = roles.setdefault(key, {'stories': [], 'voices': [], 'name': None})
        if 'Story' in v[0] and len(v) > len(r['stories']):
            r['stories'] = v
        elif str(v[0].get('_id', '')).startswith('archive_') and len(v) > len(r['voices']):
            r['voices'] = v
        pre = o.get('Pre')
        if isinstance(pre, dict) and pre.get('Name'):
            r['name'] = pre['Name']
    return roles

def collect_wiki(path):
    wiki = {}
    for d in load_jsonl(path):
        wiki[d.get('标题')] = d.get('字段', {})
    return wiki

def collect_avatar_names(path):
    """从 gd_Avatar.jsonl 建立 ID→{name, desc, path, element, rarity, ver} 映射（同 ID 取最后一行）。"""
    m = {}
    for o in load_jsonl(path):
        mid = str(o.get('_id'))
        m[mid] = {
            'name': o.get('Name'),
            'desc': o.get('Desc'),
            'path': o.get('Path'),
            'element': o.get('Element'),
            'rarity': o.get('Rarity'),
            'ver': o.get('Ver'),
        }
    return m

def talk_stats(talks_path, names):
    data = json.load(open(talks_path, encoding='utf-8'))
    per = collections.defaultdict(list)
    for x in data:
        s = x.get('S')
        if s in names:
            per[s].append(x['T'])
    stats = {}
    for name, texts in per.items():
        lens = [len(t) for t in texts]
        joined = ''.join(texts)
        words = {w: joined.count(w) for w in GAME_WORDS if joined.count(w) >= 5}
        stats[name] = {
            'count': len(texts),
            'avg_len': round(statistics.mean(lens), 1) if lens else 0,
            'short_ratio': round(sum(1 for l in lens if l <= 10) / len(lens), 2) if lens else 0,
            'ellipsis': joined.count('…') + joined.count('……') * 1,  # 粗略
            'top_words': dict(sorted(words.items(), key=lambda kv: -kv[1])[:6]),
        }
    return stats

def extract_relations(voices):
    """从语音 Title 提取关系网：仅「关于XX」「队伍编成·XX」（闲谈话题不算人物）。"""
    rel = []
    for v in voices:
        t = v.get('Title') or ''
        m = re.match(r'^(关于|队伍编成 ·)\s*(.+?)( ·.*)?$', t)
        if m and m.group(2) not in ('自己', '名字', '普罗米修斯'):
            rel.append((m.group(2), t, v.get('Voice', '')))
    return rel

ROLE_GROUPS = {  # 按命途分组展示
}

def build_persona(name, key, g, w, ts):
    """组装单个角色人设 markdown。"""
    stories = g['stories']
    voices = g['voices']
    lines = []
    ap = lines.append

    ap(f"# {name}（{w.get('称号', name)}）")
    ap('')
    meta = []
    if w: meta.append(f"{w.get('稀有度','')}")
    if w.get('命途'): meta.append(f"{w['命途']}命途")
    if w.get('元素属性'): meta.append(f"{w['元素属性']}属性")
    if w.get('派系'): meta.append(w['派系'])
    if w.get('出身'): meta.append(f"出身 {w['出身']}")
    if w.get('实装版本'): meta.append(f"实装 Ver {w['实装版本']}")
    if meta: ap('> ' + ' · '.join(meta))
    cv = []
    if w.get('中文CV'): cv.append(f"中 CV {w['中文CV']}")
    if w.get('日文CV'): cv.append(f"日 CV {w['日文CV']}")
    if cv: ap('> ' + '，'.join(cv))
    if w.get('短信签名'): ap(f"> 短信签名：{w['短信签名']}")
    ap('')

    if w.get('介绍'):
        ap('## 官方介绍')
        ap('')
        ap(w['介绍'])
        ap('')
        if w.get('卷首语'): ap(f"> 卷首语：{w['卷首语']}")
        ap('')
        if w.get('角色定位'):
            ap(f"**定位**：{w['角色定位']}")
            ap('')

    if stories:
        ap(f"## 角色故事（官方全文，{len(stories)} 段）")
        ap('')
        titles = ['一','二','三','四','五','六','七']
        for i, s in enumerate(stories):
            ap(f"### 故事{titles[i] if i < len(titles) else i+1}")
            ap('')
            ap(s.get('Story', '').strip())
            ap('')

    if voices:
        ap(f"## 语音全集（{len(voices)} 条）")
        ap('')
        # 分组：关系类 / 剧情类 / 战斗类
        rel_k, world_k, battle_k = [], [], []
        for v in voices:
            t = v.get('Title') or ''
            if re.match(r'^(关于|队伍编成|闲谈)', t): rel_k.append(v)
            elif re.search(r'战斗|受击|终结技|战技|秘技|回合|胜利|阵亡|无法战斗|弱点击破|危险|重开|回复生命|待机|战利品|解谜|发现|返回', t): battle_k.append(v)
            else: world_k.append(v)
        if world_k:
            ap('### 认知与日常')
            ap('')
            for v in world_k:
                ap(f"- **{v.get('Title','')}**：{v.get('Voice','')}")
            ap('')
        if rel_k:
            ap('### 关系与评价（他人实锤）')
            ap('')
            for v in rel_k:
                ap(f"- **{v.get('Title','')}**：{v.get('Voice','')}")
            ap('')
        if battle_k:
            ap('### 战斗语音')
            ap('')
            for v in battle_k:
                ap(f"- **{v.get('Title','')}**：{v.get('Voice','')}")
            ap('')

    if ts:
        ap('## 台词画像（剧情对话统计）')
        ap('')
        ap(f"- 剧情台词量：{ts['count']} 条")
        ap(f"- 平均句长：{ts['avg_len']} 字")
        ap(f"- 超短句（≤10字）占比：{ts['short_ratio']*100:.0f}%")
        if ts['top_words']:
            ap(f"- 高频词：{'、'.join(f'{k}×{v}' for k, v in ts['top_words'].items())}")
        ap('')

    rel = extract_relations(voices)
    if rel:
        names = sorted(set(r[0] for r in rel))
        ap('## 关系网络（语音标题实锤）')
        ap('')
        ap('、'.join(names))
        ap('')

    # ---- AI 角色扮演骨架 ----
    ap('## AI 角色扮演骨架（可直接用作 persona / system prompt 的素材）')
    ap('')
    style = []
    if ts:
        style.append(f"台词平均 {ts['avg_len']} 字，短句多" if ts['avg_len'] < 32 else "台词以中长句为主")
        if ts['short_ratio'] > 0.1: style.append(f"约 {ts['short_ratio']*100:.0f}% 的台词是不超过 10 字的短句")
    persona_brief = []
    if w.get('命途'): persona_brief.append(f"{w['命途']}命途")
    if w.get('派系'): persona_brief.append(w['派系'])
    if stories:
        persona_brief.append(f"官方角色故事 {len(stories)} 段（上文全文）")
    ap('### 角色卡')
    ap('')
    ap(f"- 姓名：{name}" + (f"（称号「{w.get('称号')}」）" if w.get('称号') else ''))
    if persona_brief: ap(f"- 身份：{'，'.join(persona_brief)}")
    if w.get('介绍'): ap(f"- 官方一句话：{w['介绍'].splitlines()[0][:80]}")
    if w.get('TAG'): ap(f"- 玩法关键词：{w['TAG']}")
    ap('')
    ap('### 语言风格建议（依据上方语音与统计数据）')
    ap('')
    if style:
        ap('- ' + '；'.join(style))
    ap('- 口癖与用词请从「语音全集」中归纳：优先复用角色原话里的语气词、称呼与习惯句式')
    ap('- 关系称呼参考「关系与评价」分组的原话')
    ap('')
    ap('### 对话规则（通用聊天平台适配）')
    ap('')
    ap('- 每次回复 1~3 句，保持角色原声；情绪越强句子越短')
    ap('- 不写括号旁白，不描述动作神态，情绪全部靠措辞与标点')
    ap('- 引用角色语音原话作为行为锚点，不要编造与官方设定冲突的内容')
    ap('- 与用户保持角色身份：不解释自己是 AI，除非对话明确要求')
    ap('')
    ap('### 开场示例（取自官方语音）')
    ap('')
    greet = [v for v in voices if (v.get('Title') or '') in ('初次见面','问候','闲谈 · 宇宙','闲谈')]
    for v in greet[:3]:
        ap(f"- **{v.get('Title','')}**：{v.get('Voice','')}")
    ap('')
    ap('---')
    ap(f'> 本档案由 hsr-personas 管线自动生成于游戏数据快照；文本版权归 miHoYo/HoYoverse 所有，仅供学习交流与社区二创，禁止商用。')
    return '\n'.join(lines)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--clean_dir', default='data')
    p.add_argument('--out_dir', default='personas')
    args = p.parse_args()

    roles = collect_game_roles(os.path.join(args.clean_dir, 'gd_角色技能.jsonl'))
    wiki = collect_wiki(os.path.join(args.clean_dir, '角色.jsonl'))
    avatars = collect_avatar_names(os.path.join(args.clean_dir, 'gd_Avatar.jsonl'))

    names = {}
    for key, g in roles.items():
        n = g.get('name') or (avatars.get(key) or {}).get('name')
        if n:
            names[key] = n
    print(f'游戏角色 {len(roles)} 个，其中已解析名字 {len(names)} 个')

    talks_path = os.path.join(args.clean_dir, 'textmap', 'SR_Talk_CH.json')
    if os.path.exists(talks_path):
        talk = talk_stats(talks_path, set(names.values()))
    else:
        talk = {}
        print('[提示] 未找到 textmap/SR_Talk_CH.json —— 台词画像模块跳过，'
              '其余模块不受影响（自备方式见 README「数据与复现」）')

    os.makedirs(args.out_dir, exist_ok=True)
    PATH_CN = {'Destruction':'毁灭','Hunt':'巡猎','Erudition':'智识','Harmony':'同谐','Nihility':'虚无','Preservation':'存护','Abundance':'丰饶','Remembrance':'记忆','Elation':'欢愉'}
    # 重名分组：同名字多 ID → 按命途加后缀；同命途多 ID（男女主）只生成第一份
    seen = set()
    made = 0
    for key, g in sorted(roles.items()):
        name = names.get(key)
        if not name or not g['stories'] or not g['voices']:
            print(f'[跳过] {key} {name or "（无名）"}：故事{len(g["stories"])} 语音{len(g["voices"])}')
            continue
        av = avatars.get(key, {})
        path_raw = av.get('path') or ''
        same_name = [k for k, gg in roles.items() if (gg.get('name') or (avatars.get(k) or {}).get('name')) == name]
        dup_group = len(same_name) > 1
        dup_path_group = sum(1 for k in same_name if (avatars.get(k) or {}).get('path') == path_raw) > 1
        sig = (name, path_raw)
        if dup_group and sig in seen:
            continue  # 同名同命途（男女主变体）内容一致，只取第一个
        seen.add(sig)
        file_name = name + (f' · {PATH_CN.get(path_raw, path_raw)}' if dup_group else '')
        w = wiki.get(name, {})
        # wiki 缺失字段用游戏数据兜底
        if not w.get('介绍') and av.get('desc'): w['介绍'] = av['desc']
        if not w.get('命途') and path_raw: w['命途'] = PATH_CN.get(path_raw, path_raw)
        if not w.get('元素属性') and av.get('element'): w['元素属性'] = {'Phys':'物理','Fire':'火','Ice':'冰','Lightning':'雷','Wind':'风','Quantum':'量子','Imaginary':'虚数'}.get(av['element'], av['element'])
        if not w.get('实装版本') and av.get('ver'): w['实装版本'] = av['ver']
        if not w.get('稀有度') and av.get('rarity'): w['稀有度'] = f"{av['rarity']}星"
        ts = talk.get(name)
        md = build_persona(name, key, g, w, ts)
        if dup_group:
            # 标题也带形态
            md = md.replace(f'# {name}（', f'# {name} · {PATH_CN.get(path_raw, path_raw)}（', 1)
        with open(os.path.join(args.out_dir, f'{file_name}.md'), 'w', encoding='utf-8') as f:
            f.write(md)
        made += 1
    print(f'生成 {made} 份人设 → {args.out_dir}/')

if __name__ == '__main__':
    main()
