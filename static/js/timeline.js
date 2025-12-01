/**
 * ClickFix Timeline & Dashboard Logic
 * Handles the interactive timeline chart, filtering, and data fetching.
 */

// Dashboard State
const state = {
    startDate: null,
    endDate: null,
    interval: 'day',
    eventTypes: ['PAGE_VIEW', 'BUTTON_CLICK', 'PAYLOAD_EXECUTED', 'TRAINING_COMPLETED', 'TRAINING_ACKNOWLEDGED', 'TRAINING_VIEWED'],
    client: '', // Will be set from template
    campaignId: null,
    selectedBuckets: [],
    timelineData: null,
    apiEndpoints: {
        timeline: '',
        stats: '',
        events: ''
    }
};

// Initialize the dashboard
function initDashboard(config) {
    // Set API endpoints and initial state
    state.apiEndpoints = config.apiEndpoints;
    state.client = config.currentClient || '';
    state.campaignId = config.campaignId || null;
    
    // Initialize dates (default: last 30 days)
    initializeDates(30);
    
    // Initial data fetch
    refreshDashboard();
    
    // Setup event listeners
    setupEventListeners();
}

// Initialize dates
function initializeDates(days = 30) {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - days);
    
    state.endDate = end.toISOString().split('T')[0];
    state.startDate = start.toISOString().split('T')[0];
    
    const startDateInput = document.getElementById('start-date');
    const endDateInput = document.getElementById('end-date');
    
    if (startDateInput) startDateInput.value = state.startDate;
    if (endDateInput) endDateInput.value = state.endDate;
}

// Fetch timeline data from API
async function fetchTimelineData() {
    const params = new URLSearchParams({
        start_date: state.startDate + 'T00:00:00',
        end_date: state.endDate + 'T23:59:59',
        interval: state.interval
    });
    
    if (state.client) params.append('client', state.client);
    if (state.campaignId) params.append('campaign_id', state.campaignId);
    if (state.eventTypes.length > 0) {
        params.append('event_type', state.eventTypes.join(','));
    }
    
    try {
        const response = await fetch(`${state.apiEndpoints.timeline}?${params}`);
        const data = await response.json();
        state.timelineData = data;
        return data;
    } catch (error) {
        return null;
    }
}

// Fetch stats from API
async function fetchStats() {
    const params = new URLSearchParams();
    
    if (state.startDate) params.append('start_date', state.startDate + 'T00:00:00');
    if (state.endDate) params.append('end_date', state.endDate + 'T23:59:59');
    if (state.client) params.append('client', state.client);
    if (state.campaignId) params.append('campaign_id', state.campaignId);
    
    try {
        const response = await fetch(`${state.apiEndpoints.stats}?${params}`);
        return await response.json();
    } catch (error) {
        return null;
    }
}

// Fetch filtered events from API
async function fetchEvents(page = 1) {
    const params = new URLSearchParams({
        page: page,
        per_page: 50
    });
    
    if (state.startDate) params.append('start_date', state.startDate + 'T00:00:00');
    if (state.endDate) params.append('end_date', state.endDate + 'T23:59:59');
    if (state.client) params.append('client', state.client);
    if (state.campaignId) params.append('campaign_id', state.campaignId);
    if (state.eventTypes.length > 0) {
        params.append('event_type', state.eventTypes.join(','));
    }
    
    try {
        const response = await fetch(`${state.apiEndpoints.events}?${params}`);
        return await response.json();
    } catch (error) {
        return null;
    }
}

