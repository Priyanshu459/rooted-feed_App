import Link from 'next/link';

// Mock data to visualize the design before connecting the database
const MOCK_PROPERTY = {
  address: "123 Maple Street, Apt 4B",
  city: "Brooklyn",
  state: "NY",
  landlord: "Equity Residential",
  overallScore: 3.8,
  breakdown: {
    noise: 4.0,
    maintenance: 2.5,
    safety: 4.5,
    pests: 4.2
  },
  reviews: [
    {
      id: 1,
      date: "Oct 12, 2023",
      isVerified: true,
      text: "Great location and felt very safe. However, whenever something broke, it took management over a week to send someone out. The walls are also surprisingly thick so noise wasn't an issue.",
      ratings: { noise: 5, maintenance: 2, safety: 5, pests: 5 }
    },
    {
      id: 2,
      date: "Aug 05, 2023",
      isVerified: false,
      text: "Had a small issue with ants in the summer, but the landlord sent pest control within 24 hours. Very responsive.",
      ratings: { noise: 4, maintenance: 5, safety: 4, pests: 3 }
    }
  ]
};

export default function PropertyProfilePage({ params }: { params: { id: string } }) {
  // Helper to render progress bars for the breakdown
  const RatingBar = ({ label, score }: { label: string, score: number }) => (
    <div className="flex items-center gap-4 text-sm mb-2">
      <span className="w-28 text-slate-600 font-medium">{label}</span>
      <div className="flex-1 h-2.5 bg-slate-100 rounded-full overflow-hidden">
        <div 
          className="h-full bg-emerald-500 rounded-full" 
          style={{ width: `${(score / 5) * 100}%` }}
        />
      </div>
      <span className="w-8 font-bold text-slate-900">{score.toFixed(1)}</span>
    </div>
  );

  return (
    <div className="flex-1 bg-slate-50 py-10">
      <div className="container mx-auto px-4 max-w-5xl">
        
        {/* Header Section */}
        <div className="bg-white rounded-2xl p-6 md:p-10 shadow-sm border border-slate-100 mb-8 flex flex-col md:flex-row gap-8 items-start md:items-center justify-between">
          <div>
            <h1 className="text-3xl font-extrabold text-slate-900 mb-2">{MOCK_PROPERTY.address}</h1>
            <p className="text-lg text-slate-500 mb-1">{MOCK_PROPERTY.city}, {MOCK_PROPERTY.state}</p>
            <p className="text-sm font-medium text-slate-700 bg-slate-100 inline-block px-3 py-1 rounded-md mt-2">
              Managed by: {MOCK_PROPERTY.landlord}
            </p>
          </div>
          
          <div className="flex items-center gap-6">
            <div className="text-center">
              <div className="text-5xl font-black text-emerald-600 tracking-tighter">
                {MOCK_PROPERTY.overallScore}
              </div>
              <div className="text-sm text-slate-500 font-medium mt-1">Out of 5.0</div>
            </div>
            <Link href="/write-review" className="bg-slate-900 text-white px-6 py-3 rounded-lg font-medium hover:bg-slate-800 transition-colors shadow-sm">
              Write Review
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Left Column: Rating Breakdown */}
          <div className="md:col-span-1">
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100 sticky top-24">
              <h3 className="text-lg font-bold text-slate-900 mb-6">Rating Breakdown</h3>
              <RatingBar label="Noise Levels" score={MOCK_PROPERTY.breakdown.noise} />
              <RatingBar label="Maintenance" score={MOCK_PROPERTY.breakdown.maintenance} />
              <RatingBar label="Safety" score={MOCK_PROPERTY.breakdown.safety} />
              <RatingBar label="Pest Control" score={MOCK_PROPERTY.breakdown.pests} />
            </div>
          </div>

          {/* Right Column: Review Feed */}
          <div className="md:col-span-2 space-y-6">
            {MOCK_PROPERTY.reviews.map((review) => (
              <div key={review.id} className="bg-white rounded-2xl p-6 md:p-8 shadow-sm border border-slate-100">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <div className="bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded text-xs font-bold flex items-center gap-1">
                        ★ {(
                          (review.ratings.noise + review.ratings.maintenance + review.ratings.safety + review.ratings.pests) / 4
                        ).toFixed(1)}
                      </div>
                      {review.isVerified && (
                        <span className="text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full flex items-center gap-1">
                          ✓ Verified Resident
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-slate-400">Reviewed on {review.date}</div>
                  </div>
                </div>
                
                <p className="text-slate-700 leading-relaxed mb-6">
                  "{review.text}"
                </p>

                <div className="flex flex-wrap gap-x-6 gap-y-2 border-t border-slate-100 pt-4">
                  <span className="text-xs text-slate-500"><b className="text-slate-700">Noise:</b> {review.ratings.noise}/5</span>
                  <span className="text-xs text-slate-500"><b className="text-slate-700">Maintenance:</b> {review.ratings.maintenance}/5</span>
                  <span className="text-xs text-slate-500"><b className="text-slate-700">Safety:</b> {review.ratings.safety}/5</span>
                  <span className="text-xs text-slate-500"><b className="text-slate-700">Pests:</b> {review.ratings.pests}/5</span>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
