// src/hooks/useFetch.ts
import { FetchState } from '@/types/fetchState';
import { useEffect, useState } from 'react';

function useFetch<T>(endpoint: string) {
  const [state, setState] = useState<FetchState<T>>({
    data: null,
    loading: true,
    error: null,
  });

  const baseUrl = process.env.API_BASE_URL;

  useEffect(() => {
    const fetchData = async () => {
      if (!baseUrl) {
        setState({ data: null, loading: false, error: 'Base URL is not defined' });
        return;
      }

      try {
        setState(prev => ({ ...prev, loading: true }));
        const response = await fetch(`${baseUrl}${endpoint}`); // Menggabungkan base URL dengan endpoint
        if (!response.ok) {
          throw new Error(`Failed to fetch: ${response.statusText}`);
        }
        const data = await response.json();
        setState({ data, loading: false, error: null });
      } catch (error: any) {
        setState({ data: null, loading: false, error: error.message });
      }
    };

    fetchData();
  }, [endpoint, baseUrl]); // Menambahkan baseUrl sebagai dependensi

  return state;
}

export default useFetch;
