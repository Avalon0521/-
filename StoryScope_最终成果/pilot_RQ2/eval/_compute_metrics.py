import re, json

rounds = ['round0','round1','round2','round3']
results = {}
for r in rounds:
    combined = ''
    per_ch = {}
    for ch in ['ch1','ch2']:
        path = f'../{r}/{ch}.txt'
        s = open(path, encoding='utf-8').read()
        content_chars = re.sub(r'[\s\W]', '', s)
        per_ch[ch] = {'raw_len': len(s), 'content_chars': len(content_chars)}
        combined += content_chars
    distinct_ratio = len(set(combined)) / len(combined) if combined else 0
    bigrams = [combined[i:i+2] for i in range(len(combined)-1)]
    bigram_distinct_ratio = len(set(bigrams)) / len(bigrams) if bigrams else 0
    results[r] = {
        'per_chapter_content_chars': {k: v['content_chars'] for k,v in per_ch.items()},
        'per_chapter_raw_len': {k: v['raw_len'] for k,v in per_ch.items()},
        'combined_content_chars': len(combined),
        'distinct_char_ratio': round(distinct_ratio,4),
        'distinct_bigram_ratio': round(bigram_distinct_ratio,4),
    }

print(json.dumps(results, ensure_ascii=False, indent=2))
