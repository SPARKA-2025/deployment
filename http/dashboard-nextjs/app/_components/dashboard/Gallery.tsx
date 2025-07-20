export default function Gallery({data}: {data: any[]}) {
  // Function to generate image URL based on plate number for MinIO fallback
  const getMinIOImageUrl = (plateNumber: string) => {
    // Remove spaces and special characters from plate number for filename
    const cleanPlateNumber = plateNumber?.replace(/\s+/g, '').replace(/[^a-zA-Z0-9]/g, '');
    // Use MinIO gateway URL for accessing saved images
    return `http://localhost:5002/download/${cleanPlateNumber}.jpg`;
  };

  // Function to get the best available image source
  const getImageSrc = (item: any) => {
    // Priority: backend base64 image > MinIO image > default image
    if (item?.img && item.img.startsWith('data:')) {
      return item.img; // Use backend base64 image
    }
    if (item?.plate?.number) {
      return getMinIOImageUrl(item.plate.number); // Try MinIO image
    }
    return '/assets/images/car.jpg'; // Default fallback
  };

  return (
    <div className="flex flex-col w-full h-fit min-h-12 rounded-md border border-gray-300">
      <div className="p-2">Gallery</div>
      <hr className="border-gray-300" />
      <div className="grid grid-cols-4 gap-12 p-4">
        {data.map((item: any, index) => (
          <div key={index} className="h-32 bg-gray-200 rounded-md">
            <img
              src={getImageSrc(item)}
              alt={`Car ${index + 1}`}
              className="h-full w-full object-cover rounded-md"
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                // If current src is not the default image, try MinIO then default
                if (!target.src.includes('/assets/images/car.jpg')) {
                  if (target.src.includes('localhost:5002')) {
                    // MinIO failed, use default
                    target.src = '/assets/images/car.jpg';
                  } else {
                    // Backend image failed, try MinIO
                    if (item?.plate?.number) {
                      target.src = getMinIOImageUrl(item.plate.number);
                    } else {
                      target.src = '/assets/images/car.jpg';
                    }
                  }
                }
              }}
            />
            <div className="flex justify-between text-sm">
                <span>
                    {item?.plate?.number}
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
