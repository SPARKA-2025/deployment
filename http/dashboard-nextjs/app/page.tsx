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
        <Link href="#disaster-recovery">Disaster Recovery</Link>
        <Link href="#team">Team</Link>
        <Link href="/login">Login Dashboard</Link>
      </nav>

      {/* Hero Section */}
      <header className="bg-blue-600 text-white text-center py-20">
        <h1 className="text-4xl font-bold">Machine Learning Monitoring Service</h1>
        <p className="mt-4 text-lg">Ensuring optimal performance and reliability of your ML systems.</p>
      </header>

      {/* Overview Section */}
      <section id="overview" className="max-w-2xl mx-auto p-8">
        <h2 className="text-2xl font-semibold">Overview</h2>
        <p className="mt-2">
          Our monitoring service provides comprehensive insights into your machine learning models' performance, ensuring they run efficiently and effectively in production environments.
        </p>
      </section>

      {/* Features Section */}
      <section id="features" className="bg-white p-8">
        <h2 className="text-2xl font-semibold">Features</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-4">
          <div className="border p-6 rounded shadow">
            <h3 className="text-lg font-bold">Performance Metrics</h3>
            <p>Track key performance indicators for your ML models.</p>
          </div>
          <div className="border p-6 rounded shadow">
            <h3 className="text-lg font-bold">Anomaly Detection</h3>
            <p>Automatically identify and alert on abnormal behaviors.</p>
          </div>
          <div className="border p-6 rounded shadow">
            <h3 className="text-lg font-bold">Resource Utilization</h3>
            <p>Monitor CPU, memory, and GPU usage for efficiency.</p>
          </div>
        </div>
      </section>

      {/* Documentation Section */}
      <section id="documentation" className="max-w-2xl mx-auto p-8">
        <h2 className="text-2xl font-semibold">Documentation</h2>
        <p className="mt-2">
          Access detailed documentation on our monitoring protocols, system architecture, and troubleshooting guides to ensure seamless operations.
        </p>
        <Link href="/docs">
          <button className="mt-4 bg-blue-600 text-white px-4 py-2 rounded">
            View Documentation
          </button>
        </Link>
      </section>

      {/* Disaster Recovery Section */}
      <section id="disaster-recovery" className="bg-white p-8">
        <h2 className="text-2xl font-semibold">Disaster Recovery</h2>
        <p className="mt-2">
          Learn about our disaster recovery protocols, including data backup strategies and recovery procedures to minimize downtime in case of failure.
        </p>
      </section>

      {/* Team Section */}
      <section id="team" className="bg-white p-8">
        <h2 className="text-2xl font-semibold">Meet the Team</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-4">
          <div className="border p-6 rounded shadow">
            <h3 className="text-lg font-bold">Alice Johnson</h3>
            <p>Lead Data Scientist</p>
            <p>Specializing in model optimization and performance tuning.</p>
          </div>
          <div className="border p-6 rounded shadow">
            <h3 className="text-lg font-bold">Bob Smith</h3>
            <p>DevOps Engineer</p>
            <p>Expert in system reliability and monitoring infrastructure.</p>
          </div>
          <div className="border p-6 rounded shadow">
            <h3 className="text-lg font-bold">Charlie Brown</h3>
            <p>Technical Support</p>
            <p>Providing assistance and troubleshooting for our users.</p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-800 text-white text-center p-4">
        <p>&copy; 2024 Machine Learning Monitoring Service</p>
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