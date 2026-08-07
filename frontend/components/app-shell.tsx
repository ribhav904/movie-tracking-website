"use client";

import {
  Activity,
  BookOpen,
  ChartNoAxesCombined,
  ChevronDown,
  Clapperboard,
  Heart,
  LibraryBig,
  Menu,
  Moon,
  Search,
  Sun,
  Swords,
  X,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { isBackendConfigured } from "@/lib/config";
import { useAuth } from "@/providers/auth-provider";
import { useTheme } from "@/providers/theme-provider";

const navigation = [
  { href: "/", label: "Today", icon: Clapperboard },
  { href: "/discover", label: "Discover", icon: Search },
  { href: "/library", label: "Library", icon: LibraryBig },
  { href: "/activity", label: "Activity", icon: Activity },
  { href: "/reports", label: "Reports", icon: ChartNoAxesCombined },
  { href: "/arena", label: "Battle Arena", icon: Swords },
  { href: "/recommendations", label: "For you", icon: Heart },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { state, email } = useAuth();
  const { resolvedTheme, toggleTheme } = useTheme();
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    if (state === "signed_out") router.replace("/sign-in");
  }, [router, state]);

  if (state === "loading") {
    return <div className="screen-loader">Restoring your collection…</div>;
  }

  return (
    <div className="app-frame">
      <aside className={`sidebar ${menuOpen ? "sidebar--open" : ""}`}>
        <div className="sidebar__brand">
          <Link href="/" className="brand" aria-label="Ledger home">
            <span className="brand__mark" aria-hidden="true">L</span>
            <span>
              <strong>Ledger</strong>
              <small>Entertainment archive</small>
            </span>
          </Link>
          <button className="icon-button sidebar__close" onClick={() => setMenuOpen(false)} aria-label="Close navigation">
            <X size={18} />
          </button>
        </div>

        <nav className="sidebar__nav" aria-label="Primary navigation">
          {navigation.map((item) => {
            const Icon = item.icon;
            const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`nav-item ${active ? "nav-item--active" : ""}`}
                onClick={() => setMenuOpen(false)}
              >
                <Icon size={17} strokeWidth={1.8} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="sidebar__footer">
          {!isBackendConfigured && <span className="preview-label">Preview data</span>}
          <Link href="/settings" className="account-link">
            <span className="account-link__avatar" aria-hidden="true">{email.slice(0, 1).toUpperCase()}</span>
            <span className="account-link__text">
              <strong>{state === "preview" ? "Preview collection" : email}</strong>
              <small>{state === "preview" ? "Local interface" : "Account settings"}</small>
            </span>
            <ChevronDown size={15} aria-hidden="true" />
          </Link>
        </div>
      </aside>

      <div className="app-main">
        <header className="topbar">
          <button className="icon-button topbar__menu" onClick={() => setMenuOpen(true)} aria-label="Open navigation">
            <Menu size={20} />
          </button>
          <button className="command-search" onClick={() => router.push("/discover")}>
            <Search size={17} />
            <span>Search your next watch, read, or play</span>
            <kbd>/</kbd>
          </button>
          <div className="topbar__actions">
            <button className="icon-button" onClick={toggleTheme} aria-label={`Switch to ${resolvedTheme === "dark" ? "light" : "dark"} mode`}>
              {resolvedTheme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <Link href="/activity#log" className="button button--primary topbar__log">
              <BookOpen size={16} />
              Log activity
            </Link>
          </div>
        </header>
        <main className="page-content">{children}</main>
      </div>

      <nav className="mobile-nav" aria-label="Mobile navigation">
        {navigation.slice(0, 5).map((item) => {
          const Icon = item.icon;
          const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
          return (
            <Link key={item.href} href={item.href} className={`mobile-nav__item ${active ? "mobile-nav__item--active" : ""}`}>
              <Icon size={18} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
      {menuOpen && <button className="sidebar-scrim" aria-label="Close navigation" onClick={() => setMenuOpen(false)} />}
    </div>
  );
}
