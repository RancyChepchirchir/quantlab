# QuantLab Research Journal

**Project:** QuantLab - Computational Finance & Scientific Machine Learning Workstation  
**Owner:** Rancy Chepchirchir  
**Journal checkpoint:** 2 September 2026  
**Status:** Active research project / portfolio-ready

---

## Why this journal exists

This file is the long-term memory of QuantLab: what has been built, why key design decisions were made, which scientific claims are safe to make, what failed, what was fixed, and what future versions should explore. The goal is that future me can reopen the repository months later and understand not only *what* the code does, but *why* it looks the way it does.

A useful rule for future changes: **do not add a feature simply because it is mathematically interesting. Add it when it strengthens the research question, improves scientific validity, or creates a genuinely better analytical workflow.**

---

## 1. Project identity

QuantLab has evolved from an option-pricing comparison app into a computational-finance research workstation.

Current public-facing framing:

> **QuantLab - Computational Finance & Scientific Machine Learning Workstation**  
> An interactive research platform for option pricing, volatility modelling and scientific machine learning, combining analytical methods, numerical PDE solvers, Monte Carlo simulation and physics-informed neural networks.

The application now has four first-class areas:

- **Pricing Lab** - `/`
- **Volatility Lab** - `/volatility-lab`
- **Surface Atlas** - `/surface-atlas`
- **Research Lab** - `/research-lab`

The old duplicate navigation concept in which `/` was "Overview" and a separate item was also "Pricing Lab" has been removed. The root route is now the canonical Pricing Lab.

---

## 2. Core research idea

The project is strongest when it compares methods under a common computational experiment rather than presenting disconnected calculators.

The main methodological progression is:

1. Analytical benchmark where available.
2. Lattice approximation.
3. Finite-difference PDE approximation.
4. Monte Carlo approximation.
5. Implied-volatility and surface calibration.
6. American-option obstacle/free-boundary analysis.
7. Scientific machine learning, especially PINNs.
8. Error topography: not merely *how much* error exists, but *where it lives* in the state-time domain and how that geometry changes during training.

This last point is one of the most important future-facing ideas in QuantLab. The PINN work should not be reduced to "a neural network prices options." The research value is in understanding convergence, topology of residual error, free-boundary behaviour, and differences between numerical and learned approximations.

---

## 3. Current architecture

### Frontend

- Next.js 16.3
- React 19.2
- TypeScript
- Tailwind CSS
- Recharts for 2D quantitative charts
- Plotly / react-plotly.js for 3D surfaces

### Backend

- FastAPI
- NumPy
- SciPy
- Pydantic
- Requests / HTTPX

### Deployment

- Backend: Railway
- Frontend: Vercel
- CI: GitHub Actions

### Important production design decision

**PyTorch is not a production dependency.** PINN models are trained offline. The resulting numerical artifacts are exported to JSON and consumed by the production backend using NumPy/interpolation. This keeps Railway deployment lightweight and avoids retraining during API requests.

---

## 4. QuantLab V1 - pricing foundations

The first coherent version established a reproducible pricing comparison environment.

Implemented methods:

- Black-Scholes analytical pricing.
- CRR binomial pricing.
- Crank-Nicolson finite differences.
- Monte Carlo simulation.
- Greeks.
- Spot sweeps.
- Numerical convergence experiments.
- Accuracy-versus-runtime comparisons.

The root Pricing Lab accepts a common contract specification and evaluates multiple methods under the same assumptions. The purpose is comparison, not just independent calculators.

A major performance correction in this phase was replacing an unnecessarily expensive finite-difference implementation with an efficient tridiagonal approach for the comparison endpoint.

The Research Lab was also introduced with benchmark JSON and figures, creating a place for experiment outputs distinct from interactive pricing.

---

## 5. QuantLab V2 - volatility modelling

V2 expanded the project from price calculation into market-implied structure.

Implemented capabilities include:

- Implied-volatility inversion via bisection.
- American implied volatility using CRR.
- Calibration API.
- Volatility surfaces.
- Interpolation / IDW.
- Raw SVI.
- SSVI.
- Model comparison.
- Arbitrage diagnostics.
- Market-data abstraction and provider fallbacks.

### Scientific correctness notes

These constraints must remain explicit in future work:

- Do **not** average call and put prices when testing butterfly arbitrage.
- Butterfly diagnostics should operate on a consistent option type.
- Market calendar diagnostics can prefer calls where appropriate.
- SVI/SSVI model surfaces are European-call constructions in the implemented workflow.
- Fixed-strike total-variance calendar checks are diagnostics, not universal proofs of arbitrage-freeness.

The volatility work should continue to distinguish raw market diagnostics from model-implied surfaces.

