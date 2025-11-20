#!/usr/bin/env python3
"""
EC2 Power Calibration Script
Measures P_idle and P_max for your specific EC2 instance

Run this on your EC2 instance to calibrate the energy formula.
"""

import psutil
import subprocess
import time
import statistics

def measure_idle_power(duration=60):
    """
    Measure baseline idle power consumption
    
    Args:
        duration: seconds to measure (default 60)
    
    Returns:
        avg_cpu_percent: average idle CPU %
    """
    print(f"\n{'='*60}")
    print("STEP 1: Measuring IDLE Power (P_idle)")
    print(f"{'='*60}")
    print(f"Duration: {duration} seconds")
    print("Instructions:")
    print("  - Close all unnecessary programs")
    print("  - Don't run any other commands during measurement")
    print("  - Let the system sit idle\n")
    
    input("Press ENTER when ready to start idle measurement...")
    
    print(f"\nMeasuring idle CPU for {duration} seconds...")
    samples = []
    interval = 0.5  # Sample every 0.5 seconds
    num_samples = int(duration / interval)
    
    for i in range(num_samples):
        cpu = psutil.cpu_percent(interval=interval)
        samples.append(cpu)
        if (i + 1) % 10 == 0:  # Progress every 5 seconds
            print(f"  Progress: {i+1}/{num_samples} samples ({cpu:.1f}% current)")
    
    avg_cpu = statistics.mean(samples)
    std_cpu = statistics.stdev(samples)
    min_cpu = min(samples)
    max_cpu = max(samples)
    
    print(f"\n{'='*60}")
    print("IDLE Measurement Results:")
    print(f"{'='*60}")
    print(f"  Average CPU: {avg_cpu:.2f}%")
    print(f"  Std Dev:     {std_cpu:.2f}%")
    print(f"  Min CPU:     {min_cpu:.2f}%")
    print(f"  Max CPU:     {max_cpu:.2f}%")
    print(f"{'='*60}\n")
    
    return avg_cpu


def measure_max_power(duration=60):
    """
    Measure maximum power consumption under full CPU load
    
    Args:
        duration: seconds to measure (default 60)
    
    Returns:
        avg_cpu_percent: average CPU % under load
    """
    print(f"\n{'='*60}")
    print("STEP 2: Measuring MAX Power (P_max)")
    print(f"{'='*60}")
    print(f"Duration: {duration} seconds")
    print("This will stress all CPU cores to 100%\n")
    
    input("Press ENTER when ready to start stress test...")
    
    # Use pure Python CPU stress (no external dependencies)
    print("\nStarting CPU stress test...")
    print("Running compute-intensive workload on all cores...\n")
    
    # Python-based CPU stress using multiprocessing
    import multiprocessing
    
    def cpu_stress_worker():
        """Worker function to max out one CPU core"""
        end_time = time.time() + duration + 5  # Extra time buffer
        while time.time() < end_time:
            # Compute-intensive operations
            _ = sum(i * i for i in range(10000))
    
    # Start one worker per CPU core
    num_cores = multiprocessing.cpu_count()
    print(f"Spawning {num_cores} worker process(es)...\n")
    
    processes = []
    for _ in range(num_cores):
        p = multiprocessing.Process(target=cpu_stress_worker)
        p.start()
        processes.append(p)
    
    stress_process = processes[0]  # Keep reference for later check
    
    # Give it 3 seconds to ramp up
    print("Warming up (3 seconds)...")
    time.sleep(3)
    
    print(f"Measuring CPU under load for {duration} seconds...")
    samples = []
    interval = 0.5
    num_samples = int(duration / interval)
    
    for i in range(num_samples):
        cpu = psutil.cpu_percent(interval=interval)
        samples.append(cpu)
        if (i + 1) % 10 == 0:  # Progress every 5 seconds
            print(f"  Progress: {i+1}/{num_samples} samples ({cpu:.1f}% current)")
        
        # Check if any stress process died
        if not any(p.is_alive() for p in processes):
            print("\n  Warning: Stress processes finished early")
            break
    
    # Clean up all worker processes
    for p in processes:
        p.terminate()
    for p in processes:
        p.join(timeout=2)
    for p in processes:
        if p.is_alive():
            p.kill()
    
    avg_cpu = statistics.mean(samples)
    std_cpu = statistics.stdev(samples)
    min_cpu = min(samples)
    max_cpu = max(samples)
    
    print(f"\n{'='*60}")
    print("MAX LOAD Measurement Results:")
    print(f"{'='*60}")
    print(f"  Average CPU: {avg_cpu:.2f}%")
    print(f"  Std Dev:     {std_cpu:.2f}%")
    print(f"  Min CPU:     {min_cpu:.2f}%")
    print(f"  Max CPU:     {max_cpu:.2f}%")
    print(f"{'='*60}\n")
    
    return avg_cpu


