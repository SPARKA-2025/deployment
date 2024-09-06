import React, { useState, useEffect } from 'react';
import axios from 'axios';

function VehicleMetadata() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [measurement, setMeasurement] = useState('plate_detection');
  const [start, setStart] = useState('-5m');
  const [stop, setStop] = useState('now()');
  const [refreshInterval, setRefreshInterval] = useState(0); // in seconds

  // useEffect(() => {
  //   fetchData();

  //   if (refreshInterval > 0) {
  //     const interval = setInterval(fetchData, refreshInterval * 1000);
  //     return () => clearInterval(interval); // Cleanup on unmount
  //   }
  // }, [measurement, start, stop, refreshInterval]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await axios.post('http://127.0.0.1:5000/query', {
        measurement: measurement,
        start: start,
        stop: stop,
      });
      console.log(response)
    } catch (error) {
      console.error("Error fetching data:", error);
    }
    setLoading(false);
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Vehicle Metadata</h1>

      <form className="mb-4 flex space-x-4">
        <div>
          <label htmlFor="measurement" className="block font-medium mb-1">Measurement</label>
          <input
            id="measurement"
            type="text"
            value={measurement}
            onChange={(e) => setMeasurement(e.target.value)}
            className="border rounded-md p-2"
            placeholder="e.g., vehicle"
          />
        </div>

        <div>
          <label htmlFor="start" className="block font-medium mb-1">Start</label>
          <input
            id="start"
            type="text"
            value={start}
            onChange={(e) => setStart(e.target.value)}
            className="border rounded-md p-2"
            placeholder="e.g., -1m, -1h"
          />
        </div>

        <div>
          <label htmlFor="stop" className="block font-medium mb-1">Stop</label>
          <input
            id="stop"
            type="text"
            value={stop}
            onChange={(e) => setStop(e.target.value)}
            className="border rounded-md p-2"
            placeholder="e.g., now"
          />
        </div>

        <div>
          <label htmlFor="refreshInterval" className="block font-medium mb-1">Auto Refresh Interval (seconds)</label>
          <input
            id="refreshInterval"
            type="number"
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(e.target.value)}
            className="border rounded-md p-2"
            placeholder="e.g., 60 for 1 minute"
          />
        </div>
      </form>

      <button onClick={fetchData}>Click</button>

      {loading ? (
        <div className="text-center">
          <div className="loader"></div>
          <p>Loading...</p>
        </div>
      ) : (
        <table className="table-auto w-full border-collapse border border-gray-200">
          <thead>
            <tr className="bg-gray-100">
              <th className="border border-gray-300 p-2">Plate Number</th>
              <th className="border border-gray-300 p-2">Vehicle</th>
              <th className="border border-gray-300 p-2">Image</th>
            </tr>
          </thead>
          <tbody>
            {data.map((item) => (
              <tr key={item.plateNumber}>
                <td className="border border-gray-300 p-2">{item.plateNumber}</td>
                <td className="border border-gray-300 p-2">{item.vehicle}</td>
                <td className="border border-gray-300 p-2">
                  <img src={item.image} alt="Vehicle" className="w-24 h-24 object-cover" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default VehicleMetadata;
