// Use relative URL so it works both locally and with ngrok
const API_URL = window.location.origin;

// Global carbon intensity state
let carbonIntensity = 710; // Default: Karnataka, India
let carbonRegion = 'Karnataka, India (default)';

// Request geolocation and carbon intensity on page load
window.addEventListener('DOMContentLoaded', async () => {
    console.log('🌍 Requesting geolocation...');
    
    if ('geolocation' in navigator) {
        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                console.log(`✅ Location: ${lat}, ${lon}`);
                
                // Call backend to get carbon intensity
                try {
                    const response = await fetch(`${API_URL}/api/carbon-intensity`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ latitude: lat, longitude: lon })
                    });
                    
                    const data = await response.json();
                    carbonIntensity = data.intensity;
                    carbonRegion = data.region;
                    
                    console.log(`📍 Carbon intensity: ${carbonRegion} = ${carbonIntensity} g/kWh`);
                    updateLocationDisplay(carbonRegion, carbonIntensity, data.source);
                } catch (error) {
                    console.error('Carbon intensity API error:', error);
                    updateLocationDisplay(carbonRegion, carbonIntensity, 'default');
                }
            },
            (error) => {
                console.log(`❌ Geolocation denied: ${error.message}`);
                updateLocationDisplay(carbonRegion, carbonIntensity, 'default');
            }
        );
    } else {
        console.log('❌ Geolocation not supported');
        updateLocationDisplay(carbonRegion, carbonIntensity, 'default');
    }
});

function updateLocationDisplay(region, intensity, source) {
    const locationElement = document.getElementById('carbonLocation');
    if (locationElement) {
        const sourceIcon = source === 'gemini' ? '🤖' : '📍';
        locationElement.innerHTML = `${sourceIcon} <strong>${region}</strong> - ${intensity} g CO₂/kWh`;
        locationElement.style.display = 'block';
    }
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        console.log(`📁 File selected: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`);
    }
}

let isUploading = false; // Prevent double-submit

async function uploadVideo() {
    console.log('🚀 uploadVideo() called, isUploading:', isUploading);
    
    if (isUploading) {
        console.warn('⚠️ Upload already in progress, ignoring duplicate call');
        return;
    }
    
    const fileInput = document.getElementById('videoInput');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Please select a video file');
        return;
    }
    
    isUploading = true;
    console.log(`📤 Starting upload: ${file.name}`);
    
    const formData = new FormData();
    formData.append('video', file);
    formData.append('carbon_intensity', carbonIntensity); // Include carbon intensity
    
    // Show loading
    document.getElementById('loading').style.display = 'block';
    document.getElementById('results').style.display = 'none';
    updateLoadingMessage('Uploading video...');
    
    try {
        // Submit video - server returns immediately with job ID
        const response = await fetch(`${API_URL}/upload`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        
        const data = await response.json();
        const jobId = data.job_id;
        console.log(`✅ Job created: ${jobId}`);
        
        // Poll for completion
        await pollJobStatus(jobId);
        
    } catch (error) {
        console.error('❌ Upload error:', error);
        alert('Error: ' + error.message);
        document.getElementById('loading').style.display = 'none';
        isUploading = false;
    }
}

