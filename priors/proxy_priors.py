"""
WS2 — Proxy-line severity priors for credibility borrowing (R5, R9).

Encodes PUBLISHED, FREELY-CITABLE severity summary statistics from cyber /
operational-risk proxy lines into lognormal severity priors on the log-dollar
scale, plus a heavy-tail (GPD) sensitivity alternative (R9). These are the
BORROWING SOURCES for the AI-agent liability severity model.

Sources (all open / citable; NO paywalled raw data used — R14):
  - Cremer et al. 2023, J. Cybersecurity 9(1):tyac016 (OA; arXiv 2202.10189)
      aggregate cyber: median ~$0.11M, mean ~$16.84M
  - Malavasi et al. 2021, arXiv 2111.03366, Table 2 (left-truncated exceedance,
      threshold u in $M): per-category cyber severity -> 3 distinct sub-lines
  - Eling & Jung 2022, Risk Management (PMC9169022): financial-industry op-risk,
      losses > $100k (disclosure floor), Tweedie p=1.9 best fit
  - Farkas, Lopez & Thomas 2021, IME 98:92-105 (open HAL hal-02118080): GPD/EVT
      tail template -> motivates the R9 GPD sensitivity bracket

Lognormal moment-matching: for X~Lognormal(mu,sigma) on $,
    median = exp(mu)             -> mu    = ln(median)
    mean   = exp(mu+sigma^2/2)   -> sigma = sqrt(2*(ln(mean)-ln(median)))
"""
from dataclasses import dataclass, field
import numpy as np


@dataclass
class ProxySubline:
    key: str
    label: str
    source: str
    median_musd: float          # published median, $M
    mean_musd: float            # published mean, $M
    trunc_u_musd: float | None  # left-truncation/disclosure threshold, $M (R7)
    n: int | None = None
    mu_log: float = field(init=False)     # lognormal mu on $ scale
    sigma_log: float = field(init=False)  # lognormal sigma

    def __post_init__(self):
        med = self.median_musd * 1e6
        mean = self.mean_musd * 1e6
        if not (mean > med > 0):
            raise ValueError(f"{self.key}: need mean>median>0 for lognormal fit")
        self.mu_log = np.log(med)
        self.sigma_log = np.sqrt(2.0 * (np.log(mean) - np.log(med)))

    # reconstructed moments (verification #2 in the plan)
    def fitted_median_musd(self):
        return np.exp(self.mu_log) / 1e6

    def fitted_mean_musd(self):
        return np.exp(self.mu_log + 0.5 * self.sigma_log**2) / 1e6


# >=3 distinct economic-loss sub-lines (R5), each a real published profile.
SUBLINES = [
    ProxySubline("privacy_disclosure", "Privacy: unauthorized contact/disclosure",
                 "Malavasi 2021 T2", median_musd=2.92, mean_musd=9.49, trunc_u_musd=0.63, n=530),
    ProxySubline("data_breach", "Data: malicious breach",
                 "Malavasi 2021 T2", median_musd=0.94, mean_musd=28.96, trunc_u_musd=0.63, n=619),
    ProxySubline("identity_fraud", "Identity: fraudulent use",
                 "Malavasi 2021 T2", median_musd=0.16, mean_musd=1.83, trunc_u_musd=0.63, n=375),
]

# Cross-check / aggregate references (not sub-lines; used for hyper-prior centring)
AGGREGATES = [
    ProxySubline("cyber_aggregate", "Cyber aggregate (Advisen)",
                 "Cremer 2023", median_musd=0.11, mean_musd=16.84, trunc_u_musd=None),
    ProxySubline("oprisk_financial", "Financial-industry op-risk (>$100k)",
                 "Eling & Jung 2022", median_musd=1.10, mean_musd=24.953, trunc_u_musd=0.10, n=2186),
]

# R9 GPD heavy-tail sensitivity bracket. The cyber literature is split on
# lognormal vs heavy/infinite-mean tails (Eling-Ibragimov-Ning 2025), so the
# prior MUST accommodate GPD tails. Shape xi in (0,1) => finite mean; xi>=1 =>
# infinite mean. We bracket xi over a defensible range for sensitivity analysis.
GPD_TAIL_BRACKET = dict(xi_grid=(0.3, 0.6, 0.9), threshold_musd=1.0,
                        note="Farkas 2021 EVT/GPD template (hal-02118080)")


def hyperprior_center():
    """Centre + spread for the shared (hyper) log-severity level, pooled across
    sub-lines. Returns (mu0, between_sd) on the log-$ scale."""
    mus = np.array([s.mu_log for s in SUBLINES])
    return float(mus.mean()), float(mus.std(ddof=1))


def lognormal_prior_params():
    return {s.key: dict(mu_log=s.mu_log, sigma_log=s.sigma_log,
                        trunc_log=(np.log(s.trunc_u_musd * 1e6) if s.trunc_u_musd else None),
                        source=s.source) for s in SUBLINES}


if __name__ == "__main__":
    print(f"{'sub-line':<42}{'mu_log':>8}{'sig_log':>8}{'med✓':>9}{'mean✓':>10}  source")
    for s in SUBLINES + AGGREGATES:
        tag = "  [SUBLINE]" if s in SUBLINES else "  (xcheck)"
        print(f"{s.label:<42}{s.mu_log:>8.2f}{s.sigma_log:>8.2f}"
              f"{s.fitted_median_musd():>8.2f}M{s.fitted_mean_musd():>9.2f}M  {s.source}{tag}")
    mu0, bsd = hyperprior_center()
    print(f"\nHyper (shared) log-severity centre: mu0={mu0:.2f}  between-subline sd={bsd:.2f}")
    print(f"  -> exp(mu0) = ${np.exp(mu0)/1e6:.2f}M  (pooled median proxy)")
    print(f"R9 GPD tail bracket: xi in {GPD_TAIL_BRACKET['xi_grid']} "
          f"(xi>=1 => infinite mean); threshold ${GPD_TAIL_BRACKET['threshold_musd']}M")
    print("\nVERIFICATION: fitted med/mean columns must match the published inputs.")
