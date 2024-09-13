import React from 'react';

const GroupedDataComponent = ({ data, url }) => {
  return (
    <div>
      <table className="table-auto">
        <thead>
          <tr>
            <th>Log</th>
            <th>Plate Number</th>
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
            <tr key={item.id}>
              {Object.entries(item.fields).map(([field, value]) => (
                <td key={field}>
                  {value}
                </td>
              ))}
              <td>
                <img
                  src={`${url}/${item.fields.filename}.jpg`}
                  alt="image"
                  width="500"
                  height="600"
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default GroupedDataComponent;
