'use client';

import React, { useState, useEffect } from "react";
import Navbar from "@/components/Navbar";
import { getCookie } from "cookies-next";
import axios from "axios";
import Sidebar from "@/_components/dashboard/Sidebar";
import Gallery from "@/_components/dashboard/Gallery";
import useFetch from "@/hooks/useFetch";
import logKendaraan from "@/utils/dummies/logKendaraan";
import LogTable from "@/_components/dashboard/LogTable";

const VehicleMetadata = () => {
  const [measurement, setMeasurement] = useState("plate_detection");
  const [start, setStart] = useState("-10m");
  const [stop, setStop] = useState("now()");
  const [refreshInterval, setRefreshInterval] = useState({
    value: 60,
    timeUnit: "seconds",
  });
  const [intervalId, setIntervalId] = useState<any>(null);
  const [hasRefreshIntervalChanged, setHasRefreshIntervalChanged] = useState(false);
  const influxdb_url = "http://localhost:5000";
  const token = getCookie("access-token");
  const { data, loading, error, refetch } = useFetch('/performance')

  useEffect(() => {
    const interval = setInterval(() => {
      refetch();
    }, refreshInterval.timeUnit === "seconds" ? refreshInterval.value * 1000 : refreshInterval.timeUnit === "minutes" ? refreshInterval.value * 60000 : refreshInterval.value * 3600000);
    setIntervalId(interval);

    return () => clearInterval(interval);
  }, [ refreshInterval]);

  const handleRefreshIntervalChange = (value: number, timeUnit: string) => {
    setRefreshInterval({ value, timeUnit });
    setHasRefreshIntervalChanged(true);
  };

  const handleApplyRefreshInterval = () => {
    clearInterval(intervalId);
    const interval = setInterval(() => {
      refetch();
    }, refreshInterval.timeUnit === "seconds" ? refreshInterval.value * 1000 : refreshInterval.timeUnit === "minutes" ? refreshInterval.value * 60000 : refreshInterval.value * 3600000);
    setIntervalId(interval);
    setHasRefreshIntervalChanged(false);
  };
  return (
    <div className="h-full w-full flex relative">
      <Sidebar />

      <div className="flex flex-col w-4/5">
        {/* NAVBAR */}
        <Navbar />

        {/* CONTENT */}
        <div className="container mx-auto px-4 gap-y-6">
          {/* FORM */}
          <form className="mb-4 flex flex-col space-y-4">
            <div>
              <label htmlFor="measurement" className="block font-medium mb-1">
                Measurement
              </label>
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
              <label htmlFor="start" className="block font-medium mb-1">
                Start
              </label>
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
              <label htmlFor="stop" className="block font-medium mb-1">
                Stop
              </label>
              <input
                id="stop"
                type="text"
                value={stop}
                onChange={(e) => setStop(e.target.value)}
                className="border rounded-md p-2"
                placeholder="e.g., now()"
              />
            </div>

            <div className="flex items-center space-x-2">
            <label htmlFor="refreshInterval" className="block font-medium">
              Refresh Interval:
            </label>
            <input
              id="refreshInterval"
              type="number"
              value={refreshInterval.value}
              onChange={(e) =>
                handleRefreshIntervalChange(parseInt(e.target.value), refreshInterval.timeUnit)
              }
              className="border rounded-md p-2 w-20"
              min="0"
            />
            <select
              value={refreshInterval.timeUnit}
              onChange={(e) =>
                handleRefreshIntervalChange(refreshInterval.value, e.target.value)
              }
              className="border rounded-md p-2 w-32"
            >
              <option value="seconds">Seconds</option>
              <option value="minutes">Minutes</option>
              <option value="hours">Hours</option>
            </select>
            {hasRefreshIntervalChanged && (
              <button
                onClick={handleApplyRefreshInterval}
                className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded"
              >
                Apply
              </button>
            )}
            <button
              onClick={() => refetch()}
              className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
            >
              Fetch Now
            </button>
          </div>
          </form>

          {loading ? (
            <p>Loading...</p>
          ) : (
            <div></div>
          )}

          <Gallery data={logKendaraan.data} />
          <LogTable data={logKendaraan.data} />
        </div>
      </div>
    </div>
  );
};

export default VehicleMetadata;