import Link from "next/link";


const navItems = [
  {
    label: "Pricing Lab",
    href: "/",
  },
  {
    label: "Volatility Lab",
    href: "/volatility-lab",
  },
  {
    label: "Surface Atlas",
    href: "/surface-atlas",
  },
  {
    label: "Research Lab",
    href: "/research-lab",
  },
];


export function QuantLabNav() {
  return (
    <nav className="border-b border-zinc-800 bg-zinc-950/90">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4 md:px-10">

        <Link
          href="/"
          className="font-semibold tracking-tight"
        >
          Quant
          <span className="text-emerald-400">
            Lab
          </span>
        </Link>

        <div className="flex items-center gap-2">
          {navItems.map(
            (link) => (
              <Link
                key={link.href}
                href={link.href}
                className="rounded-lg px-3 py-2 text-sm text-zinc-400 transition hover:bg-zinc-900 hover:text-zinc-100"
              >
                {link.label}
              </Link>
            )
          )}
        </div>

      </div>
    </nav>
  );
}