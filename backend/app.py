from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import subprocess
import time
import psutil
import os
import cv2
import numpy as np
from openpyxl import Workbook, load_workbook
from datetime import datetime

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# Use parent directory for uploads/outputs
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'outputs')
RESULTS_FILE = os.path.join(BASE_DIR, 'outputs', 'results.xlsx')  # Save in outputs folder
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Carbon intensity (grams CO2 per kWh) - BESCOM Bangalore grid
# Source: BESCOM weighted average emission factor 2023-24: 0.71 tCO2/MWh
CARBON_INTENSITY = 710  # g CO2/kWh

def predict_optimal_preset(complexity, width, height, fps, size_mb):
    """
    Determine optimal FFmpeg preset based on video complexity
    Uses rule-based approach for reliable, interpretable results
    
    Strategy: Lower complexity → faster preset (save energy without quality loss)
             Higher complexity → balanced preset (maintain quality)
    """
    # Simple, proven logic based on complexity analysis
    if complexity < 3.5:
        # Low complexity (talking heads, static scenes)
        return 'ultrafast'
    elif complexity < 7.0:
        # Medium complexity (normal videos)
        return 'superfast'
    else:
        # High complexity (action, sports)
        return 'veryfast'
    
    presets = ['ultrafast', 'superfast', 'veryfast', 'fast', 'medium']
    return presets[preset_index]

def analyze_video_complexity(video_path):
    """
    Analyze video complexity using OpenCV
    Returns a complexity score from 0-10 based on:
    - Edge density (how detailed frames are)
    - Motion between frames
    """
    try:
        cap = cv2.VideoCapture(video_path)
        
        # Sample frames (every 10th frame to save processing time)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        sample_rate = max(1, frame_count // 20)  # Sample ~20 frames max
        
        edge_scores = []
        motion_scores = []
        prev_gray = None
        
        frame_idx = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Only process sampled frames
            if frame_idx % sample_rate == 0:
                # Convert to grayscale for analysis
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # 1. Edge Detection (Canny) - measures detail/complexity
                edges = cv2.Canny(gray, 50, 150)
                edge_density = np.count_nonzero(edges) / edges.size
                edge_scores.append(edge_density)
                
                # 2. Motion Detection - compare with previous frame
                if prev_gray is not None:
                    # Calculate absolute difference between frames
                    diff = cv2.absdiff(gray, prev_gray)
                    motion_density = np.mean(diff) / 255.0
                    motion_scores.append(motion_density)
                
                prev_gray = gray
            
            frame_idx += 1
        
        cap.release()
        
        # Calculate average scores
        avg_edge = np.mean(edge_scores) if edge_scores else 0
        avg_motion = np.mean(motion_scores) if motion_scores else 0
        
        # Normalize to 0-10 scale with better calibration
        # Typical edge density: 0.05-0.15, motion: 0.01-0.10
        edge_normalized = min(10, (avg_edge / 0.15) * 10)
        motion_normalized = min(10, (avg_motion / 0.10) * 10)
        
        # Complexity score: weighted combination
        # Edge contributes 60%, motion contributes 40%
        complexity = (edge_normalized * 0.6 + motion_normalized * 0.4)
        complexity = min(10, max(0, complexity))  # Clamp to 0-10
        
        print(f"Debug - Edge: {avg_edge:.4f} ({edge_normalized:.2f}/10), Motion: {avg_motion:.4f} ({motion_normalized:.2f}/10)")
        
        return round(complexity, 2)
    
    except Exception as e:
        print(f"Error analyzing video: {e}")
        return 5.0  # Default to medium complexity if analysis fails

def calculate_energy(duration, cpu_percent):
    """
    Calculate energy consumption in Joules
    Energy (J) = Power (W) × Time (s)
    """
    # AMD Ryzen 7 7735U - TDP: 28W (boost mode for heavy workloads)
    CPU_TDP = 28
    power_watts = CPU_TDP * (cpu_percent / 100)
    energy_joules = power_watts * duration
    return round(energy_joules, 2)

def calculate_co2(energy_joules):
    """
    Calculate CO2 emissions from energy consumption
    CO2 (g) = Energy (kWh) × Carbon Intensity (g CO2/kWh)
    """
    # Convert Joules to kWh (1 kWh = 3,600,000 J)
    energy_kwh = energy_joules / 3600000
    co2_grams = energy_kwh * CARBON_INTENSITY
    return round(co2_grams, 2)

