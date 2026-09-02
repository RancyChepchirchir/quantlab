"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

type QuantLabShellProps = {
  children: ReactNode;
};

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

function isActive(pathname: string, href: string, label: string) {
  if (label === "Pricing Lab") {
    return pathname === "/" && false;
  }

  if (label === "Surface Atlas") {
    return (
        <svg
        width="18"
        height="18"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
        >
        <path d="M4 17 9 12l4 3 7-8" />
        <path d="M4 21h16" />
        <path d="M4 3v18" />
        <circle
            cx="9"
            cy="12"
            r="1"
            fill="currentColor"
        />
        <circle
            cx="13"
            cy="15"
            r="1"
            fill="currentColor"
        />
        <circle
            cx="20"
            cy="7"
            r="1"
            fill="currentColor"
        />
        </svg>
    );
    }

  return pathname.startsWith(href);
}

export function QuantLabShell({ children }: QuantLabShellProps) {
  const pathname = usePathname();

  return (
    <div className="quantlab-shell">
      <aside className="quantlab-sidebar">
        <div className="quantlab-brand">
          <div className="quantlab-brand-mark">Q</div>

          <div>
            <div className="quantlab-brand-name">QuantLab</div>
            <div className="quantlab-brand-subtitle">Research Workstation</div>
          </div>
        </div>

        <nav className="quantlab-sidebar-nav">
          {navItems.map((item) => {
            const active = isActive(pathname, item.href, item.label);

            return (
              <Link
                key={item.label}
                href={item.href}
                className={`quantlab-nav-item ${
                  active ? "quantlab-nav-item-active" : ""
                }`}
              >
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="quantlab-sidebar-section">
          <div className="quantlab-sidebar-section-title">
            System health
          </div>

          <div className="quantlab-health-row">
            <span className="quantlab-health-dot" />
            <span>Pricing engine</span>
            <span className="quantlab-health-status">Healthy</span>
          </div>

          <div className="quantlab-health-row">
            <span className="quantlab-health-dot" />
            <span>Volatility models</span>
            <span className="quantlab-health-status">Healthy</span>
          </div>

          <div className="quantlab-health-row">
            <span className="quantlab-health-dot" />
            <span>Research models</span>
            <span className="quantlab-health-status">Ready</span>
          </div>
        </div>

        <div className="quantlab-sidebar-quote">
          <p>“In God we trust; all others must bring data.”</p>
          <span>— W. Edwards Deming</span>
        </div>
      </aside>

      <div className="quantlab-main">
        <header className="quantlab-topbar">
          <div>
            <div className="quantlab-topbar-eyebrow">
              Quantitative Research Environment
            </div>

            <div className="quantlab-topbar-title">
              QuantLab
            </div>
          </div>

          <div className="quantlab-topbar-status">
            <div className="quantlab-status-block">
              <span className="quantlab-status-label">Engine</span>
              <span className="quantlab-status-live">
                <span className="quantlab-status-dot" />
                ONLINE
              </span>
            </div>

            <div className="quantlab-status-block">
              <span className="quantlab-status-label">Stack</span>
              <span className="quantlab-status-value">
                FastAPI · Next.js
              </span>
            </div>

            <div className="quantlab-status-block">
              <span className="quantlab-status-label">Mode</span>
              <span className="quantlab-status-value">
                Research
              </span>
            </div>
          </div>
        </header>

        <main className="quantlab-content">
          {children}
        </main>

        <footer className="quantlab-footer">
          <span>QuantLab Research Workstation</span>
          <span>Pricing · Volatility · Numerical Methods · Neural PDEs</span>
          <span>v3</span>
        </footer>
      </div>
    </div>
  );
}