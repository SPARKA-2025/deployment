'use client'

import { useEffect, useState } from 'react';
import Link from 'next/link';

const Documentation = () => {
  const [activeSection, setActiveSection] = useState('');

  const sections = [
    'getting-started',
    'installation',
    'usage',
    'troubleshooting',
    'faq',
    'advanced-usage',
    'performance-tuning',
    'monitoring-best-practices',
  ];

  const handleScroll = () => {
    const scrollPosition = window.scrollY;
    sections.forEach((section) => {
      const sectionElement = document.getElementById(section);
      if (sectionElement) {
        const sectionTop = sectionElement.offsetTop;
        const sectionHeight = sectionElement.offsetHeight;
        if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
          setActiveSection(section);
        }
      }
    });
  };

  useEffect(() => {
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="font-sans bg-gray-50">
      {/* Navbar */}
      <nav className="flex justify-around bg-gray-800 text-white p-4">
      <Link href="/">Home</Link>
        <Link href="#overview">Overview</Link>
        <Link href="#features">Features</Link>
        <Link href="/docs">Documentation</Link>
        <Link href="#team">Team</Link>
        <Link href="/login">Login Dashboard</Link>
      </nav>

      <div className="flex">
        {/* Sidebar */}
        <aside className="w-1/4 bg-gray-200 p-4 h-screen overflow-y-auto">
          <h2 className="text-lg font-bold">Documentation</h2>
          <ul className="mt-4">
            {sections.map((section) => (
              <li key={section}>
                <Link
                  href={`#${section}`}
                  className={`block py-2 rounded ${
                    activeSection === section ? 'bg-gray-300' : 'hover:bg-gray-300'
                  }`}
                >
                  {section.replace(/-/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())}
                </Link>
              </li>
            ))}
          </ul>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-8">
          <h1 className="text-3xl font-bold">Documentation</h1>

          {/* Sections */}
          <section id="getting-started" className="mt-10">
            <h2 className="text-2xl font-semibold">Getting Started</h2>
            <p className="mt-2">
              Welcome to the Machine Learning Monitoring Service documentation! This guide will help you set up and utilize our service effectively.
            </p>
          </section>

          <section id="installation" className="mt-10">
            <h2 className="text-2xl font-semibold">Installation</h2>
            <p className="mt-2">
              To install the monitoring service, follow these steps:
            </p>
            <ol className="list-decimal ml-6 mt-2">
              <li>Clone the repository from GitHub.</li>
              <li>Install the required dependencies using npm:</li>
              <pre className="bg-gray-100 p-2 rounded">
                <code>npm install</code>
              </pre>
              <li>Start the service:</li>
              <pre className="bg-gray-100 p-2 rounded">
                <code>npm start</code>
              </pre>
            </ol>
          </section>

          <section id="usage" className="mt-10">
            <h2 className="text-2xl font-semibold">Usage</h2>
            <p className="mt-2">
              Once the service is running, you can access the dashboard at <code>http://localhost:3000</code>. Here, you can monitor your ML models and view performance metrics.
            </p>
          </section>

          <section id="troubleshooting" className="mt-10">
            <h2 className="text-2xl font-semibold">Troubleshooting</h2>
            <p className="mt-2">
              If you encounter any issues, check the following:
            </p>
            <ul className="list-disc ml-6 mt-2">
              <li>Ensure all dependencies are installed.</li>
              <li>Check the logs for any error messages.</li>
              <li>Restart the service if you encounter unexpected behavior.</li>
            </ul>
          </section>

          <section id="faq" className="mt-10">
            <h2 className="text-2xl font-semibold">FAQ</h2>
            <p className="mt-2">
              <strong>Q: How can I reset my configurations?</strong><br />
              A: You can reset configurations by deleting the config file and restarting the service.
            </p>
          </section>

          {/* Additional Sections */}
          <section id="advanced-usage" className="mt-10">
            <h2 className="text-2xl font-semibold">Advanced Usage</h2>
            <p className="mt-2">
              For advanced users, explore additional features such as custom metrics and integration with CI/CD pipelines.
            </p>
          </section>

          <section id="performance-tuning" className="mt-10">
            <h2 className="text-2xl font-semibold">Performance Tuning</h2>
            <p className="mt-2">
              Learn how to optimize your monitoring setup to handle larger datasets and improve response times.
            </p>
          </section>

          <section id="monitoring-best-practices" className="mt-10">
            <h2 className="text-2xl font-semibold">Monitoring Best Practices</h2>
            <p className="mt-2">
              Discover best practices for monitoring your ML models, including setting thresholds and alerting strategies.
            </p>
          </section>
        </main>
      </div>
    </div>
  );
};

export default Documentation;
