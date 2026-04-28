'use client';
import { useState } from 'react';

export default function WriteReviewPage() {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    address: '', landlord: '',
    noise: 0, maintenance: 0, safety: 0, pests: 0,
    reviewText: '', file: null
  });

  const handleNext = () => setStep((prev) => Math.min(prev + 1, 4));
  const handleBack = () => setStep((prev) => Math.max(prev - 1, 1));
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log("Submitting Review:", formData);
    // TODO: Send to Supabase API
    alert("Review submitted successfully! Pending verification.");
  };

  // Helper to render star rating inputs
  const StarRating = ({ label, field }: { label: string, field: keyof typeof formData }) => (
    <div className="flex justify-between items-center mb-4">
      <label className="font-medium text-slate-700">{label}</label>
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            onClick={() => setFormData({ ...formData, [field]: star })}
            className={`text-2xl transition-colors ${
              (formData[field] as number) >= star ? 'text-emerald-500' : 'text-slate-200 hover:text-emerald-200'
            }`}
          >
            ★
          </button>
        ))}
      </div>
    </div>
  );

  return (
    <div className="flex-1 bg-slate-50 py-12 px-4">
      <div className="max-w-2xl mx-auto bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
        
        {/* Progress Bar */}
        <div className="bg-slate-100 h-2 w-full">
          <div 
            className="bg-emerald-600 h-full transition-all duration-300 ease-in-out" 
            style={{ width: `${(step / 4) * 100}%` }}
          />
        </div>

        <div className="p-8">
          <h1 className="text-3xl font-bold text-slate-900 mb-2">Leave a Review</h1>
          <p className="text-slate-500 mb-8">Step {step} of 4</p>

          <form onSubmit={handleSubmit}>
            {/* STEP 1: Location & Landlord */}
            {step === 1 && (
              <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4">
                <h2 className="text-xl font-semibold mb-4">Property Details</h2>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Property Address</label>
                  <input 
                    type="text" required placeholder="123 Main St, Apt 4B"
                    className="w-full rounded-lg border-slate-200 border p-3 focus:ring-2 focus:ring-emerald-500 outline-none"
                    value={formData.address}
                    onChange={(e) => setFormData({...formData, address: e.target.value})}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Landlord / Management Co.</label>
                  <input 
                    type="text" placeholder="e.g. Equity Residential or John Doe"
                    className="w-full rounded-lg border-slate-200 border p-3 focus:ring-2 focus:ring-emerald-500 outline-none"
                    value={formData.landlord}
                    onChange={(e) => setFormData({...formData, landlord: e.target.value})}
                  />
                </div>
              </div>
            )}

            {/* STEP 2: Ratings */}
            {step === 2 && (
              <div className="space-y-2 animate-in fade-in slide-in-from-bottom-4">
                <h2 className="text-xl font-semibold mb-4">Rate Your Experience</h2>
                <StarRating label="Noise Levels" field="noise" />
                <StarRating label="Maintenance Speed" field="maintenance" />
                <StarRating label="Safety & Security" field="safety" />
                <StarRating label="Pest Control" field="pests" />
              </div>
            )}

            {/* STEP 3: Written Review */}
            {step === 3 && (
              <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4">
                <h2 className="text-xl font-semibold mb-4">The Good & The Bad</h2>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Share your experience (Pros/Cons)</label>
                  <textarea 
                    rows={5} required placeholder="Thin walls? Responsive super? Let others know..."
                    className="w-full rounded-lg border-slate-200 border p-3 focus:ring-2 focus:ring-emerald-500 outline-none resize-none"
                    value={formData.reviewText}
                    onChange={(e) => setFormData({...formData, reviewText: e.target.value})}
                  />
                </div>
              </div>
            )}

            {/* STEP 4: Verification */}
            {step === 4 && (
              <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4">
                <h2 className="text-xl font-semibold mb-4">Get Verified (Optional)</h2>
                <p className="text-sm text-slate-500 mb-4">
                  Upload a redacted utility bill or lease agreement to get a "Verified Resident" badge. This significantly boosts trust in your review.
                </p>
                <div className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center hover:bg-slate-50 transition-colors cursor-pointer">
                  <div className="text-slate-500">
                    <p className="font-medium text-emerald-600">Click to upload</p>
                    <p className="text-sm mt-1">PDF, JPG, or PNG</p>
                  </div>
                  {/* Hidden file input goes here */}
                </div>
              </div>
            )}

            {/* Navigation Buttons */}
            <div className="flex justify-between mt-10 pt-6 border-t border-slate-100">
              <button 
                type="button" 
                onClick={handleBack}
                className={`px-6 py-2 rounded-lg font-medium text-slate-600 hover:bg-slate-100 transition-colors ${step === 1 ? 'invisible' : ''}`}
              >
                Back
              </button>
              
              {step < 4 ? (
                <button 
                  type="button" 
                  onClick={handleNext}
                  className="px-6 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-medium transition-colors shadow-sm shadow-emerald-200"
                >
                  Next
                </button>
              ) : (
                <button 
                  type="submit"
                  className="px-6 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg font-medium transition-colors shadow-sm"
                >
                  Submit Review
                </button>
              )}
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
