import Link from "next/link";

import {
  getResearchBenchmarks,
} from "@/lib/api/researchBenchmarks";

import {
  ResearchFigure,
} from "@/components/research/ResearchFigure";



function number(
  value:
    | number
    | null
    | undefined,
  digits = 6
) {
  if (
    value === null ||
    value === undefined
  ) {
    return "—";
  }

  return value.toFixed(
    digits
  );
}


function scientific(
  value:
    | number
    | undefined
) {
  if (value === undefined) {
    return "—";
  }

  return value.toExponential(
    3
  );
}


export default async function ResearchLabPage() {
  const data =
    await getResearchBenchmarks();

  const pinn =
    data.pinn;

  const deeponet =
    data.deeponet;

  const amortisation =
    data.amortisation;

  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="mx-auto max-w-7xl px-6 py-14 md:px-10">

        <header className="mb-14">
          <div className="mb-5 flex items-center justify-between gap-6">
            <div>
              <p className="text-sm uppercase tracking-[0.3em] text-emerald-400">
                QuantLab Research
              </p>

              <h1 className="mt-3 max-w-5xl text-4xl font-semibold tracking-tight md:text-6xl">
                Classical solvers,
                scientific ML &
                operator learning.
              </h1>
            </div>

            <Link
              href="/"
              className="hidden rounded-xl border border-zinc-800 px-4 py-2 text-sm text-zinc-400 transition hover:border-emerald-400 hover:text-emerald-400 md:block"
            >
              ← Pricing Lab
            </Link>
          </div>

          <p className="max-w-3xl text-lg leading-8 text-zinc-400">
            A controlled comparison of
            finite-difference methods,
            PINNs and DeepONets for
            American option pricing,
            evaluated on accuracy,
            computational cost and
            repeated-query efficiency.
          </p>
        </header>


        {pinn && (
          <section className="mb-14">

            <SectionHeading
              eyebrow="Experiment 01"
              title="American Put — Solver Accuracy"
              body="CRR provides the reference solution. Projected Crank–Nicolson is compared with two PINN formulations across a common spot-price grid."
            />

            <div className="overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900">

              <div className="overflow-x-auto">
                <table className="w-full min-w-[900px] text-left text-sm">

                  <thead className="border-b border-zinc-800 text-zinc-500">
                    <tr>
                      <th className="px-5 py-4">
                        Method
                      </th>

                      <th className="px-5 py-4">
                        MAE
                      </th>

                      <th className="px-5 py-4">
                        RMSE
                      </th>

                      <th className="px-5 py-4">
                        Max error
                      </th>

                      <th className="px-5 py-4">
                        ATM error
                      </th>

                      <th className="px-5 py-4">
                        Training / solve
                      </th>

                      <th className="px-5 py-4">
                        Inference
                      </th>
                    </tr>
                  </thead>

                  <tbody>
                    {Object.entries(
                      pinn.methods
                    ).map(
                      ([name, method]) => (
                        <tr
                          key={name}
                          className="border-b border-zinc-800/70 last:border-0"
                        >
                          <td className="px-5 py-4">
                            <div className="font-medium">
                              {displayMethod(
                                name
                              )}
                            </div>

                            {method.formulation && (
                              <div className="mt-1 text-xs text-zinc-500">
                                {
                                  method.formulation
                                }
                              </div>
                            )}
                          </td>

                          <MetricCell
                            value={
                              method.mae
                            }
                          />

                          <MetricCell
                            value={
                              method.rmse
                            }
                          />

                          <MetricCell
                            value={
                              method.max_error
                            }
                          />

                          <MetricCell
                            value={
                              method.atm_error
                            }
                          />

                          <td className="px-5 py-4 font-mono text-zinc-400">
                            {number(
                              method.training_seconds ??
                              method.runtime_seconds
                            )}{" "}
                            s
                          </td>

                          <td className="px-5 py-4 font-mono text-zinc-400">
                            {method.inference_seconds !==
                            undefined
                              ? `${number(
                                  method.inference_seconds
                                )} s`
                              : "—"}
                          </td>
                        </tr>
                      )
                    )}
                  </tbody>

                </table>
              </div>
            </div>

          </section>
        )}

        <div className="mt-8 grid gap-6 xl:grid-cols-2">

        <ResearchFigure
            src="/research/american_pinn_v1_vs_v2_solution.png"
            alt="American put pricing comparison between CRR, projected Crank Nicolson, PINN V1 and PINN V2."
            title="American put solution comparison"
            caption="The full pricing functions are compared over the same spot-price interval rather than at a single at-the-money point."
        />

        <ResearchFigure
            src="/research/american_pinn_v1_vs_v2_error.png"
            alt="Absolute pricing errors for projected Crank Nicolson and PINN models."
            title="Error profile across spot"
            caption="Absolute error relative to the high-step CRR benchmark reveals where each solver performs well and where approximation quality deteriorates."
        />

        </div>

        <div className="mt-6">
        <ResearchFigure
            src="/research/american_pinn_v1_vs_v2_training.png"
            alt="Training loss curves for American option PINN V1 and PINN V2."
            title="PINN training convergence"
            caption="The obstacle-penalty and complementarity-aware formulations are compared through their optimisation trajectories."
        />
        </div>


        {deeponet && (
          <section className="mb-14">

            <SectionHeading
              eyebrow="Experiment 02"
              title="Operator Generalisation"
              body="DeepONet learns the mapping from option parameters and evaluation coordinates to American put values generated by the classical solver."
            />

            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">

              <StatCard
                label="MAE"
                value={number(
                  deeponet.metrics.mae
                )}
              />

              <StatCard
                label="RMSE"
                value={number(
                  deeponet.metrics.rmse
                )}
              />

              <StatCard
                label="Median error"
                value={number(
                  deeponet.metrics
                    .median_error
                )}
              />

              <StatCard
                label="95% error"
                value={number(
                  deeponet.metrics
                    .p95_error
                )}
              />

              <StatCard
                label="Max error"
                value={number(
                  deeponet.metrics
                    .max_error
                )}
              />

            </div>

            <div className="mt-6 grid gap-6 lg:grid-cols-2">

              <article className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6">
                <p className="text-sm uppercase tracking-[0.18em] text-zinc-500">
                  Branch operator
                </p>

                <h3 className="mt-2 text-xl font-semibold">
                  Pricing problem
                </h3>

                <div className="mt-5 flex flex-wrap gap-2">
                  {deeponet.model
                    .branch_variables
                    .map(
                      (variable) => (
                        <span
                          key={variable}
                          className="rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 font-mono text-sm text-zinc-300"
                        >
                          {variable}
                        </span>
                      )
                    )}
                </div>
              </article>

              <article className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6">
                <p className="text-sm uppercase tracking-[0.18em] text-zinc-500">
                  Trunk operator
                </p>

                <h3 className="mt-2 text-xl font-semibold">
                  Evaluation coordinates
                </h3>

                <div className="mt-5 flex flex-wrap gap-2">
                  {deeponet.model
                    .trunk_variables
                    .map(
                      (variable) => (
                        <span
                          key={variable}
                          className="rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 font-mono text-sm text-zinc-300"
                        >
                          {variable}
                        </span>
                      )
                    )}
                </div>
              </article>

            </div>

          </section>
        )}

        <div className="mt-8 grid gap-6 xl:grid-cols-2">

        <ResearchFigure
            src="/research/american_deeponet_loss.png"
            alt="American option DeepONet training loss."
            title="DeepONet training convergence"
            caption="Training loss for the operator network learning a family of American-put pricing solutions."
        />

        <ResearchFigure
            src="/research/american_deeponet_predictions.png"
            alt="American DeepONet predictions compared with projected Crank Nicolson target prices."
            title="Out-of-sample operator predictions"
            caption="Predicted American option values are compared with projected Crank–Nicolson targets on previously unseen parameter sets."
        />

        </div>


        {amortisation && (
          <section className="mb-14">

            <SectionHeading
              eyebrow="Experiment 03"
              title="When does operator learning pay off?"
              body="DeepONet has an expensive offline stage but very cheap online inference. This experiment measures the point at which repeated pricing queries recover that upfront cost."
            />

            <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">

              <article className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6">

                <div className="grid gap-6 sm:grid-cols-2">

                  <div>
                    <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">
                      Projected CN
                    </p>

                    <p className="mt-3 font-mono text-3xl font-semibold">
                      {scientific(
                        amortisation
                          .online
                          .projected_cn
                          .seconds_per_query
                      )}
                    </p>

                    <p className="mt-2 text-sm text-zinc-500">
                      seconds / query
                    </p>
                  </div>

                  <div>
                    <p className="text-xs uppercase tracking-[0.2em] text-emerald-400">
                      DeepONet
                    </p>

                    <p className="mt-3 font-mono text-3xl font-semibold text-emerald-400">
                      {scientific(
                        amortisation
                          .online
                          .deeponet
                          .seconds_per_query
                      )}
                    </p>

                    <p className="mt-2 text-sm text-zinc-500">
                      seconds / query
                    </p>
                  </div>

                </div>

                <div className="mt-8 border-t border-zinc-800 pt-6">
                  <p className="text-sm text-zinc-500">
                    Measured online speedup
                  </p>

                  <p className="mt-2 font-mono text-4xl font-semibold">
                    {number(
                      amortisation
                        .online
                        .speedup,
                      2
                    )}
                    ×
                  </p>
                </div>

              </article>


              <article className="rounded-2xl border border-emerald-500/30 bg-emerald-400/5 p-6">

                <p className="text-sm uppercase tracking-[0.2em] text-emerald-400">
                  Break-even
                </p>

                <p className="mt-4 font-mono text-5xl font-semibold">
                  {amortisation
                    .online
                    .break_even_queries !==
                  null
                    ? Math.ceil(
                        amortisation
                          .online
                          .break_even_queries
                      ).toLocaleString()
                    : "—"}
                </p>

                <p className="mt-4 leading-7 text-zinc-400">
                  approximate pricing queries
                  required before the
                  offline data-generation and
                  training cost is recovered.
                </p>

              </article>

            </div>


            <div className="mt-6 grid gap-4 sm:grid-cols-3">

              <StatCard
                label="Data generation"
                value={`${number(
                  amortisation
                    .offline
                    .data_generation_seconds,
                  2
                )} s`}
              />

              <StatCard
                label="Training"
                value={`${number(
                  amortisation
                    .offline
                    .training_seconds,
                  2
                )} s`}
              />

              <StatCard
                label="Total offline cost"
                value={`${number(
                  amortisation
                    .offline
                    .total_seconds,
                  2
                )} s`}
              />

            </div>

          </section>
        )}


        <section className="rounded-2xl border border-zinc-800 bg-zinc-900 p-7">

          <p className="text-sm uppercase tracking-[0.2em] text-zinc-500">
            Interpretation
          </p>

          <h2 className="mt-2 text-2xl font-semibold">
            Classical solvers remain the
            accuracy baseline.
          </h2>

          <p className="mt-4 max-w-4xl leading-8 text-zinc-400">
            The scientific-ML methods are
            evaluated not simply on whether
            they reproduce an option price,
            but on whether their additional
            training cost is justified by
            generalisation and repeated-query
            performance. This makes the
            comparison fundamentally about
            computational regimes rather
            than declaring one method
            universally superior.
          </p>

        </section>

      </div>
    </main>
  );
}


