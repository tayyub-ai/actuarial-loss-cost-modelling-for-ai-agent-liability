# Labelling Protocol: AI-Agent Liability Severity Dataset

Encodes the locked requirements R8 (severity quantity), R13 (governance), R17
(inclusion boundary). Every datum in the released dataset must satisfy this protocol.
The dataset is CC-BY-SA 4.0 (derived from AIID/AIAAIC); attribute and share alike.

## 1. Inclusion boundary (R17): decide FIRST, per incident

**INCLUDE** only third-party **economic-loss** liability from an AI agent acting in a
**professional / commercial-service role**: i.e. the AI advises, informs, generates
content, interacts with customers, or supports a decision *on the deploying firm's
behalf toward a third party*, and that failure causes economic loss.

**EXCLUDE:**
- **Bodily injury / property damage** (autonomous vehicles, robotics, physical harm) →
 casualty/product lines, different actuarial world.
- **Systemic financial-market events** (algo-trading flash crashes) → correlated,
 fat-tailed, out of scope.
- Pure bias/discrimination *harm* with no economic-loss claim attached.
- First-party losses (the deployer's own loss with no third-party claimant).

Decision field: `economic_loss_3p` (Y/N), `professional_service` (Y/N). Include only if
both Y. Record a one-line `inclusion_reason`.

*Worked example:* Moffatt v. Air Canada (chatbot gave wrong fare advice → consumer
economic loss → tribunal award): INCLUDE, type = award.

## 2. Loss-type taxonomy (R8): never pool types

Each incident is assigned **exactly one** typed figure. Types are NOT commensurable and
are NEVER combined into a single "severity" number:

| type | definition | role |
|---|---|---|
| **indemnity** | amount the insurer/defendant actually paid to the claimant | **primary estimand** |
| **settlement** | negotiated settled amount (paid/agreed) | **primary estimand** (pooled with indemnity) |
| **award_judgment** | court/tribunal-ordered damages (pre-appeal) | separate stratum |
| **fine_penalty** | regulator/statutory fine | separate stratum (NOT a tort indemnity) |
| **demand** | amount sought by plaintiff (not paid) | separate stratum (upward-biased) |

**Rule:** the headline severity model uses only `indemnity`/`settlement`. Awards, fines,
demands are reported as separate strata for transparency and as measurement-error inputs,
never merged into the priced quantity. If only a demand/award exists, record it with its
true type: do NOT relabel it as a settlement.

## 3. Figure rules

- Record the figure in its **original currency and year** (`amount_orig`, `currency`,
 `loss_year`). Conversion to a common USD-year base happens downstream (documented),
 not at labelling.
- If multiple figures appear, choose the **single best-documented paid/settled amount**;
 if none paid, the award; record which and why in `figure_basis`.
- Reject press-reported "could cost up to $X" maxima, analyst estimates, company
 valuations, funding rounds, user counts: these are NOT losses. (The automated screen
 over-captures these; the human verifier must discard them.)
- Every figure needs a **direct public-record source** for that specific number
 (`figure_source_url`): court record, regulator notice, 8-K/SEC filing, or a primary
 news report citing one. AIID report text alone is not sufficient if it doesn't cite the
 figure's origin.

## 4. Governance (R13)

- **Public-record, on-the-record only.** No sealed/confidential settlement amounts.
- **Per-datum citation:** `figure_source_url` mandatory for every included figure.
- **Sensitive figures:** if a named defendant's figure is contested or could be defamatory
 if wrong, either confirm against a second primary source or aggregate/anonymise.
- **Disclaimer** ships with the dataset; academic fair use; CC-BY-SA attribution to AIID/AIAAIC.

## 5. Verifier workflow

1. Open `data/derived/verification_sheet.csv` (one row per automated candidate).
2. For each row: read the `money_snippets` (context around each $ mention) and open the
 `source_urls` + the AIID `incident_url`.
3. Apply §1 inclusion → set `economic_loss_3p`, `professional_service`, `include_final`.
4. If included: apply §2–§3 → fill `loss_type_verified`, `amount_orig`, `currency`,
 `loss_year`, `figure_basis`, `figure_source_url`, `notes`.
5. Leave excluded rows with `include_final=N` and a one-line reason.

**Quality (elite bar):** a second rater independently verifies a random ~20% sample;
report inter-rater agreement (Cohen's κ) on `include_final` and `loss_type_verified`.

## 6. Output

Verified rows with `include_final=Y` form `data/derived/severity_dataset.csv` (the
released, per-datum-sourced dataset). Report counts **by stratum** (indemnity/settlement
vs award vs fine vs demand) and **stratified + pooled** per R17: never a single pooled n.
