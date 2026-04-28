'use client';
import { useState } from 'react';

export default function SearchBar() {
  const [query, setQuery] = useState('');

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Route to search results page or trigger API call
    console.log("Searching for:", query);
  };

  return (
    <form onSubmit={handleSearch} className="relative w-full max-w-2xl mx-auto shadow-lg rounded-full">
      <div className="relative flex items-center w-full h-14 rounded-full focus-within:ring-2 focus-within:ring-emerald-500 bg-white overflow-hidden border border-slate-200">
        <div className="grid place-items-center h-full w-12 text-slate-400">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        <input
          className="peer h-full w-full outline-none text-slate-700 pr-4 bg-transparent placeholder-slate-400 text-lg"
          type="text"
          id="search"
          placeholder="Search by address, building, or landlord..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button 
          type="submit"
          className="h-full px-6 bg-emerald-600 hover:bg-emerald-700 text-white font-medium transition-colors"
        >
          Search
        </button>
      </div>
    </form>
  );
}
