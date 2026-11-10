#!/usr/bin/env python3
"""Definition-fit scoring via a pretrained Hebrew transformer, as a SECOND, independent
re-ranker alongside solver/deffit.py — not a replacement for it.

WHY (queue item 9, DAILY.md's standing "sharpest gap"): `deffit.py` (built 2026-09-09,
extended 2026-09-10/10-07/10-20) scores a candidate by BM25 lexical overlap between the
clue's text and a corpus-attested gloss of the candidate (private_defs + fillbank.json).
Across FOUR independent measurements on real puzzles (2026-09-09, 09-10, 10-07, 10-20,
all in DAILY.md), one structural number never moved: `nonretrieval_scored_clues` — among
clues where a MECHANICAL (anagram/hidden/reversal/homograph/substitution/container)
candidate is on the table, the share that ALSO gets a non-zero def_fit score — stayed at
0/28 every single time, even after widening the pool 8x (10-20) and adding a second gloss
source (09-10). The diagnosed reason (deffit.py's own docstring): BM25 needs the clue's
and the gloss's TOKENS to overlap. A mechanical candidate's real-word meaning often has
nothing to do with the clue's own vocabulary (that is the whole point of e.g. a homograph
device: "the singer" and שרה share zero letters and zero likely corpus tokens), so lexical
overlap can structurally never fire there, independent of corpus size.

This module asks the same question — does the candidate's MEANING fit the clue, not just
its letters — with a signal that does not require shared vocabulary: cosine similarity
between dense embeddings from AlephBERT (biu-nlp/alephbert-base, HuggingFace), a
general-purpose Hebrew BERT. Two prior research passes (2026-08-24/08-25, RESEARCH.md)
checked Hebrew WordNet for this role and judged it real but wrong-shaped (a synonymy
resource, not a role-category one) and found no Hebrew embedding space "tuned for this
genre." Neither pass checked a general-purpose Hebrew transformer for this; this run did
(confirmed reachable from this sandbox with no auth). It is NOT tuned for crosswords and
may not transfer any better than BM25 did — see evalrerank() for the measured answer, not
an assumption either way.

Deliberately kept as a SEPARATE module from deffit.py rather than grafted in, for the
same reason PR #103's consolidation kept defspan.py's two independent lineages separate
and disclosed rather than silently merged: this is a genuinely different kind of signal
(dense, uncalibrated cosine similarity vs. sparse BM25 with its own IDF dampening), on a
heavy optional dependency deffit.py does not otherwise need, so folding it into
`def_fit_score`'s cross-source max() would require inventing a cross-scale calibration
this run has no basis for and did not attempt. The two scores are reported and compared
side by side, never combined, so neither file's existing numbers can regress from this
one's existence.

RE-RANKER, NOT GENERATOR: like deffit.py, this never invents a candidate — it only
re-scores what candidates.py already produced. recall@N over the result is therefore
identical to recall@N over the input by construction (see selftest).

SAFETY PROPERTY: a frozen pretrained model never saw this project's gold answers at any
point (no fine-tuning on our data, no held-out filtering needed) — unlike every
corpus-built tool elsewhere in this project, there is no leak vector here at all.

DEPENDENCY, disclosed rather than silently assumed: `pip install torch transformers`
(a CPU build is enough; the model is ~440MB, fetched once from HuggingFace and cached
under ~/.cache/huggingface). NOT part of bootstrap.sh — that script's contract is a
fully-scriptable rebuild of data/, and this is a heavy, optional model dependency, not a
data asset; it is reconstructible from the public model id named here instead. Every
function that needs the model raises a clear, actionable RuntimeError if the packages
are missing rather than failing obscurely.

CLI:
  python3 solver/embed_fit.py score "<clue text>" <candidate>
  python3 solver/embed_fit.py rerank "<clue text>" <cand1> <cand2> ...
  python3 solver/embed_fit.py eval data/dataset/clues.jsonl eval   # see evalrerank()
  python3 solver/embed_fit.py selftest
"""
import sys, os, re, json
from functools import lru_cache

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIN = str.maketrans('ךםןףץ', 'כמנפצ')
MODEL_ID = 'biu-nlp/alephbert-base'


def norm(s):
    return re.sub(r'[^א-ת]', '', s or '').translate(FIN)


def strip_credit(text):
    """Drop a trailing (עפ"י <name>) contributor credit — it names who submitted the
    clue, never part of its wordplay or definition (SOLVE_PROTOCOL.md)."""
    return re.sub(r'\(עפ["״]?י[^)]*\)', '', text or '').strip()


_MODEL = None