// Render timeline chart
function renderTimeline(data) {
    const chart = document.getElementById('timeline-chart');
    const labels = document.getElementById('timeline-labels');
    
    if (!data || !data.buckets || data.buckets.length === 0) {
        chart.innerHTML = '<div style="text-align: center; color: var(--color-text-muted); padding: 2rem; width: 100%;">No data available for the selected period</div>';
        labels.innerHTML = '';
        return;
    }
    
    // Find max value for scaling
    const maxTotal = Math.max(...data.buckets.map(b => b.total), 1);
    const chartHeight = 100; // pixels
    
    // Render Y-Axis
    const yAxis = document.getElementById('timeline-y-axis');
    if (yAxis) {
        yAxis.innerHTML = '';
        const steps = 3; // 0, mid, max
        for (let i = steps; i >= 0; i--) {
            const value = Math.round((maxTotal / steps) * i);
            const label = document.createElement('div');
            label.textContent = value;
            yAxis.appendChild(label);
        }
    }

    // Render bars
    chart.innerHTML = data.buckets.map((bucket, index) => {
        const date = new Date(bucket.timestamp);
        const dateStr = formatDate(date, state.interval);
        
        // Calculate segment heights
        const pageViewHeight = (bucket.PAGE_VIEW / maxTotal) * chartHeight;
        const clickHeight = (bucket.BUTTON_CLICK / maxTotal) * chartHeight;
        const execHeight = (bucket.PAYLOAD_EXECUTED / maxTotal) * chartHeight;
        const trainingHeight = ((bucket.TRAINING_COMPLETED || 0) + (bucket.TRAINING_ACKNOWLEDGED || 0) + (bucket.TRAINING_VIEWED || 0)) / maxTotal * chartHeight;
        
        const isSelected = state.selectedBuckets.includes(bucket.timestamp);
        
        // Tooltip content
        const tooltipContent = `
            <strong>${dateStr}</strong><br>
            Views: ${bucket.PAGE_VIEW}<br>
            Clicks: ${bucket.BUTTON_CLICK}<br>
            Executions: ${bucket.PAYLOAD_EXECUTED}<br>
            Training: ${(bucket.TRAINING_COMPLETED || 0) + (bucket.TRAINING_ACKNOWLEDGED || 0) + (bucket.TRAINING_VIEWED || 0)}
        `;
        
        return `
            <div class="timeline-bar ${isSelected ? 'selected' : ''}" 
                 data-timestamp="${bucket.timestamp}"
                 data-index="${index}"
                 data-tooltip="${encodeURIComponent(tooltipContent)}"
                 onclick="toggleBucketSelection('${bucket.timestamp}')"
                 onmouseenter="showTooltip(this)"
                 onmouseleave="hideTooltip()">
                <div class="bar-segment training" style="height: ${trainingHeight}px;"></div>
                <div class="bar-segment payload-executed" style="height: ${execHeight}px;"></div>
                <div class="bar-segment button-click" style="height: ${clickHeight}px;"></div>
                <div class="bar-segment page-view" style="height: ${pageViewHeight}px;"></div>
            </div>
        `;
    }).join('');
    
    // Render labels (show ~5-7 labels)
    const labelCount = Math.min(7, data.buckets.length);
    const step = Math.max(1, Math.floor(data.buckets.length / labelCount));
    
    let labelHtml = '';
    for (let i = 0; i < data.buckets.length; i += step) {
        const bucket = data.buckets[i];
        const date = new Date(bucket.timestamp);
        labelHtml += `<span>${formatDate(date, state.interval)}</span>`;
    }
    labels.innerHTML = labelHtml;
    
    const rangeLabel = document.getElementById('timeline-range-label');
    if (rangeLabel) {
        rangeLabel.textContent = `${data.total_events} events from ${formatDate(new Date(data.start_date), 'day')} to ${formatDate(new Date(data.end_date), 'day')}`;
    }
}

// Tooltip Logic
let tooltipEl = null;

function createTooltip() {
    if (!tooltipEl) {
        tooltipEl = document.createElement('div');
        tooltipEl.id = 'timeline-tooltip';
        document.body.appendChild(tooltipEl);
    }
}

function showTooltip(element) {
    if (!tooltipEl) createTooltip();
    
    const content = decodeURIComponent(element.dataset.tooltip);
    tooltipEl.innerHTML = content;
    tooltipEl.style.opacity = '1';
    
    const rect = element.getBoundingClientRect();
    const tooltipRect = tooltipEl.getBoundingClientRect();
    
    // Position above the bar, centered
    let top = rect.top - 10;
    let left = rect.left + (rect.width / 2);
    
    // Prevent going off screen
    if (left - (tooltipRect.width / 2) < 10) {
        left = 10 + (tooltipRect.width / 2);
    } else if (left + (tooltipRect.width / 2) > window.innerWidth - 10) {
        left = window.innerWidth - 10 - (tooltipRect.width / 2);
    }
    
    tooltipEl.style.top = `${top}px`;
    tooltipEl.style.left = `${left}px`;
}

