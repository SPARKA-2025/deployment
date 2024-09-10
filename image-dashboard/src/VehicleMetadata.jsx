import React, { useState, useEffect } from 'react';
import axios from 'axios';
import GroupedDataComponent from './GroupedDataComponent';

const VehicleMetadata = ({ token, onLogout }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [measurement, setMeasurement] = useState('plate_detection');
  const [start, setStart] = useState('-2d');
  const [stop, setStop] = useState('now()');
  const [refreshInterval, setRefreshInterval] = useState(0);
  const link = 'localhost';

  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await axios.post(
        `http://${link}:5000/query`,
        { measurement, start, stop },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const groupedData = {};

      response.data.forEach(item => {
        const id = item.tags.id;
        if (!groupedData[id]) {
          groupedData[id] = { id, fields: {} };
        }
        groupedData[id].fields[item.field] = item.value;
      });

      setData(Object.values(groupedData));
      console.log(groupedData)
    } catch (error) {
      console.error("Error fetching data:", error);
      if (error.response && error.response.status === 401) {
        onLogout();
      }
    }
    setLoading(false);
  };

  useEffect(() => {
    if (token) {
      fetchData();
    }
  }, [token]);

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Vehicle Metadata</h1>

      <form className="mb-4 flex flex-col space-y-4">
        <div>
          <label htmlFor="measurement" className="block font-medium mb-1">Measurement</label>
          <input
            id="measurement"
            type="text"
            value={measurement}
            onChange={(e) => setMeasurement(e.target.value)}
            className="border rounded-md p-2"
            placeholder="e.g., plate_detection"
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
            placeholder="e.g., -2h"
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
            placeholder="e.g., now()"
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
            placeholder="e.g., 60"
          />
        </div>
      </form>

      <button
        onClick={fetchData}
        className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
      >
        Fetch Data
      </button>

      <button
        onClick={onLogout}
        className="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded mt-4"
      >
        Logout
      </button>

      {loading ? (
        <p>Loading...</p>
      ) : (
        <GroupedDataComponent data={data} url={link} />
      )}
    </div>
  );
};

export default VehicleMetadata;
