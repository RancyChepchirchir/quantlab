import {
  QuantLabNav,
} from "@/components/layout/QuantLabNav";

<body>
  <QuantLabNav />

  <Link
  href="/research-lab"
  className="mt-6 inline-flex items-center gap-2 rounded-xl border border-zinc-800 px-4 py-2 text-sm text-zinc-300 transition hover:border-emerald-400 hover:text-emerald-400"
>
  Explore FDM vs PINN vs DeepONet
  <span>→</span>
</Link>

  {children}
</body>