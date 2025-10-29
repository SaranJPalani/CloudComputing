// Use relative URL so it works both locally and with ngrok
const API_URL = window.location.origin;

async function uploadVideo() {
    const fileInput = document.getElementById('videoInput');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Please select a video file');
        return;
    }
    
    const formData = new FormData();
    formData.append('video', file);
    
    // Show loading
    document.getElementById('loading').style.display = 'block';
    document.getElementById('results').style.display = 'none';
    
    try {
        const response = await fetch(`${API_URL}/upload`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        displayResults(data);
    } catch (error) {
        alert('Error: ' + error.message);
    } finally {
        document.getElementById('loading').style.display = 'none';
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
    
    // Energy metrics
    document.getElementById('normalEnergy').textContent = `${data.normal_energy} J`;
    document.getElementById('normalTime').textContent = `${data.normal_time} seconds`;
    
    document.getElementById('greenEnergy').textContent = `${data.green_energy} J`;
    document.getElementById('greenTime').textContent = `${data.green_time} seconds`;
    
    // Savings
    document.getElementById('savingsText').textContent = `${data.savings_percent}% energy reduction`;
    document.getElementById('savingsValue').textContent = `${data.savings} Joules saved`;
    
    // Video players
    const normalVideo = document.getElementById('normalVideo');
    const greenVideo = document.getElementById('greenVideo');
    
    normalVideo.src = data.normal_video_url;
    greenVideo.src = data.green_video_url;
    
    // Display settings panels
    displaySettings('normalSettings', data.normal_settings);
    displaySettings('greenSettings', data.green_settings);
    
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
