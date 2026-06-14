# WS4: Effective credibility under disclosure-truncation (theorem-gate result)

**Status: result CORRECT but RE-FRAMED after independent review** (R12). The closed
form is derivable and numerically validated to max |error| = 0.006, but the validated
quantity is a **posterior-precision / effective-sample-size ratio**, NOT the
Bühlmann–Straub credibility (data-weight) factor (the two coincide only in the
untruncated conjugate case). So this is an **information-deflation / effective-sample-size
result for the location parameter**, not a "credibility theorem." Realistic grade:
**IME/Variance-level (incremental: Jewell × textbook truncated-normal Fisher info ×
Laplace)**: ASTIN-grade ONLY if extended to the σ/tail and the loss-cost functional.
Do not call it a theorem or "exact credibility." Caveats below.

> **Independent-review corrections (2026-06):** (1) `Z=1−Var_post/Var_prior` is a
> variance-reduction ratio; the actual data-weight ∂E[θ|data]/∂Ȳ under truncation is >1,
> so "credibility" is the wrong word for the location. (2) The "validation" is partly an
> algebraic identity + Laplace check, not a test of a credibility claim. (3) Result is for
> θ; the loss cost is σ/tail-driven: wrong parameter for the stated estimand. (4) Novelty
> is framing only; δ(α) info-deflation is textbook (Tobit/Heckman) and credibility with
> truncated/deductible data exists (Klugman–Panjer–Willmot). Keep "to our knowledge" hedges.

## Setup

Per-line severity on the log scale. Target (AI) line: observations
`Y_1,…,Y_n ~ N(θ, σ²)` with σ² the within-line variance (known/fixed for this
result). Borrowed proxy prior (commensurate / Bühlmann–Straub form):
`θ ~ N(m₀, τ²)`, where m₀ is the proxy centre and τ² the between-line
(commensurability) variance. Larger τ² = weaker borrowing.

**Baseline (known: Jewell 1974; Diaconis–Ylvisaker 1979).** With no truncation,
the posterior is `θ|Y ~ N(Z·Ȳ + (1−Z)·m₀, …)` and

> **Z = nτ² / (nτ² + σ²) = n / (n + k), k = σ²/τ².**

This is *exact credibility*: the Bayes estimator is linear in Ȳ with the
Bühlmann–Straub factor Z. Verified numerically (no-truncation rows: Z_closed =
Z_numer to 0.000).

## Disclosure-truncation breaks exact credibility and deflates Z

Realistic loss data is **left-truncated at a disclosure threshold t** (8-K
materiality, court-filing minimums, regulator publication floors, R7): we observe
`Y_i` only when `Y_i > t`. The per-observation density becomes the truncated
normal `f(y|θ)/P(Y>t|θ)`, which is **not conjugate** to the normal prior, so strict linear (exact) credibility fails and the Bayes estimator is no longer linear in Ȳ.

What survives is a **local (Fisher-information) effective credibility**. The
truncated-normal score for θ is `(y−θ)/σ² − λ(α)/σ` with
`α = (t−θ)/σ`, `λ(α) = φ(α)/(1−Φ(α))` (inverse Mills ratio). Because the second
term is constant in y, the per-observation Fisher information is

> **I(θ; t) = (1 − δ(α)) / σ², δ(α) = λ(α)·(λ(α) − α) ∈ [0, 1).**

Truncation reduces mean-information by the factor (1 − δ(α)). A Gaussian
(Laplace) posterior then has precision `1/τ² + n·I(θ;t)`, giving the

> **Proposition (effective credibility under disclosure-truncation).**
> **Z_eff(t) = n_eff·τ² / (n_eff·τ² + σ²), n_eff = n·(1 − δ(α)),**
> evaluated at θ̂ (so Z_eff is a *local* credibility). As t → −∞, δ → 0,
> n_eff → n, and Z_eff → the Jewell/Bühlmann–Straub baseline Z.

