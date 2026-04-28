import SearchBar from "@/components/SearchBar";

export default function Home() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center w-full px-4 text-center py-24 bg-gradient-to-b from-slate-50 to-white">
      <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-slate-900 mb-6">
        Don&apos;t sign blindly. <br className="hidden md:block" />
        <span className="text-emerald-600">Know before you rent.</span>
      </h1>
      <p className="text-lg md:text-xl text-slate-600 max-w-2xl mx-auto mb-10">
        Read real, verified reviews on maintenance, noise, pests, and safety from past tenants. Search an address or landlord to get started.
      </p>
      
      <div className="w-full max-w-3xl">
        <SearchBar />
      </div>
    </div>
  );
}