function hideTooltip() {
    if (tooltipEl) {
        tooltipEl.style.opacity = '0';
    }
}

// Format date based on interval
function formatDate(date, interval) {
    if (interval === 'hour') {
        return date.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric' });
    } else if (interval === 'week') {
        return date.toLocaleString('en-US', { month: 'short', day: 'numeric' });
    } else {
        return date.toLocaleString('en-US', { month: 'short', day: 'numeric' });
    }
}

// Update stats display
function updateStats(stats) {
    const elements = {
        'stat-views': stats.total_views,
        'stat-clicks': stats.total_clicks,
        'stat-executions': stats.total_executions,
        'stat-training': stats.total_training_completed
    };
    
    for (const [id, value] of Object.entries(elements)) {
        const el = document.getElementById(id);
        if (el) {
            el.classList.add('updating');
            setTimeout(() => {
                el.textContent = value;
                el.classList.remove('updating');
            }, 150);
        }
    }
}

// Update events table
function updateEventsTable(data) {
    const tbody = document.querySelector('#events-table tbody');
    if (!tbody || !data || !data.events) return;
    
    if (data.events.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-8">No events found for the selected filters.</td></tr>';
        return;
    }
    
    tbody.innerHTML = data.events.map(event => {
        const date = new Date(event.timestamp);
        const dateStr = date.toLocaleString('en-US', { 
            year: 'numeric', month: '2-digit', day: '2-digit',
            hour: '2-digit', minute: '2-digit', second: '2-digit'
        });
        
        let badgeClass = '';
        let badgeText = event.event_type;
        
        switch (event.event_type) {
            case 'PAGE_VIEW':
                badgeClass = 'badge-blue';
                badgeText = 'Viewed Page';
                break;
            case 'BUTTON_CLICK':
                badgeClass = 'badge-amber';
                badgeText = 'Clicked Fix';
                break;
            case 'PAYLOAD_EXECUTED':
                badgeClass = 'badge-red';
                badgeText = 'EXECUTED';
                break;
            case 'TRAINING_VIEWED':
                badgeClass = 'badge-gray';
                badgeText = 'Training Started';
                break;
            case 'TRAINING_COMPLETED':
                badgeClass = 'badge-green';
                badgeText = 'Training Viewed All';
                break;
            case 'TRAINING_ACKNOWLEDGED':
                badgeClass = 'badge-green';
                badgeText = 'Training Acknowledged';
                break;
        }
        
        return `
            <tr>
                <td style="white-space: nowrap;">${dateStr}</td>
                <td><code>${event.user_id}</code></td>
                <td>${event.campaign_name}</td>
                <td><span class="badge ${badgeClass}">${badgeText}</span></td>
                <td>${event.platform || '-'}</td>
                <td>${event.source_ip || '-'}</td>
                <td>
                    ${event.hostname ? `
                        <div style="font-size: 0.85em;">
                            <div><strong>Host:</strong> ${event.hostname}</div>
                            <div><strong>User:</strong> ${event.username || '-'}</div>
                        </div>
                    ` : '<span class="text-muted">-</span>'}
                </td>
            </tr>
        `;
    }).join('');
}

// Toggle bucket selection for filtering
function toggleBucketSelection(timestamp) {
    const index = state.selectedBuckets.indexOf(timestamp);
    if (index > -1) {
        state.selectedBuckets.splice(index, 1);
    } else {
        state.selectedBuckets.push(timestamp);
    }
    
    // Update visual selection
    document.querySelectorAll('.timeline-bar').forEach(bar => {
        if (state.selectedBuckets.includes(bar.dataset.timestamp)) {
            bar.classList.add('selected');
        } else {
            bar.classList.remove('selected');
        }
    });
    
    // Show/hide selection info
    const selectionInfo = document.getElementById('selection-info');
    if (state.selectedBuckets.length > 0) {
        selectionInfo.classList.add('visible');
        document.getElementById('selection-text').textContent = 
            `${state.selectedBuckets.length} time period(s) selected`;
        
        // Filter events table to selected buckets
        filterEventsBySelection();
    } else {
        selectionInfo.classList.remove('visible');
        refreshDashboard();
    }
}