def save_to_excel(data):
    """
    Save results to Excel file (append if exists, create if not)
    """
    try:
        print(f"Attempting to save to Excel: {RESULTS_FILE}")
        
        # Check if Excel file exists
        if os.path.exists(RESULTS_FILE):
            print("Excel file exists, loading...")
            wb = load_workbook(RESULTS_FILE)
            ws = wb.active
        else:
            # Create new workbook with headers
            print("Creating new Excel file...")
            wb = Workbook()
            ws = wb.active
            ws.append([
                'Timestamp', 'Filename', 'Complexity', 
                'Normal_Energy_J', 'Green_Energy_J', 'Savings_%',
                'CO2_Normal_g', 'CO2_Green_g', 'CO2_Saved_g'
            ])
        
        # Append new data
        ws.append([
            data['timestamp'],
            data['filename'],
            data['complexity'],
            data['normal_energy'],
            data['green_energy'],
            data['savings_percent'],
            data['co2_normal'],
            data['co2_green'],
            data['co2_saved']
        ])
        
        # Save workbook
        wb.save(RESULTS_FILE)
        print(f"✅ Results saved successfully to {RESULTS_FILE}")
    
    except Exception as e:
        print(f"❌ Error saving to Excel: {e}")
        import traceback
        traceback.print_exc()

@app.route('/upload', methods=['POST'])
def upload_video():
    print("=" * 80)
    print("🚀 UPLOAD ROUTE CALLED!")
    print("=" * 80)
    
    if 'video' not in request.files:
        return jsonify({'error': 'No video file'}), 400
    
    file = request.files['video']
    print(f"📹 File received: {file.filename}")
    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(input_path)
    print(f"💾 File saved to: {input_path}")
    
    # Extract video metadata
    try:
        cap = cv2.VideoCapture(input_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        cap.release()
        size_mb = os.path.getsize(input_path) / (1024 * 1024)
        
        video_info = {
            'width': width,
            'height': height,
            'fps': fps,
            'size_mb': size_mb
        }
        print(f"📊 Video: {width}x{height} @ {fps}fps, {size_mb:.2f}MB")
    except Exception as e:
        print(f"⚠️ Could not extract metadata: {e}")
        video_info = None
    
    # Step 1: Analyze video complexity
    print("Analyzing video complexity...")
    complexity = analyze_video_complexity(input_path)
    print(f"Complexity score: {complexity}/10")
    
    # Step 2: Normal transcoding (standard settings)
    normal_output = os.path.join(OUTPUT_FOLDER, 'normal_' + file.filename)
    normal_energy, normal_time, normal_settings = transcode_video(
        input_path, normal_output, 'normal', complexity, video_info
    )
    
    # Step 3: Green AI transcoding (ML-adaptive)
    green_output = os.path.join(OUTPUT_FOLDER, 'green_' + file.filename)
    green_energy, green_time, green_settings = transcode_video(
        input_path, green_output, 'green', complexity, video_info
    )
    
    # Step 4: Calculate savings and CO2
    savings = normal_energy - green_energy
    savings_percent = (savings / normal_energy) * 100 if normal_energy > 0 else 0
    
    co2_normal = calculate_co2(normal_energy)
    co2_green = calculate_co2(green_energy)
    co2_saved = co2_normal - co2_green
    
    # Step 5: Save to Excel
    excel_data = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'filename': file.filename,
        'complexity': complexity,
        'normal_energy': normal_energy,
        'green_energy': green_energy,
        'savings_percent': round(savings_percent, 2),
        'co2_normal': co2_normal,
        'co2_green': co2_green,
        'co2_saved': round(co2_saved, 2)
    }
    save_to_excel(excel_data)
    
    # Step 6: Return results with video URLs and settings
    return jsonify({
        'complexity': complexity,
        'normal_energy': normal_energy,
        'normal_time': normal_time,
        'normal_settings': normal_settings,
        'green_energy': green_energy,
        'green_time': green_time,
        'green_settings': green_settings,
        'savings': round(savings, 2),
        'savings_percent': round(savings_percent, 2),
        'co2_normal': co2_normal,
        'co2_green': co2_green,
        'co2_saved': round(co2_saved, 2),
        'normal_video_url': f'/outputs/normal_{file.filename}',
        'green_video_url': f'/outputs/green_{file.filename}'
    })

