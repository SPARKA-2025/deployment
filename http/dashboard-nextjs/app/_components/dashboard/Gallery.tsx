export default function Gallery({data}: {data: any[]}) {
  return (
    <div className="flex flex-col w-full h-fit min-h-12 rounded-md border border-gray-300">
      <div className="p-2">Gallery</div>
      <hr className="border-gray-300" />
      <div className="grid grid-cols-4 gap-12 p-4">
        {data.map((item: any, index) => (
          <div key={index} className="h-32 bg-gray-200 rounded-md">
            <img
              src={item?.img}
              alt={`Car ${index + 1}`}
              className="h-full w-full object-cover rounded-md"
            />
            <div className="flex justify-between text-sm">
                <span>
                    {item?.plate.number}
                </span>
                <span>
                    {item?.timestamp}
                </span>
            </div>
          </div>
        ))}
      </div>
      <div className="flex w-full justify-end text-blue-600 hover:text-blue-400 hover:cursor-pointer">{"Lihat selengkapnya ->"}</div>
    </div>
  );
}
