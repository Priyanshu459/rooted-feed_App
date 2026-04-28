import Link from 'next/link';

export default function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-white/80 backdrop-blur-md">
      <div className="container mx-auto flex h-16 items-center justify-between px-4 md:px-6">
        <Link href="/" className="flex items-center gap-2">
          {/* Trust-building green icon placeholder */}
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-600 text-white font-bold">
            H
          </div>
          <span className="text-xl font-bold tracking-tight text-slate-900">
            Honest Renter
          </span>
        </Link>
        <nav className="flex items-center gap-4 sm:gap-6">
          <Link href="/write-review" className="text-sm font-medium text-slate-600 hover:text-emerald-600 transition-colors hidden sm:block">
            Write a Review
          </Link>
          <Link href="/login" className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors">
            Log In
          </Link>
          <Link href="/signup" className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 transition-colors">
            Sign Up
          </Link>
        </nav>
      </div>
    </header>
  );
}
