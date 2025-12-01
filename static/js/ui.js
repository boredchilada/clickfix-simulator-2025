/**
 * ClickFix UI Utilities
 * Replaces native alerts and confirms with styled components.
 */

const ClickFixUI = {
    /**
     * Show a toast notification
     * @param {string} message - The message to display
     * @param {string} type - 'info', 'success', 'warning', 'error'
     * @param {number} duration - Duration in ms (default 3000)
     */
    toast: function(message, type = 'info', duration = 3000) {
        const container = document.getElementById('toast-container') || this._createToastContainer();
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-content">${message}</div>
            <button class="toast-close" onclick="this.parentElement.remove()">&times;</button>
        `;
        
        container.appendChild(toast);
        
        // Trigger reflow for animation
        void toast.offsetWidth;
        toast.classList.add('show');
        
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    },

    /**
     * Show a confirmation modal
     * @param {string} message - The question to ask
     * @param {function} onConfirm - Callback if user clicks Confirm
     * @param {function} onCancel - Callback if user clicks Cancel
     */
    confirm: function(message, onConfirm, onCancel) {
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <p>${message}</p>
            </div>
            <div class="modal-actions">
                <button class="btn btn-outline" id="modal-cancel">Cancel</button>
                <button class="btn btn-danger" id="modal-confirm">Confirm</button>
            </div>
        `;
        
        overlay.appendChild(modal);
        document.body.appendChild(overlay);
        
        // Animation
        void overlay.offsetWidth;
        overlay.classList.add('show');
        
        const close = () => {
            overlay.classList.remove('show');
            setTimeout(() => overlay.remove(), 300);
        };
        
        document.getElementById('modal-cancel').onclick = () => {
            close();
            if (onCancel) onCancel();
        };
        
        document.getElementById('modal-confirm').onclick = () => {
            close();
            if (onConfirm) onConfirm();
        };
    },

    confirmSubmit: function(event, message) {
        event.preventDefault();
        const form = event.target;
        this.confirm(message, () => {
            form.submit();
        });
        return false;
    },

    _createToastContainer: function() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
        return container;
    }
};

window.ClickFixUI = ClickFixUI;