def transcode_video(input_path, output_path, mode, complexity, video_info=None):
    """
    Transcode video with mode-specific settings
    Mode 'green': Uses ML-based adaptive settings
    Mode 'normal': Uses standard quality settings
    Returns: (energy, duration, settings_dict)
    """
    cpu_percentages = []
    monitoring = {'active': True}  # Use dict for thread-safe flag
    
    # Get video metadata if provided
    width = video_info.get('width', 1920) if video_info else 1920
    height = video_info.get('height', 1080) if video_info else 1080
    fps = video_info.get('fps', 30) if video_info else 30
    size_mb = video_info.get('size_mb', 50) if video_info else 50
    
    # Measure baseline CPU before starting
    baseline_cpu = psutil.cpu_percent(interval=1.0)

    # Optional FFmpeg warm-up: run a very short FFmpeg invocation to initialize codecs
    # This helps exclude FFmpeg startup/initialization time from the measured duration.
    try:
        warmup_cmd = [
            'ffmpeg', '-hide_banner', '-loglevel', 'error',
            '-ss', '0', '-t', '0.1', '-i', input_path,
            '-f', 'null', '-'  # discard output
        ]
        # Run warm-up (do not fail the whole transcoding if warmup errors)
        subprocess.run(warmup_cmd, capture_output=True, text=True, timeout=10)
        print("FFmpeg warm-up completed")
    except Exception as e:
        print(f"FFmpeg warm-up failed (ignored): {e}")

    # Start CPU monitoring in background thread
    def monitor_cpu():
        while monitoring['active']:
            cpu_percentages.append(psutil.cpu_percent(interval=0.2))

    import threading
    monitor_thread = threading.Thread(target=monitor_cpu, daemon=True)

    # Use a high-resolution timer and start it immediately before the actual transcode
    start_time = time.perf_counter()
    monitor_thread.start()
    
    settings = {}  # Track all encoding settings
    
    if mode == 'green':
        # Green AI: Rule-based adaptive preset AND CRF selection
        preset = predict_optimal_preset(complexity, width, height, fps, size_mb)
        
        # Adaptive CRF: simpler videos can use higher CRF (more compression, smaller file)
        if complexity < 3.5:
            crf = '28'  # Low complexity: aggressive compression
        elif complexity < 7.0:
            crf = '26'  # Medium complexity: moderate compression
        else:
            crf = '24'  # High complexity: preserve quality
        
        settings = {
            'mode': 'Green AI (Adaptive)',
            'preset': preset,
            'crf': crf,
            'codec': 'H.264 (libx264)',
            'threads': 4,
            'optimization': f'Complexity-based: {preset} preset + CRF {crf} for complexity {complexity:.1f}/10',
            'strategy': 'Faster encoding + higher compression for simple content = energy + bandwidth savings'
        }
        
        print(f"🌱 Green AI: complexity={complexity:.1f} → preset={preset}, CRF={crf}")
        
        cmd = [
            'ffmpeg', '-i', input_path,
            '-c:v', 'libx264',
            '-preset', preset,
            '-crf', crf,
            '-threads', '4',
            '-y', output_path
        ]
    else:
        # Normal: Standard quality settings (no adaptation)
        preset = 'medium'
        crf = '23'
        
        settings = {
            'mode': 'Standard (Fixed)',
            'preset': preset,
            'crf': crf,
            'codec': 'H.264 (libx264)',
            'threads': 4,
            'optimization': 'None (baseline)',
            'strategy': 'Fixed medium preset for all videos'
        }
        
        cmd = [
            'ffmpeg', '-i', input_path,
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-threads', '4',
            '-y', output_path
        ]
    
    # Run FFmpeg transcoding
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    end_time = time.perf_counter()
    
    # Stop monitoring and wait for thread
    monitoring['active'] = False
    time.sleep(0.3)  # Give thread time to finish
    
    # Calculate metrics
    duration = end_time - start_time
    
    # Subtract baseline CPU to get only transcoding CPU usage
    transcoding_cpu_samples = [max(0, cpu - baseline_cpu) for cpu in cpu_percentages]
    avg_cpu = sum(transcoding_cpu_samples) / len(transcoding_cpu_samples) if transcoding_cpu_samples else 50
    
    energy = calculate_energy(duration, avg_cpu)
    
    # Add runtime metrics to settings
    settings['duration'] = f"{duration:.2f}s"
    settings['avg_cpu'] = f"{avg_cpu:.1f}%"
    settings['energy'] = f"{energy}J"
    
    # Get output file size
    if os.path.exists(output_path):
        output_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        settings['output_size'] = f"{output_size_mb:.2f} MB"
    
    print(f"{mode} mode: duration={duration:.2f}s, baseline_cpu={baseline_cpu:.1f}%, avg_cpu={avg_cpu:.1f}%, energy={energy}J, preset={preset}")
    
    return energy, round(duration, 2), settings

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/outputs/<filename>')
def serve_output(filename):
    """Serve transcoded video files"""
    return send_from_directory(OUTPUT_FOLDER, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False, port=5000)