def _load():
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    try:
        import torch
        from transformers import AutoTokenizer, AutoModel
    except ImportError as e:
        raise RuntimeError(
            "embed_fit.py needs torch+transformers (pip install torch transformers; "
            "a CPU-only torch build is enough). See this module's docstring.") from e
    tok = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModel.from_pretrained(MODEL_ID)
    model.eval()
    _MODEL = (tok, model, torch)
    return _MODEL


@lru_cache(maxsize=4096)
def embed(text):
    """Mean-pooled last hidden state for `text`. Cached: a clue's embedding is computed
    once and reused across every candidate scored against it."""
    tok, model, torch = _load()
    with torch.no_grad():
        enc = tok(text, return_tensors='pt', truncation=True, max_length=64)
        out = model(**enc)
        vec = out.last_hidden_state.mean(dim=1).squeeze(0)
    return vec


def score(clue_text, candidate):
    """Cosine similarity between the clue's (credit-stripped) surface and one candidate
    word. Higher = more related in this model's training distribution. NOT calibrated
    against deffit.py's def_fit scale or any fixed threshold — only meaningful as a
    RANKING among candidates for the same clue, which is all rerank()/evalrerank() use
    it for. (BERT embeddings are known to sit in a narrow cosine band regardless of
    relatedness — "anisotropy" — so do not read an absolute value as "similar" vs.
    "unrelated"; only the ORDER across candidates for one clue is meaningful here.)"""
    _, _, torch = _load()
    import torch.nn.functional as F
    a = embed(strip_credit(clue_text))
    b = embed(candidate)
    return F.cosine_similarity(a, b, dim=0).item()


def rerank(clue_text, cands):
    """Stable-sorts candidate dicts (candidates.py's own shape, each with an 'answer'
    key) by embed_fit score, descending; ties preserve candidates.py's own
    mechanism-priority order. Returns NEW dicts (each carries an 'embed_fit' key);
    never mutates the input or drops/adds a candidate."""
    scored = [(score(clue_text, c['answer']), i, c) for i, c in enumerate(cands)]
    scored.sort(key=lambda x: (-x[0], x[1]))
    out = []
    for s, _i, c in scored:
        c2 = dict(c)
        c2['embed_fit'] = s
        out.append(c2)
    return out


NON_RETRIEVAL_MECHANISMS = {
    'anagram', 'hidden', 'reversal', 'homograph', 'homophone', 'homophone_vowel',
    'substitution', 'container', 'charade', 'culture_category', 'pattern',
}


# ---------------------------------------------------------------------------
# diagnostic, metric names deliberately matching deffit.py's eval_rerank() so the two
# re-rankers' numbers on the same puzzle are directly comparable, not just similarly
# shaped. Conditional on recall@N (gold already in candidates.generate()'s pool) —
# gold is used only to SCORE the outcome after generation, never to generate.
# ---------------------------------------------------------------------------
def evalrerank(dataset_path, split=None, max_n=25):
    sys.path.insert(0, HERE)
    import candidates as cand_mod

    total = recall_hit = 0
    base_top1 = base_rr = rerank_top1 = rerank_rr = 0
    moved_up = moved_down = unchanged = 0
    nr_recall_hit = nr_base_top1 = nr_rerank_top1 = 0
    examples = []
    for line in open(dataset_path):
        r = json.loads(line)
        if split and r.get('split') != split:
            continue
        if not r.get('answer_raw'):
            continue
        total += 1
        cands = cand_mod.generate(r['clue_text'], r['enum'], max_n=max_n)
        gold = cand_mod.norm(r['answer_raw'])
        answers = [c['answer'] for c in cands]
        base_rank = answers.index(gold) + 1 if gold in answers else None
        if base_rank is None:
            continue
        recall_hit += 1
        reranked = rerank(r['clue_text'], cands)
        re_rank = [c['answer'] for c in reranked].index(gold) + 1
        base_top1 += base_rank == 1
        rerank_top1 += re_rank == 1
        base_rr += 1.0 / base_rank
        rerank_rr += 1.0 / re_rank
        if re_rank < base_rank:
            moved_up += 1
        elif re_rank > base_rank:
            moved_down += 1
        else:
            unchanged += 1
        # the motivating question (see module docstring): deffit.py's BM25 signal
        # has never once scored a NON-retrieval-mechanism candidate above zero
        # (nonretrieval_scored_clues, 0/28 across 4 measurements) because lexical
        # overlap can't fire without shared vocabulary. Break this clue's gold hit
        # out by WHICH mechanism found it, so that specific case is visible rather
        # than averaged away by the retrieval-mechanism hits that dominate recall@N.
        gold_mechanism = next(c['mechanism'] for c in cands if c['answer'] == gold)
        if gold_mechanism in NON_RETRIEVAL_MECHANISMS:
            nr_recall_hit += 1
            nr_base_top1 += base_rank == 1
            nr_rerank_top1 += re_rank == 1
        examples.append((r['clue_number'], r['direction'], gold, gold_mechanism,
                          base_rank, re_rank))
    return {
        'total': total, 'recall_hit': recall_hit,
        'base_top1': base_top1, 'rerank_top1': rerank_top1,
        'base_mrr': base_rr / recall_hit if recall_hit else 0.0,
        'rerank_mrr': rerank_rr / recall_hit if recall_hit else 0.0,
        'moved_up': moved_up, 'moved_down': moved_down, 'unchanged': unchanged,
        'nr_recall_hit': nr_recall_hit, 'nr_base_top1': nr_base_top1,
        'nr_rerank_top1': nr_rerank_top1,
        'examples': examples,
    }


