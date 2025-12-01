/**
 * Training Module Tracker & UI Controller
 * Handles scroll tracking, animations, and section completion events for the training page.
 */
const TrainingTracker = {
    userId: null,
    trackEndpoint: '/track/training',
    sectionsViewed: new Set(),
    
    init: function(userId, trackEndpoint) {
        this.userId = userId || null;
        if (trackEndpoint) {
            this.trackEndpoint = trackEndpoint;
        }
        this._setupScrollTracking();
        
        // Trigger initial animation for the first section if visible on load
        this._checkInitialVisibility();
    },
    
    _setupScrollTracking: function() {
        const sections = document.querySelectorAll('.training-section');
        
        if (!window.IntersectionObserver) {
            // Fallback for very old browsers: just make everything visible
            sections.forEach(s => s.classList.add('active'));
            return;
        }

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const section = entry.target;
                    
                    // Trigger Animation
                    section.classList.add('active');
                    
                    // Track Event if it has a data-training-section attribute
                    const sectionId = section.dataset.trainingSection;
                    if (sectionId && !this.sectionsViewed.has(sectionId)) {
                        this.sectionsViewed.add(sectionId);
                        this._trackEvent(sectionId);
                    }
                }
            });
        }, { threshold: 0.3 }); // 0.3 means 30% of the section must be visible
        
        sections.forEach(section => observer.observe(section));
    },

    _checkInitialVisibility: function() {
        // Sometimes the observer needs a moment or the first section is already there
        setTimeout(() => {
            const firstSection = document.querySelector('.training-section');
            if (firstSection) firstSection.classList.add('active');
        }, 100);
    },
    
    _trackEvent: function(eventType) {
        if (!this.userId) {
            return;
        }
        
        // Use fetch for reliable tracking
        const url = `${this.trackEndpoint}/${this.userId}?section=${eventType}`;
        
        fetch(url, { method: 'POST' })
            .catch(err => console.error('[Training] Tracking failed:', err));
    },

    complete: function() {
        this._trackEvent('TRAINING_ACKNOWLEDGED');
    }
};

// Expose globally
window.TrainingTracker = TrainingTracker;