"use client";

import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";

type SubMenuItem = {
    title: string;
    path: string;
  };
  
  type MenuItem = {
    title: string;
    path?: string;
    submenu?: SubMenuItem[];
  };

export default function Sidebar({}) {
  const pathname = usePathname();
  const router = useRouter();
  const [openMenu, setOpenMenu] = useState<number|null>(null);

  const menu = [
    {
      title: "Home",
      path: "/",
      submenu: [
        { title: "Home", path: "/" },
        { title: "Overview", path: "#overview" },
        { title: "Features", path: "#features" },
        { title: "Documentation", path: "documentation" },
        { title: "Team", path: "#team" },
      ],
    },
    { title: "Monitoring", path: "dashboard" },
    { title: "Performance", path: "dashboard/performance" },
    { title: "Alert & Notification", path: "dashboard/alert-notification" },
    { title: "Data Analysis", path: "dashboard/data-analysis" },
    { title: "Management", path: "dashboard/management" },
  ];

  const handleMenuClick = (item: MenuItem, index: number | null) => {
    if (item.submenu) {
      setOpenMenu(openMenu === index ? null : index);
    } else if (item.path) {
      router.replace(`/${item.path}`);
    }
  };

  const handleSubMenuClick = (subItem: SubMenuItem) => {
    if (subItem.path) {
      router.replace(`/${subItem.path}`);
    }
  };

  return (
    <div className="flex flex-col text-white text-xl items-center h-screen w-1/5 bg-gray-800 gap-y-4 py-8 sticky top-0">
      {menu.map((item, index) => (
        <div key={index} className="w-[80%]">
          <div
            className={`h-12 w-full px-2 rounded-md flex items-center justify-between
              ${
                pathname.includes(`/${item.path || ""}`)
                  ? "bg-blue-600"
                  : "hover:cursor-pointer hover:bg-blue-600"
              }`}
            onClick={() => handleMenuClick(item, index)}
          >
            <span>{item.title}</span>
            {item.submenu && (
              <span>{openMenu === index ? "-" : "+"}</span>
            )}
          </div>

          {openMenu === index && item.submenu && (
            <div className="ml-6 flex flex-col gap-y-2">
              {item.submenu.map((subItem, subIndex) => (
                <div
                  key={subIndex}
                  className={`text-lg px-2 py-1 rounded-md flex items-center
                    ${
                      pathname.includes(`dashboard/${subItem.path}`)
                        ? "bg-blue-500"
                        : "hover:cursor-pointer hover:bg-blue-500"
                    }`}
                  onClick={() => handleSubMenuClick(subItem)}
                >
                  {subItem.title}
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
