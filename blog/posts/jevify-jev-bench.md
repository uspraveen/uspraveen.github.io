# Jevify: Teaching Open Models to Answer in Probabilities

> **Jevify** is my open engine for turning ordinary open-weight LLMs into *System One* decision models - models that never write text, only return probabilities your code can branch on. **jev-bench** is the benchmark I built to check whether those probabilities can be trusted. This is what I found after scoring 46 models on 22,773 test questions - including the result I'm proudest of: fine-tuning made models contradict themselves, and one training penalty cut that roughly tenfold at no accuracy cost.

![jev-bench: every model, accuracy vs calibration](/images/jevify/accuracy-vs-ece.png)

## A model that doesn't talk

Most of what software asks an LLM is not "write me a paragraph." It is a decision. Which of these 77 intents is this support message? How helpful is this answer on a 0-4 scale? Is this comment toxic, yes or no?

We usually get those answers by making a model *generate* text and then parsing it. That throws away the most useful thing the model knows: how sure it is.

A System One model, the idea behind TypeSafe's [Jev](https://typesafe.ai), works differently. It reads a `state`, answers a typed question, and returns a probability distribution. No prose. The product promise is calibration: **an answer given 0.8 should be right about 80% of the time.** If that holds, you can put a threshold on it and build real software around it.

There are only three question types:

<div class="pipeline"><div class="pipeline-step"><span class="pipeline-num">01 / CHOICE</span><strong>Which of these K?</strong><span>Probabilities over options, e.g. 151 assistant intents.</span></div><div class="pipeline-step"><span class="pipeline-num">02 / SCORE</span><strong>Where on this scale?</strong><span>Probabilities over ordered levels, e.g. a 0-4 Likert rating.</span></div><div class="pipeline-step"><span class="pipeline-num">03 / NOUL</span><strong>Is this true?</strong><span>A single P(yes), e.g. is this SMS spam.</span></div><div class="pipeline-step"><span class="pipeline-num">04 / BRANCH</span><strong>Your code decides</strong><span>Route, gate, or escalate on the number itself.</span></div></div>

I wanted two things. First, an honest way to measure whether a decision model's numbers mean what they say. Second, to find out whether an open model I can run on my own GPUs could do the same job. Jevify is the second; jev-bench is the first.

## Building jev-bench

The rule I set myself: **real human-labeled data only, and keep human disagreement where it exists.** A calibration benchmark that only checks the argmax can't tell a model that is right and sure from one that is right by luck.

<div class="stat-grid"><div class="stat"><strong>166,054</strong><span>rows across train / val / test</span></div><div class="stat"><strong>22</strong><span>configs from real labeled datasets</span></div><div class="stat"><strong>22,773</strong><span>test records every model is scored on</span></div></div>

The 22 configs cover customer-support routing (Banking77, CLINC150, MASSIVE), legal clauses (LEDGAR), exam questions (MMLU, ARC), NLI, review ratings, LLM-judging (HelpSteer2), safety, fact-checking, spam and multi-hop QA. Every row is a `(state, question, label)` triple in exactly the wire format a System One model consumes, so you can send it straight to the API.

Four configs are what I call **calibration gold**: GoEmotions, Measuring Hate Speech, Civil Comments and ChaosNLI carry the actual *share* of human annotators behind each label. ChaosNLI has 100 crowdworkers per item. That lets me score a model not just against "the answer," but against how people actually split.

Six sources are held out of every training run, so I can tell real generalization from memorization.

## What I found when I measured Jev

I started by running Jev 1.13.0 through its API on every test record, one request each. Overall: **0.733 accuracy, ECE 0.113.**

On crisp, grounded questions it is excellent and calibrated: ARC at 0.979 with ECE 0.010, FEVER at 0.972. It's also fast in an interesting way - about 75 ms fixed plus 5.5 µs per input token, flat in the number of options. The answer is *read*, not decoded.

But on questions where humans disagree, its confidence stops carrying information.

