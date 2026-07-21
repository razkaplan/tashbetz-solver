#!/usr/bin/env python3
"""Export SFT chat-format dataset (train split only) for small-model fine-tuning (Track B).

Output: data/dataset/sft.jsonl — one {"messages": [...]} per clue, MLX-LoRA compatible.
"""
import json

SYS = ('אתה פותר תשבצי היגיון בעברית בסגנון יורם הרועה (הארץ). '
       'קבל הגדרה ומבנה אותיות, החזר את הפתרון והסבר קצר של המנגנון.')

def main():
    n = 0
    with open('data/dataset/sft.jsonl', 'w') as out:
        for line in open('data/dataset/clues.jsonl'):
            r = json.loads(line)
            if r['split'] != 'train' or not r['answer_raw'] or not r['len_ok']:
                continue
            enum = ','.join(map(str, r['enum']))
            expl = r['explanations_crowd'][0] if r['explanations_crowd'] else ''
            user = f"הגדרה: {r['clue_text']} ({enum})"
            asst = f"פתרון: {r['answer_raw']}" + (f"\nהסבר: {expl}" if expl else '')
            out.write(json.dumps({'messages': [
                {'role': 'system', 'content': SYS},
                {'role': 'user', 'content': user},
                {'role': 'assistant', 'content': asst},
            ]}, ensure_ascii=False) + '\n')
            n += 1
    print('wrote', n, 'SFT examples')

if __name__ == '__main__':
    main()