**Numerical validation** (`validate_zeff.py`, grid posterior vs closed form,
θ=13.5, σ=2, m₀=13.5, τ=0.8): max |Z_closed − Z_numer| = **0.006** over
n∈{5,10,20,40} × truncation quantiles {0, .25, .5, .75}. The approximation is
excellent even at n=5.

## Corollary: the identifiability frontier in closed form

Z_eff = ½ ⟺ n_eff = σ²/τ², i.e.

> **n*(t) = (σ²/τ²) / (1 − δ(α)).**

Disclosure-truncation **inflates the data requirement** for the loss-cost-driving
parameter by the multiplicative factor **1/(1 − δ(α))**. Validated magnitudes
(τ=0.8, σ=2 ⇒ untruncated n*=6.25):

| truncation quantile | 1 − δ | n* (Z=0.5) | inflation |
|---|---|---|---|
| none | 1.000 | 6.2 | ×1.00 |
| 25th pct | 0.535 | 11.7 | ×1.87 |
| median | 0.363 | 17.2 | ×2.75 |
| 75th pct | 0.242 | 25.9 | ×4.14 |

This is the AI-relevant quantitative message: **the frontier is not fixed: the
disclosure threshold moves it by 2–4×.** It ties the abstract identifiability
frontier to the concrete public-record reality that small losses are never
disclosed.

## Heterogeneous source/target thresholds (the AI-specific piece)

If the proxy (source) line is censored at t_S and the AI (target) line at t_T, the
proxy contributes effective information `n₀·(1 − δ(α_S))` and the target
`n·(1 − δ(α_T))`. Borrowing is therefore **asymmetric in the two thresholds**: a
proxy line with a *lower* disclosure floor lends *more* effective credibility than
its raw count suggests. This heterogeneous-threshold credibility is, as far as the
WS-foundations research found, not in the existing credibility literature.

## Adaptive borrowing (combine with robust-MAP)

Under a robust-MAP mixture prior (Schmidli 2014) the borrowing self-attenuates
under prior–data conflict: Z_eff also becomes a decreasing function of the conflict
statistic |Ȳ−m₀| (demonstrated numerically in `model/frontier_sim.py`). The full
frontier is therefore a surface in **(n, conflict, truncation)**: conflict raises
n* via down-weighting; truncation raises it via the 1/(1−δ) factor.

## Honest verdict (R12)

**Tractable → pursue the ASTIN methods track.** Caveats, stated plainly so the
paper does not overclaim:

1. **Local, not strictly exact.** Truncation breaks Jewell exact credibility; the
 (1−δ) result is the Fisher-information/Laplace effective credibility, validated
 to <0.006 but formally a leading-order result (state as such).
2. **Location parameter.** Derived for θ (which, with σ, drives the loss cost).
 Extending cleanly to the σ/tail and the loss-cost functional E[X]=exp(θ+σ²/2),
 and to the GPD/heavy-tail (R9) regime, is the next increment.
3. **θ-dependence.** δ(α) depends on θ through α ⇒ Z_eff is evaluated at θ̂ (a local
 credibility), consistent with the adaptive framing.
4. **Novelty is modest but real.** The truncated-normal Fisher information is
 textbook; the *credibility-deflation framing*, the closed-form frontier
 n*=(σ²/τ²)/(1−δ), and the heterogeneous source/target-threshold borrowing are a
 novel synthesis for disclosure-censored loss data: distinct from Kim–Jeon
 (2013) trimming credibility (which trims observed data; here the data-generating
 process is truncated by disclosure). Strongest framed as *"exact credibility
 under disclosure-censoring and its identifiability frontier."*

**Track decision (revised post-review):** IME/Variance is the realistic central case
(the result is correct but incremental as a location effective-sample-size identity).
ASTIN becomes justified ONLY if the result is extended to the σ/tail and the loss-cost
functional E[X]=exp(θ+σ²/2): that extension is the single most important piece of
remaining work, and it likely wants an FCAS/FIA co-author (R2).
