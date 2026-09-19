/**
 * Digital Consumer Complaint Registration & Grievance Redressal System
 * Frontend Interactions & File Preview Utilities
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Auto dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-8px)';
            alert.style.transition = 'all 0.4s ease';
            setTimeout(() => alert.remove(), 400);
        }, 6000);
    });

    // 2. Drag & Drop File Upload with Preview
    const dropzone = document.getElementById('fileDropzone');
    const fileInput = document.getElementById('fileUploadInput');
    const fileInfoContainer = document.getElementById('fileInfoContainer');
    const fileNameDisplay = document.getElementById('fileNameDisplay');
    const filePreviewImg = document.getElementById('filePreviewImg');

    if (dropzone && fileInput) {
        // Clicking dropzone triggers file input
        dropzone.addEventListener('click', () => fileInput.click());

        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.remove('dragover');
            }, false);
        });

        dropzone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length) {
                fileInput.files = files;
                handleFileSelection(files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length) {
                handleFileSelection(e.target.files[0]);
            }
        });
    }

    function handleFileSelection(file) {
        if (!file) return;

        if (fileInfoContainer && fileNameDisplay) {
            fileNameDisplay.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
            fileInfoContainer.style.display = 'block';
        }

        // Show image thumbnail if file is an image
        if (filePreviewImg && file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (e) => {
                filePreviewImg.src = e.target.result;
                filePreviewImg.style.display = 'block';
            };
            reader.readAsDataURL(file);
        } else if (filePreviewImg) {
            filePreviewImg.style.display = 'none';
        }
    }

    // 3. Live search filter for tables
    const tableSearchInput = document.getElementById('tableSearchInput');
    if (tableSearchInput) {
        tableSearchInput.addEventListener('keyup', (e) => {
            const term = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('.data-table tbody tr');
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(term) ? '' : 'none';
            });
        });
    }

    // 4. Character count for complaint description
    const descTextarea = document.querySelector('textarea[name="description"]');
    const charCounter = document.getElementById('charCounter');
    if (descTextarea && charCounter) {
        const updateCount = () => {
            const len = descTextarea.value.length;
            charCounter.textContent = `${len} characters entered`;
        };
        descTextarea.addEventListener('input', updateCount);
        updateCount();
    }
});