// Clear timeline selection
function clearTimelineSelection() {
    state.selectedBuckets = [];
    document.querySelectorAll('.timeline-bar').forEach(bar => {
        bar.classList.remove('selected');
    });
    const selectionInfo = document.getElementById('selection-info');
    if (selectionInfo) selectionInfo.classList.remove('visible');
    refreshDashboard();
}

// Filter events by selected buckets
async function filterEventsBySelection() {
    if (state.selectedBuckets.length === 0) return;
    
    // For simplicity, we'll use the min/max of selected buckets as date range
    const dates = state.selectedBuckets.map(ts => new Date(ts)).sort((a, b) => a - b);
    const minDate = dates[0];
    const maxDate = dates[dates.length - 1];
    
    // Adjust max date based on interval
    let adjustedMaxDate = new Date(maxDate);
    if (state.interval === 'hour') {
        adjustedMaxDate.setHours(adjustedMaxDate.getHours() + 1);
    } else if (state.interval === 'week') {
        adjustedMaxDate.setDate(adjustedMaxDate.getDate() + 7);
    } else {
        adjustedMaxDate.setDate(adjustedMaxDate.getDate() + 1);
    }
    
    const params = new URLSearchParams({
        start_date: minDate.toISOString(),
        end_date: adjustedMaxDate.toISOString(),
        per_page: 50
    });
    
    if (state.client) params.append('client', state.client);
    if (state.campaignId) params.append('campaign_id', state.campaignId);
    if (state.eventTypes.length > 0) {
        params.append('event_type', state.eventTypes.join(','));
    }
    
    try {
        const response = await fetch(`${state.apiEndpoints.events}?${params}`);
        const data = await response.json();
        updateEventsTable(data);
    } catch (error) {
        // Silently handle fetch errors
    }
}

// Refresh entire dashboard
async function refreshDashboard() {
    // Fetch all data
    const [timelineData, stats, events] = await Promise.all([
        fetchTimelineData(),
        fetchStats(),
        fetchEvents()
    ]);
    
    // Update UI
    if (timelineData) renderTimeline(timelineData);
    if (stats) updateStats(stats);
    if (events) updateEventsTable(events);
}

// Setup Event Listeners
function setupEventListeners() {
    // Date range presets
    document.querySelectorAll('.preset-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            
            const range = e.target.dataset.range;
            const customRange = document.getElementById('custom-date-range');
            
            if (range === 'custom') {
                if (customRange) customRange.style.display = 'flex';
            } else {
                if (customRange) customRange.style.display = 'none';
                initializeDates(parseInt(range));
                clearTimelineSelection();
                refreshDashboard();
            }
        });
    });
    
    // Custom date inputs
    const startDateInput = document.getElementById('start-date');
    if (startDateInput) {
        startDateInput.addEventListener('change', (e) => {
            state.startDate = e.target.value;
            clearTimelineSelection();
            refreshDashboard();
        });
    }
    
    const endDateInput = document.getElementById('end-date');
    if (endDateInput) {
        endDateInput.addEventListener('change', (e) => {
            state.endDate = e.target.value;
            clearTimelineSelection();
            refreshDashboard();
        });
    }
    
    // Interval select
    const intervalSelect = document.getElementById('interval-select');
    if (intervalSelect) {
        intervalSelect.addEventListener('change', (e) => {
            state.interval = e.target.value;
            clearTimelineSelection();
            refreshDashboard();
        });
    }
    
    // Client filter
    const clientFilter = document.getElementById('client-filter');
    if (clientFilter) {
        clientFilter.addEventListener('change', (e) => {
            state.client = e.target.value;
            clearTimelineSelection();
            refreshDashboard();
        });
    }
    
    // Campaign filter
    const campaignFilter = document.getElementById('campaign-filter');
    if (campaignFilter) {
        campaignFilter.addEventListener('change', (e) => {
            state.campaignId = e.target.value || null;
            clearTimelineSelection();
            refreshDashboard();
        });
    }
    
    // Event type chips - these control data filtering via API
    document.querySelectorAll('.event-type-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            chip.classList.toggle('active');
            
            // Sync the corresponding legend item
            const chipTypes = chip.dataset.type.split(',');
            syncLegendItem(chipTypes[0], chip.classList.contains('active'));
            
            // Rebuild event types array
            state.eventTypes = [];
            document.querySelectorAll('.event-type-chip.active').forEach(activeChip => {
                const types = activeChip.dataset.type.split(',');
                state.eventTypes.push(...types);
            });
            
            clearTimelineSelection();
            refreshDashboard();
        });
    });
    
    // Legend items - sync with chips and toggle visual segments
    document.querySelectorAll('.legend-item').forEach(item => {
        item.addEventListener('click', () => {
            const eventType = item.dataset.type;
            const willBeActive = item.classList.contains('inactive');
            
            // Find and click the corresponding chip to trigger API refresh
            const correspondingChip = findCorrespondingChip(eventType);
            if (correspondingChip) {
                const chipIsActive = correspondingChip.classList.contains('active');
                // Only click if states don't match
                if (chipIsActive !== willBeActive) {
                    correspondingChip.click();
                    return; // The chip click handler will handle everything
                }
            }
            
            // If no chip found or states already match, just toggle visual
            item.classList.toggle('inactive');
            toggleSegmentVisibility(eventType, !item.classList.contains('inactive'));
        });
    });
}

