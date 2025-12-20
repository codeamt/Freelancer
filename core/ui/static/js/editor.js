// Editor state
let currentPanel = 'structure';
let selectedSection = null;
let selectedComponent = null;

// Panel switching
document.querySelectorAll('[id^="view-"]').forEach(btn => {
    btn.addEventListener('click', (e) => {
        const panel = e.target.id.replace('view-', '');
        switchPanel(panel);
    });
});

function switchPanel(panel) {
    // Hide all panels
    document.querySelectorAll('.panel').forEach(p => p.classList.add('hidden'));
    
    // Show selected panel
    document.getElementById(`${panel}-panel`).classList.remove('hidden');
    
    // Update toolbar
    document.querySelectorAll('[id^="view-"]').forEach(btn => {
        btn.classList.toggle('btn-active', btn.id === `view-${panel}`);
    });
    
    currentPanel = panel;
}

// Drag and drop for components
document.querySelectorAll('[draggable="true"]').forEach(component => {
    component.addEventListener('dragstart', (e) => {
        e.dataTransfer.setData('template_id', e.target.dataset.templateId);
    });
});

document.getElementById('section-list').addEventListener('drop', (e) => {
    e.preventDefault();
    const templateId = e.dataTransfer.getData('template_id');
    
    // Add component via HTMX
    htmx.ajax('POST', '/api/editor/components/add', {
        values: {
            session_id: window.EDITOR_SESSION,
            section_id: selectedSection,
            component_template_id: templateId
        },
        target: '#preview-frame'
    });
});

// Auto-save every 30 seconds
setInterval(() => {
    fetch('/api/editor/auto-save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: window.EDITOR_SESSION })
    });
}, 30000);

// Preview switching
document.querySelectorAll('.preview-switch').forEach(btn => {
    btn.addEventListener('click', (e) => {
        const userType = e.target.dataset.userType;
        const iframe = document.getElementById('preview-frame');
        iframe.src = `/api/editor/preview/${userType}?session_id=${window.EDITOR_SESSION}`;
    });
});