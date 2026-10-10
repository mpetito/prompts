"""Condense a Claude Code session JSONL into a readable narrative plus stats.

usage: condense.py <session.jsonl> <out dir> <label>
Writes <label>-narrative.md, <label>-user-prompts.md and <label>-stats.md. Chunk the narrative at about
450K characters for one reader each; the reader brief is in ../references/reader-brief.md.
"""
import json, sys, collections, os, re
src, outdir, label = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(outdir, exist_ok=True)
stats = collections.Counter()
tools = collections.Counter()
agents = collections.Counter()          # (subagent_type, model)
skills = collections.Counter()
models = collections.Counter()
errors = []
denials = []
interrupts = 0
compactions = []
user_prompts = []
narrative = []
pr_links = []
def short(s, n):
    s = s if isinstance(s, str) else json.dumps(s)
    s = s.replace('\n', ' ⏎ ')
    return s if len(s) <= n else s[:n] + f'…[+{len(s)-n}]'
with open(src) as fh:
    for line in fh:
        try: d = json.loads(line)
        except Exception: stats['badline'] += 1; continue
        t = d.get('type')
        ts = (d.get('timestamp') or '')[:16].replace('T', ' ')
        if t == 'pr-link':
            pr_links.append((ts, d.get('prNumber'))); continue
        if t == 'system':
            st = d.get('subtype')
            stats[f'system:{st}'] += 1
            if st == 'compact_boundary' or d.get('compactMetadata'):
                compactions.append(ts)
                narrative.append(f'\n#### [{ts}] === COMPACTION === {short(d.get("content",""), 200)}\n')
            if d.get('hookErrors'):
                errors.append((ts, 'hook', short(d['hookErrors'], 300)))
            if d.get('level') == 'error' or st in ('api_error',):
                errors.append((ts, st, short(d.get('content', ''), 300)))
            continue
        if t == 'queue-operation':
            stats['queue:' + str(d.get('operation'))] += 1
            c = d.get('content') or ''
            if d.get('operation') == 'enqueue' and not c.startswith('<agent-message'):
                narrative.append(f'\n#### [{ts}] QUEUED USER INPUT: {short(c, 2000)}\n')
            continue
        if t not in ('user', 'assistant'):
            continue
        if d.get('isSidechain'): stats['sidechain'] += 1
        msg = d.get('message') or {}
        content = msg.get('content')
        if t == 'assistant':
            models[msg.get('model')] += 1
            if d.get('isApiErrorMessage') or d.get('apiErrorStatus'):
                errors.append((ts, 'api', short(d.get('error') or content, 300)))
            if isinstance(content, str):
                narrative.append(f'\n[{ts}] ASSISTANT: {content}\n'); continue
            for b in content or []:
                bt = b.get('type')
                if bt == 'text' and b.get('text', '').strip():
                    narrative.append(f'\n[{ts}] ASSISTANT: {b["text"]}\n')
                elif bt == 'tool_use':
                    name = b.get('name'); inp = b.get('input') or {}
                    tools[name] += 1
                    if name == 'Agent':
                        key = (inp.get('subagent_type') or 'default', inp.get('model') or 'unset')
                        agents[key] += 1
                        narrative.append(f'[{ts}] TOOL Agent type={key[0]} model={key[1]} desc={inp.get("description")!r} prompt={short(inp.get("prompt",""), 1500)}')
                    elif name == 'Skill':
                        skills[inp.get('skill')] += 1
                        narrative.append(f'[{ts}] TOOL Skill {inp.get("skill")} {short(inp.get("args",""),200)}')
                    elif name == 'Bash':
                        narrative.append(f'[{ts}] TOOL Bash: {short(inp.get("command",""), 400)}  # {inp.get("description","")}')
                    elif name in ('SendMessage',):
                        narrative.append(f'[{ts}] TOOL SendMessage to={inp.get("to")} {short(inp.get("message",""), 1200)}')
                    elif name in ('Read','Write','Edit'):
                        narrative.append(f'[{ts}] TOOL {name} {inp.get("file_path")} {short(inp.get("content") or inp.get("new_string") or "", 200)}')
                    else:
                        narrative.append(f'[{ts}] TOOL {name} {short(inp, 400)}')
        else:  # user
            if d.get('isCompactSummary'):
                narrative.append(f'\n#### [{ts}] === COMPACT SUMMARY ===\n{content if isinstance(content,str) else short(content, 20000)}\n')
                stats['compact_summary'] += 1; continue
            if d.get('toolDenialKind'):
                denials.append((ts, d.get('toolDenialKind')))
            if isinstance(content, str):
                if d.get('isMeta'): stats['user_meta'] += 1; continue
                if '[Request interrupted by user' in content:
                    interrupts += 1
                user_prompts.append((ts, content))
                narrative.append(f'\n#### [{ts}] USER: {content}\n')
                continue
            for b in content or []:
                bt = b.get('type')
                if bt == 'tool_result':
                    c = b.get('content')
                    if isinstance(c, list):
                        c = ' '.join(x.get('text', '') for x in c if isinstance(x, dict))
                    c = c or ''
                    is_err = b.get('is_error')
                    if is_err: stats['tool_error'] += 1
                    if '[Request interrupted by user' in c: interrupts += 1
                    narrative.append(f'[{ts}] RESULT{" ERROR" if is_err else ""}: {short(c, 700 if is_err else 350)}')
                elif bt == 'text':
                    txt = b.get('text', '')
                    if txt.startswith('<agent-message') or 'Subagent hand-back' in txt[:300]:
                        narrative.append(f'\n[{ts}] SUBAGENT REPORT: {short(txt, 2500)}\n'); stats['subagent_report'] += 1
                    elif txt.startswith('<system-reminder>') or txt.startswith('<local-command'):
                        stats['user_sysreminder'] += 1
                    else:
                        if '[Request interrupted by user' in txt: interrupts += 1
                        user_prompts.append((ts, txt))
                        narrative.append(f'\n#### [{ts}] USER: {txt}\n')
with open(f'{outdir}/{label}-narrative.md', 'w') as f:
    f.write('\n'.join(narrative))
with open(f'{outdir}/{label}-user-prompts.md', 'w') as f:
    for ts, p in user_prompts:
        f.write(f'\n### [{ts}]\n{p}\n')
with open(f'{outdir}/{label}-stats.md', 'w') as f:
    f.write(f'# {label}\n\nstats: {dict(stats)}\n\nmodels: {dict(models)}\n\ninterrupts: {interrupts}\n\ncompactions: {len(compactions)} {compactions}\n\nPR links: {len(pr_links)} unique {len(set(p for _,p in pr_links))}\n\n')
    f.write('## tools\n' + '\n'.join(f'{k}: {v}' for k, v in tools.most_common()) + '\n\n')
    f.write('## agents (type, model)\n' + '\n'.join(f'{k}: {v}' for k, v in agents.most_common()) + '\n\n')
    f.write('## skills\n' + '\n'.join(f'{k}: {v}' for k, v in skills.most_common()) + '\n\n')
    f.write('## denials\n' + '\n'.join(map(str, denials)) + '\n\n')
    f.write('## errors\n' + '\n'.join(map(str, errors)) + '\n')
print(label, 'narrative chars', sum(len(x) for x in narrative), 'user prompts', len(user_prompts))
