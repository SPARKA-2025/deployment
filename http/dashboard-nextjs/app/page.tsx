'use client'

import Link from 'next/link';

const Home = () => {
  return (
    <div className="font-sans bg-gray-50">
      {/* Navbar */}
      <nav className="flex justify-around bg-gray-800 text-white p-4">
        <Link href="/">Home</Link>
        <Link href="#overview">Overview</Link>
        <Link href="#features">Features</Link>
        <Link href="#documentation">Documentation</Link>
        <Link href="#team">Team</Link>
        <Link href="/login">Login Dashboard</Link>
      </nav>

      {/* Hero Section */}
      <header className="bg-blue-600 text-white text-center py-20">
        <h1 className="text-4xl font-bold">Smart Parking Solutions</h1>
        <p className="mt-4 text-lg">Revolutionizing parking with machine learning and real-time data.</p>
      </header>

      {/* Overview Section */}
      <section id="overview" className="max-w-2xl mx-auto p-8">
        <h2 className="text-2xl font-semibold">Overview</h2>
        <p className="mt-2">
          Our monitoring machine learning system enhances smart parking by optimizing space usage and providing real-time data for a seamless user experience.
        </p>
      </section>

      {/* Features Section */}
      <section id="features" className="bg-white p-8">
        <h2 className="text-2xl font-semibold">Features</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-4">
          <div className="border p-6 rounded shadow">
            <h3 className="text-lg font-bold">Real-time Monitoring</h3>
            <p>Instant updates on available parking spaces.</p>
          </div>
          <div className="border p-6 rounded shadow">
            <h3 className="text-lg font-bold">Predictive Analytics</h3>
            <p>Utilize data to forecast parking availability.</p>
          </div>
          <div className="border p-6 rounded shadow">
            <h3 className="text-lg font-bold">User-friendly App</h3>
            <p>Access parking information anytime, anywhere.</p>
          </div>
        </div>
      </section>

      {/* Documentation Section */}
      <section id="documentation" className="max-w-2xl mx-auto p-8">
        <h2 className="text-2xl font-semibold">Documentation</h2>
        <p className="mt-2">
          Explore our comprehensive documentation to understand the features, setup process, and best practices for using our system.
        </p>
        <Link href="/docs">
          <button className="mt-4 bg-blue-600 text-white px-4 py-2 rounded">
            View Documentation
          </button>
        </Link>
      </section>

      {/* Team Section */}
      <section id="team" className="bg-white p-8">
        <h2 className="text-2xl font-semibold">Meet the Team</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-4">
          <div className="border p-6 rounded shadow">
            <h3 className="text-lg font-bold">John Doe</h3>
            <p>CEO & Founder</p>
            <p>Visionary leader driving innovation.</p>
          </div>
          <div className="border p-6 rounded shadow">
            <h3 className="text-lg font-bold">Jane Smith</h3>
            <p>CTO</p>
            <p>Expert in machine learning and AI technology.</p>
          </div>
          <div className="border p-6 rounded shadow">
            <h3 className="text-lg font-bold">Emily Johnson</h3>
            <p>Product Manager</p>
            <p>Passionate about user experience and design.</p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-800 text-white text-center p-4">
        <p>&copy; 2024 Smart Parking Ecosystem</p>
        <div className="mt-2">
          <Link href="/privacy" className="text-gray-300 hover:underline">Privacy Policy</Link>
          <span className="mx-2">|</span>
          <Link href="/terms" className="text-gray-300 hover:underline">Terms of Service</Link>
        </div>
      </footer>
    </div>
  );
};

export default Home;