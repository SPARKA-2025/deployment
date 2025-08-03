import subprocess
import json

def test_grpc_from_container():
    """Test gRPC connections from inside the container"""
    print("=== TESTING gRPC CONNECTIONS FROM CONTAINER ===")
    print("="*60)
    
    # Test if we can reach the gRPC services from inside container
    container_name = "sparka-server-api-dev"
    
    # Test 1: Check if host.docker.internal is reachable
    print("\n1. Testing host.docker.internal connectivity...")
    try:
        result = subprocess.run([
            "docker", "exec", container_name, 
            "ping", "-c", "1", "host.docker.internal"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ host.docker.internal is reachable")
        else:
            print("❌ host.docker.internal is NOT reachable")
            print(f"Error: {result.stderr}")
    except Exception as e:
        print(f"❌ Error testing host.docker.internal: {e}")
    
    # Test 2: Check if gRPC ports are accessible
    ports = ["50051", "50052", "50053"]
    services = ["OCR", "Plate", "Vehicle"]
    
    print("\n2. Testing gRPC port connectivity...")
    for port, service in zip(ports, services):
        try:
            result = subprocess.run([
                "docker", "exec", container_name,
                "nc", "-z", "host.docker.internal", port
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                print(f"✅ {service} service (port {port}) is reachable")
            else:
                print(f"❌ {service} service (port {port}) is NOT reachable")
        except Exception as e:
            print(f"❌ Error testing {service} port {port}: {e}")
    
    # Test 3: Check Python gRPC import
    print("\n3. Testing Python gRPC imports in container...")
    try:
        result = subprocess.run([
            "docker", "exec", container_name,
            "python", "-c", "import grpc; print('gRPC import successful')"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ gRPC Python module is available")
            print(f"Output: {result.stdout.strip()}")
        else:
            print("❌ gRPC Python module import failed")
            print(f"Error: {result.stderr}")
    except Exception as e:
        print(f"❌ Error testing gRPC import: {e}")
    
    # Test 4: Check if we can create a simple gRPC connection
    print("\n4. Testing simple gRPC connection...")
    grpc_test_code = '''
import grpc
import sys
try:
    channel = grpc.insecure_channel("host.docker.internal:50053")
    grpc.channel_ready_future(channel).result(timeout=5)
    print("SUCCESS: gRPC connection established")
except Exception as e:
    print(f"ERROR: gRPC connection failed: {e}")
    sys.exit(1)
'''
    
    try:
        result = subprocess.run([
            "docker", "exec", container_name,
            "python", "-c", grpc_test_code
        ], capture_output=True, text=True, timeout=15)
        
        print(f"Output: {result.stdout.strip()}")
        if result.stderr:
            print(f"Error: {result.stderr.strip()}")
            
    except Exception as e:
        print(f"❌ Error testing gRPC connection: {e}")
    
    print("\n=== SUMMARY ===")
    print("If any of the above tests failed, that's likely the root cause.")
    print("If all tests passed, the issue might be in the server code logic.")

if __name__ == '__main__':
    test_grpc_from_container()