async function pollJobStatus(jobId) {
    const pollInterval = 2000; // Poll every 2 seconds
    
    while (true) {
        try {
            const response = await fetch(`${API_URL}/status/${jobId}`);
            
            if (!response.ok) {
                throw new Error(`Status check failed: ${response.status}`);
            }
            
            const status = await response.json();
            console.log(`📊 Job progress: ${status.progress}%`);
            
            // Update loading message based on progress
            if (status.progress < 20) {
                updateLoadingMessage('Analyzing video complexity...');
            } else if (status.progress < 50) {
                updateLoadingMessage('Processing normal mode...');
            } else if (status.progress < 80) {
                updateLoadingMessage('Processing rule-based mode...');
            } else if (status.progress < 100) {
                updateLoadingMessage('Processing ML mode...');
            }
            
            if (status.status === 'completed') {
                console.log('✅ Job completed, displaying results');
                displayResults(status.result);
                document.getElementById('loading').style.display = 'none';
                isUploading = false;
                break;
            } else if (status.status === 'failed') {
                throw new Error(status.error || 'Processing failed');
            }
            
            // Wait before next poll
            await new Promise(resolve => setTimeout(resolve, pollInterval));
            
        } catch (error) {
            console.error('❌ Polling error:', error);
            alert('Error checking status: ' + error.message);
            document.getElementById('loading').style.display = 'none';
            isUploading = false;
            break;
        }
    }
}

function updateLoadingMessage(message) {
    const loadingDiv = document.getElementById('loading');
    // Update the loading message text (assumes you have a <p> inside loading div)
    const messageEl = loadingDiv.querySelector('p');
    if (messageEl) {
        messageEl.textContent = message;
    }
}

function displayResults(data) {
    // Complexity info
    document.getElementById('complexityScore').textContent = `${data.complexity}/10`;
    
    let complexityLabel = 'Medium';
    if (data.complexity < 3.5) complexityLabel = 'Low (Simple video)';
    else if (data.complexity < 7.0) complexityLabel = 'Medium (Normal video)';
    else complexityLabel = 'High (Complex video)';
    document.getElementById('complexityLabel').textContent = complexityLabel;
    
    // File size metrics
    document.getElementById('normalSize').textContent = `${data.normal_size_mb} MB`;
    document.getElementById('ruleSize').textContent = `${data.rule_size_mb} MB`;
    document.getElementById('mlSize').textContent = `${data.ml_size_mb} MB`;
    
    // Energy metrics for all 3 methods
    document.getElementById('normalEnergy').textContent = `${data.normal_energy} J`;
    document.getElementById('normalTime').textContent = `${data.normal_time}s`;
    
    document.getElementById('ruleEnergy').textContent = `${data.rule_energy} J`;
    document.getElementById('ruleTime').textContent = `${data.rule_time}s`;
    document.getElementById('ruleSavings').textContent = `${data.rule_savings_percent}% saved`;
    
    document.getElementById('mlEnergy').textContent = `${data.ml_energy} J`;
    document.getElementById('mlTime').textContent = `${data.ml_time}s`;
    document.getElementById('mlSavings').textContent = `${data.ml_savings_percent}% saved`;
    
    // Storage savings
    document.getElementById('ruleStorageSaved').textContent = 
        `${data.rule_storage_saved_mb >= 0 ? '+' : ''}${data.rule_storage_saved_mb.toFixed(2)} MB (${data.rule_storage_saved_percent >= 0 ? '+' : ''}${data.rule_storage_saved_percent.toFixed(1)}%)`;
    document.getElementById('mlStorageSaved').textContent = 
        `${data.ml_storage_saved_mb >= 0 ? '+' : ''}${data.ml_storage_saved_mb.toFixed(2)} MB (${data.ml_storage_saved_percent >= 0 ? '+' : ''}${data.ml_storage_saved_percent.toFixed(1)}%)`;
    
    // CO2 reduction
    document.getElementById('normalCO2').textContent = `${data.co2_normal.toFixed(4)} g CO₂`;
    document.getElementById('ruleCO2').textContent = `${data.co2_rule.toFixed(4)} g CO₂`;
    document.getElementById('mlCO2').textContent = `${data.co2_ml.toFixed(4)} g CO₂`;
    
    document.getElementById('ruleCO2Saved').textContent = `${data.co2_rule_saved.toFixed(4)} g CO₂ saved`;
    document.getElementById('mlCO2Saved').textContent = `${data.co2_ml_saved.toFixed(4)} g CO₂ saved`;
    
    // Determine best method based on lowest energy consumption
    let bestMethod, bestEnergy, bestSavings, bestCO2, co2Saved;
    if (data.rule_energy < data.ml_energy) {
        bestMethod = 'Rule-based Adaptive';
        bestEnergy = data.rule_energy;
        bestSavings = data.rule_savings_percent;
        bestCO2 = data.co2_rule;
        co2Saved = data.co2_rule_saved;
    } else {
        bestMethod = 'ML-Optimized';
        bestEnergy = data.ml_energy;
        bestSavings = data.ml_savings_percent;
        bestCO2 = data.co2_ml;
        co2Saved = data.co2_ml_saved;
    }
    
    document.getElementById('savingsText').textContent = 
        `${bestSavings}% energy saved (${bestMethod} - ${bestEnergy}J consumed)`;
    document.getElementById('savingsValue').textContent = 
        `CO₂: ${co2Saved.toFixed(4)}g saved (Energy → kWh × 0.716 g/kWh Karnataka grid)`;
    
    // Video players
    const normalVideo = document.getElementById('normalVideo');
    const ruleVideo = document.getElementById('ruleVideo');
    const mlVideo = document.getElementById('mlVideo');
    
    normalVideo.src = data.normal_video_url;
    ruleVideo.src = data.rule_video_url;
    mlVideo.src = data.ml_video_url;
    
    // CO2 under video players
    document.getElementById('normalVideoCO2').textContent = `CO₂: ${data.co2_normal.toFixed(4)}g`;
    document.getElementById('ruleVideoCO2').textContent = `CO₂: ${data.co2_rule.toFixed(4)}g`;
    document.getElementById('mlVideoCO2').textContent = `CO₂: ${data.co2_ml.toFixed(4)}g`;
    document.getElementById('ruleVideoCO2Saved').textContent = `✓ ${data.co2_rule_saved.toFixed(4)}g saved`;
    document.getElementById('mlVideoCO2Saved').textContent = `✓ ${data.co2_ml_saved.toFixed(4)}g saved`;
    
    // Display settings panels for all 3 methods
    displaySettings('normalSettings', data.normal_settings);
    displaySettings('ruleSettings', data.rule_settings);
    displaySettings('mlSettings', data.ml_settings);
    
    document.getElementById('results').style.display = 'block';
}