![Jev's confidence vs accuracy across ChaosNLI agreement bands](/images/jevify/chaosnli-confidence.png)

On ChaosNLI, as human agreement goes from split to consensus, Jev's accuracy climbs from 0.47 to 0.96. Its confidence barely moves: 0.81, 0.84, 0.83, 0.88. The correlation is r = 0.046. It is more confident than the human majority on 80% of items.

<div class="pull-quote"><svg viewBox="0 0 24 24" fill="#ff5000"><path d="M7 7h4v4H8c0 2 1 3 3 3v3c-3 0-5-2-5-6V7zm8 0h4v4h-3c0 2 1 3 3 3v3c-3 0-5-2-5-6V7z"/></svg><div><p>A decision model's job is not just to be right. It is to know when it might not be.</p><cite>The question jev-bench is built around</cite></div></div>

## Jevify: climbing the ladder

Jevify takes an open checkpoint and "Jevifies" it in tiers, each one scored on the same records:

- **Tier 0** - no training. Read the model's own probabilities over the options (its *decision readout*) and fit a temperature on validation data only.
- **Tier 1** - decision heads trained with proper scoring rules, backbone frozen.
- **Tier 2** - LoRA under those heads.
- **Readout fine-tuning** - train the model on its own decision distribution, optionally with a coherence penalty (more on that below).

![Qwen3.5-4B through every Jevify tier](/images/jevify/qwen4b-ladder.png)

Following one model, Qwen3.5-4B, up the ladder: 0.662 untuned, 0.698 with residual heads, 0.747 with LoRA + heads, and 0.751 with readout fine-tuning plus coherence. Notice the last step barely moves accuracy (+0.008) - but look at the sure loss underneath it, from 0.283 to 0.029. That's the next section. Tier 0 alone is surprisingly strong: an untuned Gemma-4-12B-it with just a fitted temperature reaches 0.716 at ECE 0.086, better calibrated than Jev as served.

The held-out sources kept me honest. Early on, heads that *replaced* the model's own scorer gained +0.077 on trained sources and lost 0.098 on held-out ones. A zero-initialized residual on top of that scorer kept the gain and erased the regression. If I had held out records instead of whole sources, I would never have seen it.

## The bug nobody measures: models that contradict themselves

Here is the finding I'm proudest of.

A decision model is usually asked several related questions about the same input. Route it? Is it billing? Is it urgent? Suppose a model says a support message is **60% "billing"** in a three-way routing question, but only **45%** when you ask "is it billing?" directly. No single belief about the world produces both answers. The model has contradicted itself.

That has a sharp consequence. If you treated those probabilities as betting odds, a bettor could take one side of the first answer and the other side of the second and **win money no matter what the message turns out to be**. A classical result from de Finetti says such *incoherent* probabilities are never better: there is always a coherent set of answers that scores at least as well, whichever answer is right.

<div class="decision-panel"><div><strong>What sure loss measures</strong><span>For each family of related questions, the distance from the model's answers to the nearest set that could all be true together. Zero means perfectly consistent.</span></div><div><strong>Why accuracy misses it</strong><span>A model can be accurate and well calibrated on every question alone and still contradict itself across related ones. Only asking the family together exposes it.</span></div></div>

jev-bench builds **4,749 families** automatically from the test items: a choice question plus a yes/no for each option, a yes/no plus its negation, a rating plus "at least level k" thresholds. Then it measures the sure loss d².

When I trained models on their own readout with plain supervision, accuracy went up - and coherence collapsed. Each answer got sharper while its sibling questions drifted apart.

<div class="stat-grid"><div class="stat"><strong>0.151</strong><span>Qwen3.5-4B untuned</span></div><div class="stat"><strong>0.283 / 0.316</strong><span>after supervised readout fine-tune (LoRA / full)</span></div><div class="stat"><strong>0.029 / 0.024</strong><span>same, + coherence penalty</span></div></div>

So I added a coherence penalty to training: alongside learning the right answer, the model pays for any gap between its answers to related questions.

![Sure loss before and after the coherence penalty](/images/jevify/sure-loss.png)

It worked everywhere I tried it. Supervised readout fine-tuning roughly doubles sure loss (Qwen3.5-4B: 0.151 to 0.283). The penalty drives it to **0.024-0.031**, about ten times lower, and below Jev's 0.081. Accuracy didn't pay for it: Qwen3.5-4B went 0.743 to 0.751 with the penalty, the full fine-tune 0.752 to 0.757, Qwen3.5-2B 0.701 to 0.702, Gemma-4-E4B-it 0.737 to 0.742. Perplexity's hosted pplx-decider-v1-27b, for comparison, sits at 0.219 - the least coherent system I measured.

<div class="pull-quote"><svg viewBox="0 0 24 24" fill="#ff5000"><path d="M7 7h4v4H8c0 2 1 3 3 3v3c-3 0-5-2-5-6V7zm8 0h4v4h-3c0 2 1 3 3 3v3c-3 0-5-2-5-6V7z"/></svg><div><p>Coherence is what lets you ask a model once and rely on the answer. Fine-tuning for accuracy quietly breaks it; a coherence penalty gets it back for free.</p><cite>Sure loss 0.283 → 0.029 at 4B, accuracy 0.743 → 0.751</cite></div></div>

One caveat I want to be upfront about: sure loss is measured only on the relations my generator builds, and a model can be perfectly coherent and still wrong. That's why it sits next to accuracy and calibration, not instead of them.

## The results

<div class="stat-grid"><div class="stat"><strong>0.770</strong><span>best open accuracy (Jev: 0.733)</span></div><div class="stat"><strong>0.055</strong><span>its ECE (Jev: 0.113)</span></div><div class="stat"><strong>0.305</strong><span>TVD to human labels (Jev: 0.432)</span></div></div>

The top of the leaderboard is now open models Jevified with readout fine-tuning plus coherence:

| model | accuracy | ECE | TVD to humans |
|---|---|---|---|
| Qwen-AgentWorld-35B-A3B (≈3B active) | **0.770** | 0.055 | 0.305 |
| Qwen3.5-9B | 0.763 | 0.056 | 0.301 |
| Qwen3.5-4B | 0.751 | 0.058 | 0.303 |
| pplx-decider-v1-27b (hosted) | 0.748 | 0.080 | 0.378 |
| Gemma-4-E4B-it | 0.742 | 0.053 | 0.297 |
| **Jev 1.13.0 (API)** | 0.733 | 0.113 | 0.432 |

A 35B mixture-of-experts model with about 3B active parameters has the highest accuracy in the table, up from 0.709 untuned. The full fine-tune of Qwen3.5-4B with coherence reaches 0.757 accuracy, 0.802 on held-out sources and a sure loss of 0.024.

It also generalizes in ways I didn't train for. Readout fine-tuning cut injected-instruction hijacks from about 0.3 to about 0.1. And the same three primitives work on images: an untuned Qwen3-VL-2B answers POPE hallucination questions at 0.891 with ECE 0.046 after the recipe, in 68-79 ms on one A40.

## Where Jev still wins

I want this to be an honest benchmark, so here is where the open models are still behind:

- **The six held-out sources.** Jev scores 0.835 there, against 0.828 for my best open model (Perplexity's decider: 0.840).
- **Applying a rule written into the question.** On 885 LegalBench fact patterns, Jev applies the stated rule at 0.924. My best open model reaches 0.80; untrained and Tier 2 models sit at 0.62-0.70.
- **Rating scales.** The 35B gives back accuracy on yelp5 (62.3 → 52.2) and sst5 (56.7 → 52.2).

And one finding cuts the other way: on a community phishing benchmark someone else wrote, an untuned Gemma-4-12B beats Jev by twenty points (0.825 vs 0.628). Fine-tuned 4Bs, including my own, stopped flagging phishing - a moved threshold, which one shift fitted on sixteen labelled emails repairs.

## Try it

Everything is open:

- **Dataset:** [Praveenrajus/jev-bench](https://huggingface.co/datasets/Praveenrajus/jev-bench) - `load_dataset("Praveenrajus/jev-bench", "chaosnli", split="test")`
- **Engine:** [github.com/uspraveen/Jevify](https://github.com/uspraveen/Jevify) - metrics, runner, training recipes, and `jevify-serve`, a drop-in for the TypeSafe SDK
- **Models:** the [Jevified checkpoints](https://huggingface.co/Praveenrajus) on Hugging Face, from 2B to the 35B MoE, plus vision
- **Every finding with caveats:** [FINDINGS.md](https://github.com/uspraveen/Jevify/blob/main/docs/FINDINGS.md)

```python
from jevify import load_jevified

model = load_jevified("Praveenrajus/jevify-qwen3.5-4b-readout-full-coh")
model.ask({"text": "The battery lasted two days on a single charge."},
          {"q": {"type": "noul", "instructions": "Is the review positive?"}})
```

The thing I keep coming back to: a probability is only useful if it is *honest* - calibrated against reality, consistent with itself, and humble where people disagree. jev-bench is how I check that. Jevify is how I'm getting open models there.

<p class="source-note">All numbers are from the jev-bench dataset card (v0.1.1, built 2026-09-20) and the Jevify model cards on Hugging Face, measured on the 22,773 jev-bench test records unless noted. Several results are single seeds; see FINDINGS for intervals and caveats.</p>
