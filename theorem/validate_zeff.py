"""
WS4 theorem-gate: numerical validation of the proposed closed-form result

  Z_eff(t) = n_eff * tau^2 / (n_eff * tau^2 + sigma^2),  n_eff = n * (1 - delta(alpha))

for the LOCATION credibility under left-truncation at disclosure threshold t,
where  alpha = (t - theta)/sigma,  lambda(alpha) = phi(alpha)/(1-Phi(alpha)),
       delta(alpha) = lambda(alpha) * (lambda(alpha) - alpha)   in [0,1).

Baseline (t -> -inf, delta -> 0): Z = n*tau^2/(n*tau^2 + sigma^2) = Jewell/Bühlmann-Straub.

We compare the CLOSED-FORM prediction to a deterministic grid posterior under the
truncated-normal likelihood with a normal (commensurate) prior. Agreement across
(n, truncation) confirms the result lands -> ASTIN methods track (R12).
"""
import numpy as np
from scipy import stats

THETA, SIGMA, M0, TAU = 13.5, 2.0, 13.5, 0.8   # truth, within-line sd, prior centre, prior sd
RNG = np.random.default_rng(1)
theta_grid = np.linspace(THETA - 8 * TAU, THETA + 8 * TAU, 1200)
dt = theta_grid[1] - theta_grid[0]


def delta(alpha):
    if not np.isfinite(alpha):
        return 0.0 if alpha < 0 else 1.0    # no truncation (-inf) -> no info loss
    lam = stats.norm.pdf(alpha) / stats.norm.sf(alpha)
    return lam * (lam - alpha)


def n_eff(n, t):
    a = (t - THETA) / SIGMA
    return n * (1.0 - delta(a))


def Z_closed_form(n, t):
    ne = n_eff(n, t)
    return ne * TAU**2 / (ne * TAU**2 + SIGMA**2)


def Z_numerical(n, t, reps=400):
    var_prior = TAU**2
    zs = []
    for _ in range(reps):
        ys = []
        while len(ys) < n:                       # draw observed (Y>t) sample
            d = RNG.normal(THETA, SIGMA, size=6 * n)
            ys.extend(d[d > t].tolist())
        y = np.array(ys[:n])
        # truncated-normal log-lik over theta_grid
        z = (y[None, :] - theta_grid[:, None]) / SIGMA
        ll = (stats.norm.logpdf(z) - np.log(SIGMA)).sum(axis=1)
        if np.isfinite(t):
            ll = ll - n * stats.norm.logsf((t - theta_grid) / SIGMA)   # truncation normaliser
        post = np.exp(ll - ll.max()) * stats.norm.pdf(theta_grid, M0, TAU)
        post /= post.sum() * dt
        m = (theta_grid * post).sum() * dt
        v = ((theta_grid - m) ** 2 * post).sum() * dt
        zs.append(1.0 - v / var_prior)
    return float(np.mean(zs))


if __name__ == "__main__":
    print(f"theta={THETA} sigma={SIGMA} m0={M0} tau={TAU}")
    print(f"baseline k = sigma^2/tau^2 = {SIGMA**2/TAU**2:.2f}  (Z=0.5 at n=k, no truncation)\n")
    quantiles = [0.0, 0.25, 0.5, 0.75]   # left-truncation quantile of the AI distribution
    print(f"{'n':>4} {'trunc q':>8} {'alpha':>7} {'1-delta':>8} {'n_eff':>7} "
          f"{'Z_closed':>9} {'Z_numer':>9} {'|diff|':>7}")
    maxdiff = 0.0
    for q in quantiles:
        t = -np.inf if q == 0 else THETA + stats.norm.ppf(q) * SIGMA
        a = (t - THETA) / SIGMA if np.isfinite(t) else -np.inf
        omd = 1.0 - (delta(a) if np.isfinite(a) else 0.0)
        for n in (5, 10, 20, 40):
            zc, zn = Z_closed_form(n, t), Z_numerical(n, t)
            d_ = abs(zc - zn); maxdiff = max(maxdiff, d_)
            print(f"{n:>4} {q:>8.2f} {(a if np.isfinite(a) else float('-inf')):>7.2f} "
                  f"{omd:>8.3f} {n_eff(n,t):>7.2f} {zc:>9.3f} {zn:>9.3f} {d_:>7.3f}")
    print(f"\nMAX |closed-form - numerical| across all cells: {maxdiff:.3f}")
    print("VERDICT:", "LANDS — closed-form matches numerics (ASTIN track)" if maxdiff < 0.03
          else "does NOT match — investigate / applied (IME) track")
    # frontier: n* = (sigma^2/tau^2)/(1-delta) — truncation inflates required n
    print("\nFrontier n*(Z=0.5) = (sigma^2/tau^2)/(1-delta):")
    for q in quantiles:
        t = -np.inf if q == 0 else THETA + stats.norm.ppf(q) * SIGMA
        a = (t - THETA) / SIGMA if np.isfinite(t) else -np.inf
        omd = 1.0 - (delta(a) if np.isfinite(a) else 0.0)
        print(f"  trunc q={q:.2f}: n* = {(SIGMA**2/TAU**2)/omd:.1f}  "
              f"(inflation x{1/omd:.2f} vs untruncated)")
