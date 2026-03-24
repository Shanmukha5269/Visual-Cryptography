// Visual Cryptography Tool - Frontend JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Mode selection buttons
    const encryptBtn = document.getElementById('encrypt-btn');
    const decryptBtn = document.getElementById('decrypt-btn');

    // Sections
    const encryptSection = document.getElementById('encrypt-section');
    const decryptSection = document.getElementById('decrypt-section');

    // Action buttons
    const encryptActionBtn = document.getElementById('encrypt-btn-action');
    const decryptActionBtn = document.getElementById('decrypt-btn-action');

    // Loading and results
    const loadingDiv = document.getElementById('loading');
    const resultsDiv = document.getElementById('results');
    const imageGrid = document.getElementById('image-grid');
    const metricsDiv = document.getElementById('metrics');

    // Mode switching
    encryptBtn.addEventListener('click', () => switchMode('encrypt'));
    decryptBtn.addEventListener('click', () => switchMode('decrypt'));

    function switchMode(mode) {
        // Update button states
        encryptBtn.classList.toggle('active', mode === 'encrypt');
        decryptBtn.classList.toggle('active', mode === 'decrypt');

        // Show/hide sections
        encryptSection.classList.toggle('active', mode === 'encrypt');
        decryptSection.classList.toggle('active', mode === 'decrypt');

        // Hide results
        resultsDiv.classList.add('hidden');
        metricsDiv.classList.add('hidden');
    }

    // Encrypt functionality
    encryptActionBtn.addEventListener('click', async () => {
        const fileInput = document.getElementById('encrypt-file');
        const sharesSelect = document.getElementById('shares-select');

        if (!fileInput.files[0]) {
            alert('Please select an image file.');
            return;
        }

        clearResults();

        const formData = new FormData();
        formData.append('image', fileInput.files[0]);
        formData.append('shares', sharesSelect.value);

        showLoading();

        try {
            const response = await fetch('/encrypt', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Encryption failed');
            }

            const data = await response.json();
            displayResults(data.shares, 'shares');
            if (data.metrics) {
                displayMetrics(data.metrics);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred during encryption.');
        } finally {
            hideLoading();
        }
    });

    // Decrypt functionality
    decryptActionBtn.addEventListener('click', async () => {
        const fileInput = document.getElementById('decrypt-files');
        const sharesSelect = document.getElementById('decrypt-shares-select');

        if (fileInput.files.length === 0) {
            alert('Please select share image files.');
            return;
        }

        clearResults();

        const formData = new FormData();
        for (let i = 0; i < fileInput.files.length; i++) {
            formData.append('shares', fileInput.files[i]);
        }
        formData.append('num_shares', sharesSelect.value);

        showLoading();

        try {
            const response = await fetch('/decrypt', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Decryption failed');
            }

            const data = await response.json();
            displayResults([data.reconstructed], 'reconstructed');
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred during decryption.');
        } finally {
            hideLoading();
        }
    });

    function showLoading() {
        loadingDiv.classList.remove('hidden');
        encryptActionBtn.disabled = true;
        decryptActionBtn.disabled = true;
    }

    function hideLoading() {
        loadingDiv.classList.add('hidden');
        encryptActionBtn.disabled = false;
        decryptActionBtn.disabled = false;
    }

    function clearResults() {
        imageGrid.innerHTML = '';
        resultsDiv.classList.add('hidden');
        metricsDiv.classList.add('hidden');
        metricsDiv.innerHTML = '';
    }

    function displayResults(images, type) {
        imageGrid.innerHTML = '';

        images.forEach((imagePath, index) => {
            const imageItem = document.createElement('div');
            imageItem.className = 'image-item';

            const img = document.createElement('img');
            img.src = imagePath;
            img.alt = type === 'shares' ? `Share ${index + 1}` : 'Reconstructed Image';

            const downloadBtn = document.createElement('button');
            downloadBtn.className = 'download-btn';
            downloadBtn.textContent = 'Download';
            downloadBtn.addEventListener('click', () => downloadImage(imagePath, type, index));

            imageItem.appendChild(img);
            imageItem.appendChild(downloadBtn);
            imageGrid.appendChild(imageItem);
        });

        resultsDiv.classList.remove('hidden');
    }

    function displayMetrics(metrics) {
        metricsDiv.innerHTML = `
            <h3>Quality Metrics</h3>
            <p>PSNR: ${metrics.psnr.toFixed(2)} dB</p>
            <p>Mean NCORR: ${metrics.nxcorr.toFixed(4)}</p>
        `;
        metricsDiv.classList.remove('hidden');
    }

    function downloadImage(imagePath, type, index) {
        const link = document.createElement('a');
        link.href = imagePath;
        link.download = type === 'shares' ? `XOR_Share_${index + 1}.png` : 'Output_XOR.png';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
});