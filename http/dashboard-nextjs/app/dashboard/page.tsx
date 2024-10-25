"use client"
import React, { useState, useEffect } from 'react';
import GroupedDataComponent from '@/components/GroupedDataComponent'
import Navbar from '@/components/Navbar';
import { getCookie } from "cookies-next";
import axios from 'axios';


const VehicleMetadata = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [measurement, setMeasurement] = useState('plate_detection');
  const [start, setStart] = useState('-10m');
  const [stop, setStop] = useState('now()');
  const [refreshInterval, setRefreshInterval] = useState(0);
  const influxdb_url = 'http://localhost:5000';
  const token = getCookie('access-token');

  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await axios.post(
        `${influxdb_url}/query`,
        { measurement, start, stop },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const groupedData : any = {};

      response.data.forEach((item : any) => {
        const id = item.tags.id;
        if (!groupedData[id]) {
          groupedData[id] = { id, fields: {} };
        }
        // console.log(item.time)
        groupedData[id].fields[item.field] = item.value;
        groupedData[id].fields["time"] = item.time
      });

      setData(Object.values(groupedData));
      console.log(groupedData)
    } catch (error) {
      console.error("Error fetching data:", error);
    }
    setLoading(false);
  };

  useEffect(() => {
    if (token) {
      fetchData();
    }
  }, [token]);

  return (
    <div>

     <Navbar/>
      <div className="container mx-auto p-4">
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
        </form>

        <button
        //   onClick={fetchData}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
        >
          Fetch Data
        </button>


        {loading ? (
          <p>Loading...</p>
        ) : (
          <GroupedDataComponent data={data} url={'http://localhost:5002/download'} />
        )}
      </div>
    </div>
  );
};

export default VehicleMetadata;