---

## 6. QuantLab V3 - Research Workstation

V3 changed the visual and conceptual identity of the project.

The intended aesthetic is a dark research terminal / computational laboratory: navy, purple, cyan, compact cards, dense analytical grids, and interactive scientific plots.

Key V3 additions:

- Shared QuantLab shell.
- Dedicated research navigation.
- Generic 3D surface component.
- 3D implied-volatility surfaces.
- 3D SSVI total-variance surfaces.
- Volatility KPI strip.
- Compact market configuration UI.
- Collapsible quote inspector.
- Cross-section views.
- American Option Surface Atlas.

The design principle is **dense but interpretable**. It should resemble a scientific workstation rather than a consumer finance dashboard.

---

## 7. American Option Surface Atlas

This became the central V3 research feature.

The Surface Atlas is deliberately based on **American puts**, because the projected Crank-Nicolson implementation is put-specific and naturally exposes the early-exercise obstacle.

### Governing problem

For an American option with payoff \(\Phi(S)\):

\[
\max\left\{
\frac{\partial V}{\partial t}
+(r-q)S\frac{\partial V}{\partial S}
+\frac{1}{2}\sigma^2S^2\frac{\partial^2 V}{\partial S^2}
-rV,
\Phi(S)-V
\right\}=0,
\qquad
V(T,S)=\Phi(S).
\]

For an American put:

\[
\Phi(S)=\max(K-S,0).
\]

Time-to-maturity is represented as

\[
\tau=T-t.
\]

### Reference method

Projected Crank-Nicolson enforces the obstacle numerically:

\[
V_i^n=\max\left(V_i^{n,\mathrm{CN}},\Phi(S_i)\right).
\]

This projected CN surface is used as the numerical reference for comparative plots. It is a **reference approximation**, not an analytical exact solution.

### Error definition

For a method \(m\):

\[
E_m(S,\tau)=V_m(S,\tau)-V_{\mathrm{ref}}(S,\tau).
\]

Absolute error:

\[
|E_m(S,\tau)|.
\]

### Exercise / continuation gap

The obstacle gap is

\[
G(S,\tau)=V(S,\tau)-\max(K-S,0).
\]

This quantity is **not numerical error**. It measures distance from the exercise payoff and supports approximate free-boundary identification.

A numerical boundary estimate is obtained using a thresholded gap:

\[
S^*(\tau)\approx
\sup\left\{S_i<K:\;G(S_i,\tau)\le\varepsilon\right\}.
\]

The estimated curve should always be described as a numerical diagnostic rather than an analytical free-boundary solution.

---

## 8. Surface Atlas comparison design

The first atlas aligned CRR and projected CN on a common rectangular state-time grid.

Core panels:

1. CRR American put surface.
2. Projected Crank-Nicolson reference surface with estimated exercise boundary.
3. Signed CRR-minus-CN error surface.
4. Exercise premium / obstacle-gap view.
5. Free-boundary heatmap / diagnostic view.

Later, PINN outputs expanded the comparison into a 2x3 research matrix:

1. CRR.
2. Projected CN.
3. PINN V2.
4. CRR - CN.
5. PINN - CN.
6. \(|\mathrm{PINN}-\mathrm{CN}|\).

The layout was inspired by an earlier research poster comparing numerical approximations with PINNs for American options, but the current implementation uses actual QuantLab outputs rather than decorative/static figures.

---

## 9. PINN V2 experiment

The PINN uses \((S,t)\) as input and approximates option value.

The model is trained offline in PyTorch with Tanh activations. Production only reads exported artifacts.

The complementarity structure uses a smoothed Fischer-Burmeister function:

\[
\phi_\epsilon(a,b)
=\sqrt{a^2+b^2+\epsilon^2}-a-b,
\]

with

\[
a=V-\Phi,
\qquad
b=-\mathcal{L}V.
\]

Typical training configuration in the existing experiment:

- 4000 epochs.
- 3000 interior samples.
- 1000 terminal samples.
- 1000 boundary samples.
- learning rate \(10^{-3}\).
- complementarity weight 10.
- terminal/boundary weights 5.
- seed 42.

Base experiment parameters:

- \(S_0=100\)
- \(K=100\)
- \(r=0.05\)
- \(\sigma=0.20\)
- \(T=1\)
- \(q=0\)

### Time-coordinate warning

The PINN artifact uses calendar time \(t\), while Surface Atlas uses \(\tau=T-t\). Any future interpolation or overlay must preserve this transformation.

---

## 10. Offline artifacts

Current research artifacts include:

- `backend/experiments/results/american_pinn_v2_surface.json`
- `backend/experiments/results/american_pinn_convergence_atlas.json`

