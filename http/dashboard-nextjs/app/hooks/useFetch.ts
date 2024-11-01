'use client';

import { FetchState } from '@/types/fetchState';
import { getCookie } from 'cookies-next';
import { useEffect, useState } from 'react';

const cookieToken = getCookie("access-token");

function useFetch<T>(endpoint: string, method: string = 'get', authToken: any = cookieToken) {
  const [state, setState] = useState<FetchState<T>>({
    data: null,
    loading: true,
    error: null,
  });

  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

  const fetchData = async () => {
    try {
      setState(prev => ({ ...prev, loading: true }));
      const response = await fetch(`${baseUrl}${endpoint}`, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        }
      });
      if (!response.ok) {
        throw new Error(`Failed to fetch: ${response.statusText}`);
      }
      const data = await response.json();
      setState({ data, loading: false, error: null });
    } catch (error: any) {
      setState({ data: null, loading: false, error: error.message });
    }
  };

  useEffect(() => {
    if (!baseUrl) {
      setState({ data: null, loading: false, error: 'Base URL is not defined' });
      return;
    }

    fetchData();

    // Optional cleanup if needed
    return () => {
      // Clean up if any async tasks
    };
  }, [endpoint, baseUrl]);

  return {
    ...state,
    refetch: fetchData,
  };
}

export default useFetch;
