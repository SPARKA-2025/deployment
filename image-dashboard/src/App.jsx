import React, { useState, useEffect } from 'react';
import axios from 'axios';

const GroupedDataComponent = ({ data }) => {
  return (
    <div>
      <table class="table-auto">
      <thead>
        <tr>
          <th>Log</th>
          <th>Plate Number </th>
          <th>Plate Number X</th>
          <th>Plate Number Y</th>
          <th>Vehicle</th>
          <th>Vehicle X</th>
          <th>Vehicle Y</th>
          <th>Image</th>
        </tr>
      </thead>
      <tbody>
            {data.map((item) => (
            <tr key={item.fields.filename}>
                {Object.entries(item.fields).map(([field, value]) => (
                  <td key={field}>
                    {value}
                  </td>
                ))}
                <td>
                  <img src={`http://minio_gateway/download/${item.fields.filename}.jpg`} alt="image" width="500" height="600"></img>
                </td>
                {console.log(item.fields.filename)}
            </tr>
          ))}
      </tbody>
    </table>
    </div>
  );
};

function VehicleMetadata() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [measurement, setMeasurement] = useState('plate_detection');
  const [start, setStart] = useState('-2h');
  const [stop, setStop] = useState('now()');
  const [refreshInterval, setRefreshInterval] = useState(0); // in seconds

  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await axios.post('http://influxdb_gateway:5000/query', {
        measurement: measurement,
        start: start,
        stop: stop,
      });

      console.log(response.data)
      const groupedData = {};

      // Iterate over each object in the array
      response.data.forEach(item => {
        const id = item.tags.id;

        // If the id doesn't exist in groupedData, initialize it
        if (!groupedData[id]) {
          groupedData[id] = {
            id: id,
            fields: {}
          };
        }

        // Add the field and value to the corresponding id's fields object
        groupedData[id].fields[item.field] = item.value;
      });

      // Convert the groupedData object back into an array of objects if needed
      const result = Object.values(groupedData);

      // Output the result
      console.log(result);
      setData(result)
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
      <button className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded" onClick={fetchData}>
        Click
      </button>
      <GroupedDataComponent data={data}/>
    </div>
  );
}

export default VehicleMetadata;
