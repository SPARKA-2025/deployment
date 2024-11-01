export default function LogTable({data}: {data: any[]}) {
    return (
        <div className="w-full">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <th className="p-2 border text-left">Log ID</th>
                <th className="p-2 border text-left">Timestamp</th>
                <th className="p-2 border text-left">Plate Number</th>
                <th className="p-2 border text-left">Plate X</th>
                <th className="p-2 border text-left">Plate Y</th>
                <th className="p-2 border text-left">Vehicle X</th>
                <th className="p-2 border text-left">Vehicle Y</th>
              </tr>
            </thead>
            <tbody>
              {data.map((item) => (
                <tr key={item.logId}>
                  <td className="p-2 border">{item.logId}</td>
                  <td className="p-2 border">{item.timestamp}</td>
                  <td className="p-2 border">{item.plate.number}</td>
                  <td className="p-2 border">{item.plate.x}</td>
                  <td className="p-2 border">{item.plate.y}</td>
                  <td className="p-2 border">{item.vehiclePosition.x}</td>
                  <td className="p-2 border">{item.vehiclePosition.y}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
    );
}