function displayMethod(
  name: string
) {
  const labels: Record<
    string,
    string
  > = {
    crr: "CRR benchmark",
    projected_cn:
      "Projected Crank–Nicolson",
    pinn_v1: "PINN V1",
    pinn_v2: "PINN V2",
  };

  return (
    labels[name] ??
    name.replaceAll(
      "_",
      " "
    )
  );
}


function MetricCell({
  value,
}: {
  value: number;
}) {
  return (
    <td className="px-5 py-4 font-mono text-zinc-400">
      {number(value)}
    </td>
  );
}


function StatCard({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <article className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5">
      <p className="text-xs uppercase tracking-[0.18em] text-zinc-500">
        {label}
      </p>

      <p className="mt-4 font-mono text-2xl font-semibold">
        {value}
      </p>
    </article>
  );
}


function SectionHeading({
  eyebrow,
  title,
  body,
}: {
  eyebrow: string;
  title: string;
  body: string;
}) {
  return (
    <div className="mb-6">
      <p className="text-sm uppercase tracking-[0.2em] text-zinc-500">
        {eyebrow}
      </p>

      <h2 className="mt-2 text-3xl font-semibold">
        {title}
      </h2>

      <p className="mt-3 max-w-3xl leading-7 text-zinc-400">
        {body}
      </p>
    </div>
  );
}