The convergence artifact captures one training trajectory at:

- 500 epochs
- 1000 epochs
- 2000 epochs
- 4000 epochs

This is important: the surfaces represent checkpoints from a single trajectory rather than four unrelated retraining runs.

---

## 11. PINN learning dynamics

A set of frontend components was built to study not just final error, but how error changes during optimization.

Important components/features include:

- PINN learning-dynamics plots.
- 3D absolute-error surfaces across checkpoints.
- Error convergence curves.
- Training objective view.
- Improvement surface.
- Free-boundary difficulty diagnostics.
- Boundary-distance error profile.
- Final error topography.
- 2x2 error-evolution atlas for 500/1000/2000/4000 epochs.

The improvement surface is

\[
I_{500\rightarrow4000}(S,\tau)
=
|E_{500}(S,\tau)|-|E_{4000}(S,\tau)|.
\]

Positive values indicate regions where the PINN improved between the early and final checkpoint.

---

## 12. Boundary-distance diagnostics

To avoid arbitrary physical-distance thresholds, the free-boundary diagnostic was made grid-aware.

Define

\[
\Delta S=\operatorname{median}(S_{i+1}-S_i),
\]

and

\[
d_h=
\frac{|S-S^*(\tau)|}{\Delta S}.
\]

Error is then grouped into bands such as:

- \(<1\Delta S\)
- \(1-2\Delta S\)
- \(2-4\Delta S\)
- \(4-8\Delta S\)
- \(8+\Delta S\)

At 4000 epochs the observed profile showed a meaningful concentration of residual error near the estimated stopping boundary, although the relationship was nonlinear and a single Pearson correlation was not an adequate headline summary.

A key interpretation from the observed trajectory is:

> broad-domain error -> spatial collapse -> increasingly localized residual structure.

This is descriptive evidence, not a formal statistical proof of a free-boundary learning phenomenon.

---

## 13. Linear vs log error topography

The error-evolution atlas now has two display modes.

### Linear view

Uses the raw absolute error:

\[
z=|E|.
\]

A pooled robust 97.5th-percentile display cap is used so very large early-training residuals do not visually flatten the later surfaces. The true uncapped maximum is still reported numerically.

### Log view

Uses

\[
z=\log_{10}\left(\max(|E|,10^{-6})\right).
\]

The logarithmic view reveals late-stage residual geometry that is difficult to see on the linear scale.

Important implementation choice: **metrics remain in raw price-error units**. Only the visualization coordinate is transformed. Hover data can report both transformed and original error values.

The free-boundary ridge must be transformed onto the same z-coordinate system in log mode; otherwise it would be plotted at an incorrect height.

---

## 14. WebGL resource failure and architectural fix

A major frontend issue appeared after adding multiple 3D PINN plots.

Symptom:

- The top CRR surface became a large white rectangle.
- Browser emitted a Plotly/WebGL shader error.
- CN and PINN could still render.

A crucial debugging test was to remove the lower `PinnErrorEvolutionAtlas`. The CRR surface immediately returned. This demonstrated that the CRR data itself was valid: the problem was browser WebGL context/resource pressure caused by too many simultaneously mounted 3D plots.

### Fix

A reusable lazy plot section was introduced using `IntersectionObserver`.

Lower 3D sections mount only as they approach the viewport and can unmount when hidden, releasing WebGL contexts.

Design rule going forward:

> Keep the top method-comparison surfaces eager. Lazy-mount lower multi-surface research sections. Do not treat every 3D plot as if WebGL resources were unlimited.

This fix worked and should be preserved.

---

## 15. Navigation cleanup and portfolio readiness

The QuantLab shell previously contained both `Overview` and `Pricing Lab` even though the root page already *was* the pricing lab.

Current navigation is intentionally:

- Pricing Lab `/`
- Volatility Lab `/volatility-lab`
- Surface Atlas `/surface-atlas`
- Research Lab `/research-lab`

The root page now also contains a prominent Surface Atlas CTA describing the American put state-time research workflow.

This was the point at which the project became sufficiently coherent to feature on the portfolio.

Suggested portfolio framing:

> **QuantLab - Computational Finance & Scientific Machine Learning Workstation**  
> An interactive research platform for option pricing, volatility modelling and scientific machine learning, combining analytical methods, numerical PDE solvers, Monte Carlo simulation and physics-informed neural networks.

Suggested status label:

> **Active research project** - extending numerical option-pricing experiments toward scientific machine learning and uncertainty-aware computational finance.

---

# Future-Me Roadmap

## A. Do next when there is a clear research reason

### 1. Promote the best-trained PINN artifact