// Helper: Toggle visibility of chart bar segments
function toggleSegmentVisibility(eventType, visible) {
    const segmentClassMap = {
        'PAGE_VIEW': '.bar-segment.page-view',
        'BUTTON_CLICK': '.bar-segment.button-click',
        'PAYLOAD_EXECUTED': '.bar-segment.payload-executed',
        'TRAINING': '.bar-segment.training'
    };
    
    const segmentSelector = segmentClassMap[eventType];
    if (segmentSelector) {
        const segments = document.querySelectorAll(segmentSelector);
        segments.forEach(segment => {
            if (!visible) {
                segment.dataset.originalHeight = segment.style.height;
                segment.style.height = '0px';
                segment.style.opacity = '0';
            } else {
                segment.style.height = segment.dataset.originalHeight || segment.style.height;
                segment.style.opacity = '1';
            }
        });
    }
}

// Helper: Find the Event Type Chip that corresponds to a legend type
function findCorrespondingChip(legendType) {
    // Map legend types to chip data-type values
    const legendToChipMap = {
        'PAGE_VIEW': 'PAGE_VIEW',
        'BUTTON_CLICK': 'BUTTON_CLICK',
        'PAYLOAD_EXECUTED': 'PAYLOAD_EXECUTED',
        'TRAINING': 'TRAINING_COMPLETED,TRAINING_ACKNOWLEDGED,TRAINING_VIEWED'
    };
    
    const chipType = legendToChipMap[legendType];
    if (chipType) {
        return document.querySelector(`.event-type-chip[data-type="${chipType}"]`);
    }
    return null;
}

// Helper: Sync legend item visual state with chip state
function syncLegendItem(chipType, isActive) {
    // Map chip types to legend types
    const chipToLegendMap = {
        'PAGE_VIEW': 'PAGE_VIEW',
        'BUTTON_CLICK': 'BUTTON_CLICK',
        'PAYLOAD_EXECUTED': 'PAYLOAD_EXECUTED',
        'TRAINING_COMPLETED': 'TRAINING',
        'TRAINING_ACKNOWLEDGED': 'TRAINING',
        'TRAINING_VIEWED': 'TRAINING'
    };
    
    const legendType = chipToLegendMap[chipType];
    if (legendType) {
        const legendItem = document.querySelector(`.legend-item[data-type="${legendType}"]`);
        if (legendItem) {
            if (isActive) {
                legendItem.classList.remove('inactive');
            } else {
                legendItem.classList.add('inactive');
            }
            toggleSegmentVisibility(legendType, isActive);
        }
    }
}

// Copy link function
function copyLink(url) {
    navigator.clipboard.writeText(url).then(() => {
        ClickFixUI.toast("Link copied to clipboard!", "success");
    });
}

// Global refresh function for the refresh button
window.refreshDashboard = refreshDashboard;
window.copyLink = copyLink;
window.toggleBucketSelection = toggleBucketSelection;
window.clearTimelineSelection = clearTimelineSelection;
window.showTooltip = showTooltip;
window.hideTooltip = hideTooltip;