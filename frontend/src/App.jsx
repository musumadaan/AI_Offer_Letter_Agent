import { useState } from 'react';

function App() {
  const [name, setName] = useState('');
  const [offerLetter, setOfferLetter] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showOfferLetter, setShowOfferLetter] = useState(false);

  const fetchOfferLetter = async () => {
    if (!name.trim()) {
      setError('Please enter an employee name.');
      return;
    }
    setLoading(true);
    setError('');
    setOfferLetter('');
    try {
      const response = await fetch(`/api/generate-offer/?name=${encodeURIComponent(name)}`);
      if (!response.ok) throw new Error(`Failed to fetch offer letter: ${response.status}`);
      const data = await response.json();
      setOfferLetter(data.offer_letter || 'No offer letter generated.');
      setShowOfferLetter(true);
    } catch (err) {
      setError(err.message);
      console.error("Fetch error:", err); // Debug
    } finally {
      setLoading(false);
    }
  };

  const goBack = () => {
    setShowOfferLetter(false);
    setOfferLetter('');
    setError('');
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      {!showOfferLetter ? (
        <div className="bg-white p-6 rounded-lg shadow-lg w-full max-w-md">
          <h1 className="text-2xl font-bold mb-4 text-center">Offer Letter Generator</h1>
          <div className="mb-4">
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter employee name"
              className="w-full p-2 border rounded mb-2"
            />
            <button
              onClick={fetchOfferLetter}
              disabled={loading}
              className="w-full bg-blue-500 text-white p-2 rounded hover:bg-blue-600 disabled:bg-blue-300"
            >
              {loading ? 'Generating...' : 'Generate Offer Letter'}
            </button>
          </div>
          {error && <p className="text-red-500 text-center mb-4">{error}</p>}
        </div>
      ) : (
        <div className="bg-white p-6 rounded-lg shadow-lg w-full max-w-md">
          <h1 className="text-2xl font-bold mb-4 text-center">Offer Letter</h1>
          <div className="mt-4 p-4 bg-gray-50 rounded">
            <pre className="whitespace-pre-wrap text-sm">{offerLetter}</pre>
          </div>
          <button
            onClick={goBack}
            className="mt-4 w-full bg-gray-500 text-white p-2 rounded hover:bg-gray-600"
          >
            Back to Search
          </button>
        </div>
      )}
    </div>
  );
}

export default App;