# ---------------------------------------------------------------------------
def selftest():
    """Checks against a live AlephBERT download — no dev/eval gold data is embedded in
    this file (same discipline as every other module here), but unlike those modules
    this one needs no held-out filtering at all: it never trains on anything, so there
    is nothing of this project's to leak. Requires network access to fetch the model
    once; if torch/transformers aren't installed, this fails loudly with install
    instructions rather than silently skipping."""
    ok = True

    print('--- strip_credit: drops a trailing contributor credit, keeps the clue text ---')
    stripped = strip_credit('משהו כלשהו (עפ"י יוסי קאופמן)')
    print(f'  {stripped!r} (expected no credit)')
    ok &= 'קאופמן' not in stripped

    print("--- score: a clue naming a role ranks the matching homograph above an "
          "unrelated word (PLAYBOOK.md/SOLVE_PROTOCOL.md's canonical שרה example) ---")
    s_match = score('מי שרה בבוקר', 'שרה')
    s_other = score('מי שרה בבוקר', 'שולחן')
    print(f'  sim(clue, שרה)={s_match:.3f}  sim(clue, שולחן)={s_other:.3f} '
          f'(expected שרה higher)')
    ok &= s_match > s_other

    print('--- rerank: promotes the matching candidate, never drops or adds one '
          '(recall@N over the result is unchanged by construction) ---')
    cands = [
        {'answer': 'שולחן', 'mechanism': 'anagram', 'fodder': 'x'},
        {'answer': 'מכונית', 'mechanism': 'hidden', 'fodder': 'y'},
        {'answer': 'שרה', 'mechanism': 'pattern', 'fodder': 'z'},
    ]
    out = rerank('מי שרה בבוקר', cands)
    print(f'  first candidate after rerank: {out[0]["answer"]} (expected שרה)')
    ok &= out[0]['answer'] == 'שרה'
    same_set = {c['answer'] for c in cands} == {c['answer'] for c in out}
    print(f'  same answer set and count before/after: '
          f'{same_set and len(cands) == len(out)} (expected True)')
    ok &= same_set and len(cands) == len(out)
    print(f'  embed_fit key attached to every candidate: '
          f'{all("embed_fit" in c for c in out)} (expected True)')
    ok &= all('embed_fit' in c for c in out)

    print(f'\n{"ALL PASSED" if ok else "FAILURES ABOVE"}')
    return ok


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == 'score':
        print(f'{score(sys.argv[2], norm(sys.argv[3])):.4f}')
    elif cmd == 'rerank':
        clue = sys.argv[2]
        cands = [{'answer': norm(c), 'mechanism': 'cli', 'fodder': None}
                  for c in sys.argv[3:]]
        for c in rerank(clue, cands):
            print(f'{c["embed_fit"]:.4f}\t{c["answer"]}')
    elif cmd == 'eval':
        path, split = sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None
        res = evalrerank(path, split)
        print(f"total clues: {res['total']}   recall_hit: {res['recall_hit']}")
        print(f"base_top1: {res['base_top1']}   rerank_top1: {res['rerank_top1']}")
        print(f"base_mrr: {res['base_mrr']:.3f}   rerank_mrr: {res['rerank_mrr']:.3f}")
        print(f"moved_up: {res['moved_up']}   moved_down: {res['moved_down']}   "
              f"unchanged: {res['unchanged']}")
        print(f"non-retrieval-mechanism gold hits: {res['nr_recall_hit']}   "
              f"base_top1: {res['nr_base_top1']}   rerank_top1: {res['nr_rerank_top1']}")
        for row in res['examples']:
            print(' ', row)
    elif cmd == 'selftest':
        sys.exit(0 if selftest() else 1)
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    os.chdir(ROOT)
    main()
