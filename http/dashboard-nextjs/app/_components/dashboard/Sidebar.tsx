"use client";

import { usePathname, useRouter } from "next/navigation";

export default function Sidebar({}) {
  const pathname = usePathname();
  const router = useRouter();
  const menu = [
    {
      title: "Monitoring",
      path: "",
    },
    {
      title: "Performance",
      path: "performance",
    },
    {
      title: "Alert & Notification",
      path: "alert-notification",
    },
    {
      title: "Data Analysis",
      path: "data-analysis",
    },
    {
      title: "Management",
      path: "management",
    },
  ];

  return (
    <div className="flex flex-col text-white text-xl items-center h-screen w-1/5 bg-gray-800 gap-y-4 py-8">
      {menu.map((item, index) => (
        <div
          key={index}
          className={`h-[8%] w-[80%] px-2 rounded-md flex items-center
            ${
                pathname.includes(`dashboard${item.path}`)
                    ? " bg-blue-600 "
                    : "hover:cursor-pointer hover:bg-blue-600"
            }`
        }
          onClick={ () => router.push(`/dashboard/${item.path}`)}
        >
          {item.title}
        </div>
      ))}
    </div>
  );
}
