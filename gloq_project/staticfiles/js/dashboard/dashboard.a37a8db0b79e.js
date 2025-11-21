document.addEventListener('DOMContentLoaded', function() {
    // Modal functionality
    const entryModal = document.getElementById('entry-modal');
    const floatingNewDrop = document.getElementById('floating-new-drop');
    const closeEntryModal = document.getElementById('close-entry-modal');
    
    // Three-dot menu functionality
    const toolsToggle = document.getElementById('tools-toggle');
    const toolsDropdown = document.getElementById('tools-dropdown');
    
    // Toggle tools dropdown
    toolsToggle.addEventListener('click', function(e) {
        e.stopPropagation();
        toolsDropdown.classList.toggle('active');
    });
    
    // Close tools dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (toolsDropdown.classList.contains('active') && 
            !toolsDropdown.contains(e.target) && 
            !toolsToggle.contains(e.target)) {
            toolsDropdown.classList.remove('active');
        }
    });
    
    // Entry Modal - triggered by floating button
    floatingNewDrop.addEventListener('click', function() {
        // Clear any previous alerts
        const alertContainer = document.getElementById('form-alerts');
        if (alertContainer) {
            alertContainer.innerHTML = '';
        }
        
        entryModal.classList.add('active');
        
        // Focus on textarea when opened
        setTimeout(() => {
            const textarea = entryModal.querySelector('textarea');
            if (textarea) textarea.focus();
        }, 300);
    });

    closeEntryModal.addEventListener('click', function() {
        entryModal.classList.remove('active');
        // Clear form
        const form = document.getElementById('journal-form');
        if (form) form.reset();
    });

    // Close modals on overlay click
    entryModal.addEventListener('click', function(e) {
        if (e.target === entryModal) {
            entryModal.classList.remove('active');
            const form = document.getElementById('journal-form');
            if (form) form.reset();
        }
    });

    // Close modals on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            entryModal.classList.remove('active');
            toolsDropdown.classList.remove('active');
        }
    });
});

// Handle HTMX form submission responses
document.body.addEventListener('htmx:afterRequest', function(event) {
    console.log('HTMX afterRequest triggered', event.detail);
    
    if (event.detail.target && event.detail.target.id === 'journal-form') {
        const xhr = event.detail.xhr;
        const alertContainer = document.getElementById('form-alerts');
        const entryModal = document.getElementById('entry-modal');
        
        console.log('Form submission detected. Status:', xhr.status);
        console.log('Response text:', xhr.responseText);
        
        if (!alertContainer) {
            console.error('Alert container not found!');
            return;
        }
        
        try {
            const response = JSON.parse(xhr.responseText);
            console.log('Parsed response:', response);
            
            if (xhr.status === 200 && response.success) {
                console.log('Success case triggered');
                // Success - show message, reset and hide form
                alertContainer.innerHTML = `
                    <div class="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-4 fade-in">
                        ${response.message}
                    </div>
                `;
                
                // Reset form and close modal
                const form = document.getElementById('journal-form');
                if (form) form.reset();
                if (entryModal) entryModal.classList.remove('active');
                
                // Refresh stream content after new entry
                const streamContent = document.getElementById('stream-content');
                if (streamContent) {
                    htmx.ajax('GET', '{% url "journal:stream_content" %}', {
                        target: '#stream-content',
                        swap: 'innerHTML'
                    });
                }
                
                // Auto-hide success message after 5 seconds
                setTimeout(() => {
                    if (alertContainer) alertContainer.innerHTML = '';
                }, 5000);
                
            } else {
                console.log('Error case triggered');
                // Error - show error message
                alertContainer.innerHTML = `
                    <div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4 fade-in">
                        ${response.error || 'An unexpected error occurred.'}
                    </div>
                `;
            }
        } catch (e) {
            console.error('Error parsing response:', e);
            alertContainer.innerHTML = `
                <div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4 fade-in">
                    An error occurred while saving your entry.
                </div>
            `;
        }
    }
});




