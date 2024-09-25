'use client'
import React, {useState, useEffect} from "react";
import { getCookie, deleteCookie } from "cookies-next";

const Navbar = () => {
  const [hasToken, setHasToken] = useState(false);

  useEffect(() => {
    const myCookie = getCookie('access-token');
    setHasToken(Boolean(myCookie));
  }, []);

  const onLogout = () => {
    deleteCookie('access-token');
    window.location.href = '/';
  };

  return (
    <nav className="block w-full max-w-screen-lg px-4 py-2 mx-auto bg-white shadow-md rounded-md lg:px-8 lg:py-3 mt-10">
      <div className="container flex flex-wrap items-center justify-between mx-auto text-slate-800">
        <a href="#" className="mr-4 block cursor-pointer py-1.5 text-base text-slate-800 font-semibold">
          Plate Detection Operations Dashboard
        </a>

        <div className="hidden lg:block">
          <ul className="flex flex-col gap-2 mt-2 mb-4 lg:mb-0 lg:mt-0 lg:flex-row lg:items-center lg:gap-6">
            <li className="flex items-center p-1 text-sm gap-x-2 text-slate-600">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor" className="h-6 w-6 text-slate-500">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 0 0 2.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 0 0-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75 2.25 2.25 0 0 0-.1-.664m-5.8 0A2.251 2.251 0 0 1 13.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25ZM6.75 12h.008v.008H6.75V12Zm0 3h.008v.008H6.75V15Zm0 3h.008v.008H6.75V18Z" />
              </svg>
              <a href="#" className="flex items-center">Pages</a>
            </li>
            {hasToken && (
              <li className="flex items-center p-1 text-sm gap-x-2 text-slate-600">
                <button
                  onClick={onLogout}
                  className="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded m-2"
                >
                  Logout
                </button>
              </li>
            )}
          </ul>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
