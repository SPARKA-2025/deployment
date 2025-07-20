import time
import multiprocessing
import psutil
import numpy as np
import os

def cpu_benchmark(n=10000000):
    start = time.time()
    result = sum(i * i for i in range(n))  # A CPU-bound operation
    end = time.time()
    return end - start  # Time taken for the operation

def multi_core_benchmark():
    """Benchmark CPU performance using multiple cores."""
    num_cores = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(processes=num_cores)  # Pool with num_cores workers
    tasks = [10000000] * num_cores  # Each core gets the same workload

    start = time.time()
    # Use pool.map to execute cpu_benchmark on each core
    pool_results = pool.map(cpu_benchmark, tasks)
    pool.close()
    pool.join()  # Wait for all processes to complete
    end = time.time()

    # Return the total time and average time per task
    total_time = end - start
    avg_time = total_time / num_cores
    return total_time, avg_time

def memory_benchmark(size_in_gb=1):
    # Allocate memory to test
    size_in_bytes = size_in_gb * 1024 * 1024 * 1024
    start = time.time()
    
    # Create an array of random numbers
    data = np.random.random(size_in_bytes // 8)  # Each float64 is 8 bytes
    
    end = time.time()
    memory_usage = psutil.virtual_memory().used / (1024 ** 3)  # Memory used in GB
    elapsed_time = end - start
    print(f"Allocated {size_in_gb} GB, Time taken: {elapsed_time:.4f} seconds")
    return elapsed_time, memory_usage

def disk_benchmark(file_path="test_file.tmp", file_size_mb=100):
    # Write to a file
    with open(file_path, 'wb') as f:
        start = time.time()
        f.write(os.urandom(file_size_mb * 1024 * 1024))  # Write random data
        write_time = time.time() - start
    
    # Read from the file
    with open(file_path, 'rb') as f:
        start = time.time()
        _ = f.read()
        read_time = time.time() - start

    # Clean up
    os.remove(file_path)
    
    print(f"Disk Write Time: {write_time:.4f} seconds")
    print(f"Disk Read Time: {read_time:.4f} seconds")
    return write_time, read_time

# Test disk I/O performance


if __name__ == "__main__":
    single_core_time = cpu_benchmark()
    print(f"Single-Core CPU Benchmark: {single_core_time} seconds")
    
    multi_core_time, avg_core_time = multi_core_benchmark()
    print(f"Total Multi-Core Benchmark Time: {multi_core_time:.4f} seconds")
    print(f"Average Time per Core: {avg_core_time:.4f} seconds")

    time_taken, memory_used = memory_benchmark(4)
    print(f"Memory Usage After Test: {memory_used} GB")

    disk_benchmark()