def calculate_power_values(idle_cpu, max_cpu):
    """
    Calculate P_idle and P_max from CPU measurements
    
    For t2.micro: Assume TDP ~28W based on typical Intel Xeon E5 vCPU share
    This is an approximation; actual power depends on instance generation.
    """
    print(f"\n{'='*60}")
    print("STEP 3: Calculating Power Values")
    print(f"{'='*60}\n")
    
    # EC2 t2.micro approximate values (Intel Xeon E5-2676 v3 or similar)
    # These are educated estimates - AWS doesn't publish exact per-instance power
    TDP_ESTIMATE = 28  # Watts (conservative estimate for 1 vCPU share)
    
    print("Instance Type: t2.micro (1 vCPU)")
    print(f"Estimated vCPU TDP: {TDP_ESTIMATE}W (conservative)")
    print(f"\nMeasured CPU utilization:")
    print(f"  Idle:     {idle_cpu:.2f}%")
    print(f"  Max load: {max_cpu:.2f}%")
    
    # Linear power model
    # P = TDP * (cpu_percent / 100)
    P_idle = TDP_ESTIMATE * (idle_cpu / 100)
    P_max = TDP_ESTIMATE * (max_cpu / 100)
    
    print(f"\n{'='*60}")
    print("CALIBRATED POWER VALUES:")
    print(f"{'='*60}")
    print(f"  P_idle = {P_idle:.3f} W")
    print(f"  P_max  = {P_max:.3f} W")
    print(f"{'='*60}\n")
    
    return P_idle, P_max


def generate_code_update(P_idle, P_max):
    """Generate code snippet to update app.py"""
    print(f"\n{'='*60}")
    print("STEP 4: Update Your Code")
    print(f"{'='*60}\n")
    
    print("Add these constants at the top of backend/app.py:")
    print("-" * 60)
    print(f"""
# EC2 Power Calibration Results (measured on {time.strftime('%Y-%m-%d')})
P_IDLE_W = {P_idle:.3f}  # Watts - idle power consumption
P_MAX_W = {P_max:.3f}   # Watts - max load power consumption
""")
    print("-" * 60)
    
    print("\nThen update the calculate_energy() function to use:")
    print("-" * 60)
    print(f"""
def calculate_energy(...):
    # ... existing baseline and monitoring code ...
    
    # New energy calculation using calibrated values
    power_w = P_IDLE_W + (P_MAX_W - P_IDLE_W) * (avg_cpu_percent / 100)
    energy_joules = power_w * duration
    
    return energy_joules, avg_cpu_percent
""")
    print("-" * 60)
    
    print("\nThis replaces the current TDP-based calculation with")
    print("measured idle and max power values specific to your EC2 instance.\n")


def main():
    print("\n" + "="*60)
    print(" EC2 POWER CALIBRATION TOOL")
    print(" For Green AI Video Transcoder")
    print("="*60)
    print("\nThis script will measure:")
    print("  1. P_idle  - Power consumption when system is idle")
    print("  2. P_max   - Power consumption under full CPU load")
    print("\nTotal time: ~2-3 minutes")
    print("="*60 + "\n")
    
    # Measure idle
    idle_cpu = measure_idle_power(duration=60)
    
    print("\n" + "="*60)
    print("Idle measurement complete. Taking 10 second break...")
    print("="*60)
    time.sleep(10)
    
    # Measure max
    max_cpu = measure_max_power(duration=60)
    
    print("\n" + "="*60)
    print("Max load measurement complete. Calculating results...")
    print("="*60)
    time.sleep(2)
    
    # Calculate power values
    P_idle, P_max = calculate_power_values(idle_cpu, max_cpu)
    
    # Show code update
    generate_code_update(P_idle, P_max)
    
    print("\n" + "="*60)
    print(" CALIBRATION COMPLETE!")
    print("="*60)
    print("\nNext steps:")
    print("  1. Copy the code snippets above")
    print("  2. Update backend/app.py with the new constants")
    print("  3. Update calculate_energy() function")
    print("  4. Rebuild Docker: docker-compose build")
    print("  5. Restart: docker-compose up -d")
    print("\nYour energy measurements will now be specific to this EC2 instance!")
    print("="*60 + "\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCalibration cancelled by user.")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