function displaySettings(elementId, settings) {
    const panel = document.getElementById(elementId);
    
    // Clear existing content except title
    const title = panel.querySelector('h5');
    panel.innerHTML = '';
    panel.appendChild(title);
    
    // Create settings table
    const table = document.createElement('div');
    table.className = 'settings-table';
    
    const settingsOrder = [
        { key: 'mode', label: 'Mode', icon: '🎯' },
        { key: 'preset', label: 'Preset', icon: '⚡' },
        { key: 'codec', label: 'Codec', icon: '🎬' },
        { key: 'crf', label: 'Quality (CRF)', icon: '💎' },
        { key: 'duration', label: 'Duration', icon: '⏱️' },
        { key: 'avg_cpu', label: 'Avg CPU', icon: '💻' },
        { key: 'energy', label: 'Energy Used', icon: '⚡' },
        { key: 'output_size', label: 'File Size', icon: '📦' },
        { key: 'optimization', label: 'Optimization', icon: '🤖' }
    ];
    
    settingsOrder.forEach(({ key, label, icon }) => {
        if (settings[key]) {
            const row = document.createElement('div');
            row.className = 'settings-row';
            row.innerHTML = `
                <span class="settings-label">${icon} ${label}:</span>
                <span class="settings-value">${settings[key]}</span>
            `;
            table.appendChild(row);
        }
    });
    
    // Add strategy note if present
    if (settings.strategy) {
        const note = document.createElement('div');
        note.className = 'settings-note';
        note.textContent = settings.strategy;
        table.appendChild(note);
    }
    
    panel.appendChild(table);
}
