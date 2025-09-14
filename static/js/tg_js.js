(function() {
    'use strict';
    
    let selectedFiles = [];
    
    // DOM Elements
    const elements = {
        selectAll: document.getElementById('selectAll'),
        fileInput: document.getElementById('fileInput'),
        fileUploadSection: document.getElementById('fileUploadSection'),
        selectedFiles: document.getElementById('selectedFiles'),
        massMessageForm: document.getElementById('massMessageForm'),
        messageText: document.getElementById('messageText'),
        sendButton: document.getElementById('sendButton'),
        loading: document.getElementById('loading'),
        status: document.getElementById('status'),
        progressBar: document.getElementById('progressBar'),
        progressFill: document.getElementById('progressFill')
    };
    
    // Select all functionality
    elements.selectAll.addEventListener('change', function() {
        const checkboxes = document.querySelectorAll('input[name="group_ids"]');
        checkboxes.forEach(checkbox => {
            checkbox.checked = this.checked;
        });
    });
    
    // File input change event
    elements.fileInput.addEventListener('change', function(e) {
        addFiles(Array.from(e.target.files));
        e.target.value = ''; // Reset input
    });
    
    // Drag and drop functionality
    setupDragAndDrop();
    
    // Form submission
    elements.massMessageForm.addEventListener('submit', handleFormSubmit);
    
    // Functions
    function addFiles(files) {
        files.forEach(file => {
            if (!selectedFiles.find(f => f.name === file.name && f.size === file.size)) {
                selectedFiles.push(file);
            }
        });
        updateFilesList();
    }
    
    function setupDragAndDrop() {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            elements.fileUploadSection.addEventListener(eventName, preventDefaults, false);
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            elements.fileUploadSection.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            elements.fileUploadSection.addEventListener(eventName, unhighlight, false);
        });
        
        elements.fileUploadSection.addEventListener('drop', handleDrop, false);
    }
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    function highlight() {
        elements.fileUploadSection.classList.add('dragover');
    }
    
    function unhighlight() {
        elements.fileUploadSection.classList.remove('dragover');
    }
    
    function handleDrop(e) {
        const files = Array.from(e.dataTransfer.files);
        addFiles(files);
    }
    
    function updateFilesList() {
        elements.selectedFiles.innerHTML = '';
        
        selectedFiles.forEach((file, index) => {
            const fileItem = createFileItem(file, index);
            elements.selectedFiles.appendChild(fileItem);
        });
    }
    
    function createFileItem(file, index) {
        const item = document.createElement('div');
        item.className = 'tg-file-item';
        
        const icon = document.createElement('div');
        icon.className = 'tg-file-icon';
        
        if (file.type.startsWith('image/')) {
            icon.classList.add('image');
            icon.textContent = '🖼️';
        } else if (file.type.startsWith('video/')) {
            icon.classList.add('video');
            icon.textContent = '🎥';
        } else if (file.type.startsWith('audio/')) {
            icon.classList.add('audio');
            icon.textContent = '🎵';
        } else {
            icon.classList.add('document');
            icon.textContent = '📄';
        }
        
        const details = document.createElement('div');
        details.className = 'tg-file-details';
        
        const name = document.createElement('div');
        name.className = 'tg-file-name';
        name.textContent = file.name;
        
        const size = document.createElement('div');
        size.className = 'tg-file-size';
        size.textContent = formatFileSize(file.size);
        
        details.appendChild(name);
        details.appendChild(size);
        
        const removeBtn = document.createElement('button');
        removeBtn.className = 'tg-remove-file';
        removeBtn.textContent = '×';
        removeBtn.type = 'button';
        removeBtn.addEventListener('click', () => {
            selectedFiles.splice(index, 1);
            updateFilesList();
        });
        
        item.appendChild(icon);
        item.appendChild(details);
        item.appendChild(removeBtn);
        
        return item;
    }
    
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    function handleFormSubmit(e) {
        e.preventDefault();
        
        const selectedGroups = document.querySelectorAll('input[name="group_ids"]:checked');
        const messageText = elements.messageText.value.trim();
        
        // Validation
        if (selectedGroups.length === 0) {
            showStatus('error', '❌ Kamida bitta guruhni tanlang!');
            return;
        }
        
        if (!messageText && selectedFiles.length === 0) {
            showStatus('error', '❌ Matn yoki fayl kiriting!');
            return;
        }
        
        // Prepare form data
        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
        
        if (messageText) {
            formData.append('message_text', messageText);
        }
        
        selectedGroups.forEach(checkbox => {
            formData.append('group_ids', checkbox.value);
        });
        
        selectedFiles.forEach(file => {
            formData.append('files', file);
        });
        
        // Send request
        sendMessage(formData);
    }
    
    function sendMessage(formData) {
        // UI updates
        elements.sendButton.disabled = true;
        elements.loading.style.display = 'block';
        elements.progressBar.style.display = 'block';
        elements.status.style.display = 'none';
        
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 2;
            if (progress <= 90) {
                elements.progressFill.style.width = progress + '%';
            }
        }, 100);
        
        // Send request
        fetch('/send-mass-message/', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            clearInterval(progressInterval);
            elements.progressFill.style.width = '100%';
            
            if (data.success) {
                let message = `✅ <strong>Muvaffaqiyat!</strong> ${data.successful_sends} ta guruhga yuborildi.`;
                if (data.failed_sends > 0) {
                    message += `<br>❌ ${data.failed_sends} ta xatolik.`;
                    if (data.errors && data.errors.length > 0) {
                        message += '<br><br><strong>Xatoliklar:</strong><br>' + data.errors.join('<br>');
                    }
                }
                showStatus('success', message);
                
                // Clear form on success
                elements.messageText.value = '';
                selectedFiles = [];
                updateFilesList();
                document.querySelectorAll('input[name="group_ids"]').forEach(cb => cb.checked = false);
                elements.selectAll.checked = false;
            } else {
                showStatus('error', `❌ <strong>Xatolik:</strong> ${data.error}`);
            }
        })
        .catch(error => {
            clearInterval(progressInterval);
            showStatus('error', `❌ <strong>Xatolik yuz berdi:</strong> ${error.message}`);
        })
        .finally(() => {
            elements.sendButton.disabled = false;
            elements.loading.style.display = 'none';
            setTimeout(() => {
                elements.progressBar.style.display = 'none';
                elements.progressFill.style.width = '0%';
            }, 1000);
        });
    }
    
    function showStatus(type, message) {
        elements.status.className = 'tg-status ' + type;
        elements.status.innerHTML = message;
        elements.status.style.display = 'block';
        
        // Auto hide after 10 seconds for success, 15 for error
        const hideTime = type === 'success' ? 10000 : 15000;
        setTimeout(() => {
            elements.status.style.display = 'none';
        }, hideTime);
    }
})();