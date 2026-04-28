export default function Footer() {
  return (
    <footer className="w-full border-t bg-slate-50 py-8 text-slate-500 mt-auto">
      <div className="container mx-auto px-4 md:px-6 flex flex-col md:flex-row justify-between items-center gap-4">
        <div className="text-sm">
          &copy; {new Date().getFullYear()} The Honest Renter&apos;s Database. All rights reserved.
        </div>
        <nav className="flex gap-4 sm:gap-6 text-sm">
          <a href="#" className="hover:text-emerald-600 transition-colors">Terms of Service</a>
          <a href="#" className="hover:text-emerald-600 transition-colors">Privacy Policy</a>
          <a href="#" className="hover:text-emerald-600 transition-colors">For Landlords</a>
        </nav>
      </div>
    </footer>
  );
}
