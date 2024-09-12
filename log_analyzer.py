import platform
import os
import psutil
import shutil
import socket
import subprocess
import time
import re
from collections import defaultdict
from operator import itemgetter

# System Information Functions

def get_os_info():
    # Retrieves operating system details
    return platform.system(), platform.release(), platform.version(), platform.machine()

def get_network_data():
    # Retrieves network details including hostname, private IP, public IP, and default gateway
    hostname = socket.gethostname()
    private_ip = socket.gethostbyname(hostname)
    public_ip = subprocess.getoutput("curl -s ifconfig.me")
    if platform.system() == "Windows":
        default_gateway = subprocess.getoutput("ipconfig | findstr /i \"Gateway\"").split()[-1]
    else:
        default_gateway = subprocess.getoutput("ip route | grep default | awk '{print $3}'")
    return hostname, private_ip, public_ip, default_gateway

def get_disk_stats():
    # Retrieves disk partition details and total/used/free disk space
    partitions = psutil.disk_partitions()
    total, used, free = shutil.disk_usage("/")
    return partitions, total, used, free

def get_largest_dirs(path='/', n=5):
    # Retrieves the largest directories based on size within a specified path
    dir_sizes = defaultdict(int)
    for root, dirs, files in os.walk(path, topdown=True):
        # Exclude certain system directories
        dirs[:] = [d for d in dirs if not d.startswith('proc') and not d.startswith('sys') and not d.startswith('dev')]
        for f in files:
            fp = os.path.join(root, f)
            try:
                if os.access(fp, os.R_OK):  # Check if the file is readable
                    dir_sizes[root] += os.path.getsize(fp)
            except (FileNotFoundError, PermissionError):
                continue
    largest_dirs = sorted(dir_sizes.items(), key=itemgetter(1), reverse=True)[:n]
    return largest_dirs

def monitor_cpu_usage(interval=10):
    # Monitors CPU usage and prints current usage every specified interval
    try:
        while True:  # Run indefinitely until interrupted
            cpu_usage = psutil.cpu_percent(interval=interval)
            print(f"Current CPU Usage: {cpu_usage}%")
            time.sleep(interval)  # Wait for the specified interval before checking again
    except KeyboardInterrupt:
        print("\nCPU monitoring stopped.")

# Log Parsing Functions

def parse_auth_log(file_path):
    # Parses authentication log file for various user activities
    regex_patterns = {
        "timestamp": r'^(.*?)\s',
        "user_cmd": r'(\w+)\s+:\s+(\w+)\[(\d+)\]:\s+(\S+)',
        "new_user": r'useradd\s+.*?\s+(\w+)$',
        "del_user": r'userdel\s+.*?\s+(\w+)$',
        "passwd_change": r'passwd\s+(\w+)',
        "su_command": r'su\s+\S+\s+to\s+(\w+)',
        "sudo_command": r'sudo\s+(\S+)',
        "sudo_fail": r'(\w+)\s+.*?sudo.*?authentication\s+failure'
    }
    
    try:
        with open(file_path, 'r') as log_file:
            for line in log_file:
                print(line)  # Print each line to check input
                timestamp_match = re.search(regex_patterns["timestamp"], line)
                timestamp = timestamp_match.group(1) if timestamp_match else "Unknown"
                print(timestamp_match) 

                # Extract command usage
                user_cmd_match = re.search(regex_patterns["user_cmd"], line)
                if user_cmd_match:
                    executing_user = user_cmd_match.group(2)
                    command = user_cmd_match.group(4)
                    print(f"{timestamp} - User: {executing_user} executed Command: {command}")
                    continue

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

# Main Function

def main():
    # Retrieves and displays various system information
    
    os_name, os_version, os_release, os_machine = get_os_info()
    print(f"\n=== Operating System Details ===")
    print(f"Operating System: {os_name} {os_version}")
    print(f"Version: {os_release}")
    print(f"Machine: {os_machine}")

    hostname, private_ip, public_ip, default_gateway = get_network_data()
    print(f"\n=== Network Details ===")
    print(f"Hostname: {hostname}")
    print(f"Private IP: {private_ip}")
    print(f"Public IP: {public_ip}")
    print(f"Default Gateway: {default_gateway}")

    partitions, total, used, free = get_disk_stats()
    print(f"\n=== Disk Details ===")
    print("Partitions:")
    for partition in partitions:
        print(f"  {partition}")
    print(f"Total Disk Size: {total} bytes")
    print(f"Used Disk Space: {used} bytes")
    print(f"Free Disk Space: {free} bytes")

    largest_dirs = get_largest_dirs()
    print("\n=== Largest Directories ===")
    for i, (dir, size) in enumerate(largest_dirs, 1):
        print(f"{i}. {dir}: {size} bytes")

    print("\n=== CPU Monitoring (Press Ctrl+C to stop) ===")
    monitor_cpu_usage(interval=10)  # Starts monitoring CPU usage with a 10-second interval

    print("\n=== Parsing auth.log ===")
    log_file_path = input("Enter the path to the auth.log file (press Enter to use default '/var/log/auth.log'): ")
    if not log_file_path: 
        log_file_path = '/var/log/auth.log'
    parse_auth_log(log_file_path)

if __name__ == "__main__":
    main()

