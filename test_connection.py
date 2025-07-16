"""
Example script to demonstrate gRPC server connectivity
"""

import time
import logging
import threading
import grpc
from concurrent import futures

def test_server_connection():
    """Test basic gRPC server connection"""
    print("Testing gRPC server connection...")
    
    try:
        # Create a channel to the server
        channel = grpc.insecure_channel('localhost:50051')
        
        # Test if the channel is ready
        grpc.channel_ready_future(channel).result(timeout=5)
        
        print("✓ Successfully connected to gRPC server on localhost:50051")
        print("  Server is accepting connections")
        
        # Close the channel
        channel.close()
        
        return True
        
    except grpc.RpcError as e:
        print(f"✗ gRPC connection error: {e}")
        return False
    except Exception as e:
        print(f"✗ Connection error: {e}")
        return False

def main():
    """Main test function"""
    print("InsightPilot gRPC Server Connection Test")
    print("=" * 45)
    
    print("\nInstructions:")
    print("1. Start InsightPilot in standalone mode:")
    print("   python run_insightpilot.py --mode standalone")
    print("2. Wait for the server to start (check status bar)")
    print("3. Run this test script in another terminal")
    print("4. The test will attempt to connect to the server")
    
    print("\n" + "=" * 45)
    
    # Test connection
    success = test_server_connection()
    
    if success:
        print("\n✓ Connection test passed!")
        print("  The gRPC server is running and accessible")
        print("  External clients can connect to the server")
    else:
        print("\n✗ Connection test failed!")
        print("  Make sure InsightPilot is running in standalone mode")
        print("  Check that the server started successfully")
    
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
