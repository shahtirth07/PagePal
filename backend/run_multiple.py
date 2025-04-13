import subprocess
import time

ports = [5000, 5001, 5002]  # Ports for three instances

processes = []

try:
    for port in ports:
        # Set the PORT environment variable and run the Flask app
        process = subprocess.Popen(
            f"PORT={port} python app.py",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        processes.append(process)
        print(f"Started server on port {port}")
        time.sleep(2)  # Give each server time to start up

    print("\nServers are running on:")
    for port in ports:
        print(f"http://localhost:{port}")

    # Keep the script running
    input("\nPress Enter to stop all servers...")

finally:
    # Clean up: terminate all processes
    for process in processes:
        process.terminate()
    print("\nAll servers stopped.") 