The lightweight V2 artifact was initially a 500-epoch preview, while the convergence artifact contains a 4000-epoch checkpoint. Future production/portfolio comparisons should preferentially expose the best converged snapshot while preserving the training trajectory as a separate experiment.

### 2. Improve free-boundary evaluation

Possible refinements:

- Exclude the terminal row \(\tau=0\) from some boundary-distance inference.
- Separate spatial domain-boundary residuals from stopping-boundary residuals.
- Compare the extracted free boundary against a higher-resolution numerical benchmark.
- Perform grid-refinement studies to quantify boundary-estimation sensitivity.

Do this only if it strengthens a paper/thesis argument; it is not required merely to make the dashboard larger.

### 3. Add stronger scientific baselines

Potential extensions:

- Higher-resolution projected CN reference.
- Trinomial lattice comparison.
- Longstaff-Schwartz Monte Carlo for American options.
- Alternative PINN formulations for variational inequalities.
- Deep operator / DeepONet experiments where there is a genuine parameter-family question.

### 4. Parameterized scientific ML

A major future direction is to move from a PINN for one contract family to a model conditioned on parameters such as

\[
(S,K,r,q,\sigma,\tau).
\]

This would make the research question about learning an **option-pricing operator**, not simply fitting one PDE instance.

### 5. Uncertainty-aware modelling

Future work could add uncertainty quantification to learned pricing surfaces, for example:

- ensembles,
- Bayesian approximations,
- conformal calibration,
- predictive intervals over model discrepancy.

This would align QuantLab with broader interests in uncertainty-aware financial decision systems.

---

## B. Volatility research ideas

Potential extensions:

- SABR.
- Heston calibration.
- Local-volatility construction.
- SVI/SSVI parameter stability through time.
- Surface-arbitrage stress tests.
- Calibration confidence / parameter uncertainty.

Do not add all of these at once. Prefer one research question with a clear comparison protocol.

---

## C. Numerical-method ideas

Potential extensions:

- Explicit and implicit finite differences in the same benchmark suite.
- Trinomial trees.
- Adaptive meshes near the exercise boundary.
- Richardson extrapolation.
- Runtime/accuracy Pareto frontiers.
- Stability diagnostics for PDE discretizations.

The original thesis/research theme - **numerical approximations versus neural approximations** - should remain visible in these extensions.

---

## D. Surface Atlas ideas

The Surface Atlas can become the flagship QuantLab research interface.

Possible future panels:

- method-to-method signed error.
- relative error with robust denominator.
- exercise-boundary comparison across methods.
- cross-sectional slices at selected maturities.
- animation through training epochs.
- parameter sweep atlas for volatility or rates.
- click-to-expand individual poster panels.
- export-ready figure mode for papers/presentations.

Keep WebGL constraints in mind. Prefer lazy loading and selective rendering rather than mounting every surface at once.

---

## E. Portfolio and research communication

Portfolio page should include:

- Strong Surface Atlas hero image.
- Short architectural explanation.
- Live Demo button.
- GitHub button.
- Four-module summary: Pricing, Volatility, Surface Atlas, PINN Research.
- A short paragraph connecting the project to earlier research on American option numerical approximations and PINNs.

A useful public message is that QuantLab is **active research software**, not a static course project.

---

## F. Documentation goals

Maintain documentation in three layers:

1. `README.md` - concise setup, architecture, demo and quick research summary.
2. `docs/QuantLab_Research_Journal.md` - this living notebook of decisions, experiments and future goals.
3. A formal LaTeX/PDF technical report - equations, methods, implementation chronology, diagnostics and research roadmap.

When a major new experiment is completed, add a dated journal entry here before moving on.

---

# Dated Log

## 2026-09-02 - Portfolio-ready checkpoint

### Completed

- Surface Atlas established as a first-class module.
- PINN convergence trajectory exposed at 500, 1000, 2000 and 4000 epochs.
- PINN absolute-error topography and boundary ridge visualized.
- Linear and \(\log_{10}\) error modes implemented.
- WebGL resource issue diagnosed and fixed using lazy mount/unmount architecture.
- Root navigation simplified: `/` is now Pricing Lab.
- Surface Atlas added to navigation and promoted from the Pricing Lab landing content.
- Frontend changes committed and pushed.

### Current interpretation

QuantLab now has a sufficiently coherent scientific and software narrative for a portfolio. Further work should deepen the research rather than simply increase feature count.

### Next portfolio task

Create the QuantLab portfolio entry with a strong hero image, project summary, architecture/stack, research highlights, Live Demo and GitHub links.

### Reminder to future me

Do not describe projected CN as an exact solution. Do not call the obstacle gap a numerical error. Keep the distinction between pricing reference, exercise gap, free-boundary estimate, and PINN approximation error explicit.

