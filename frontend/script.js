
// CONFIG

const API_BASE = 'http://localhost:5000/api';

const state = {
    view: 'dashboard',
    page: 1,
    pageSize: 50,
    charts: {},
    data: {}
};


// FORMATTING HELPERS

const format = {
    num: (n) => n ? n.toLocaleString() : '--',
    curr: (n) => n ? `$${n.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}` : '--',
    dec: (n, d = 1) => n ? n.toFixed(d) : '--'
};


// UI HELPERS

const ui = {
    show: (id) => document.getElementById(id)?.classList.remove('hidden'),
    hide: (id) => document.getElementById(id)?.classList.add('hidden'),
    get: (id) => document.getElementById(id),
    setText: (id, text) => {
        const el = document.getElementById(id);
        if (el) el.textContent = text;
    }
};


// API CALLS

const api = {
    async fetch(endpoint) {
        try {
            const res = await fetch(`${API_BASE}${endpoint}`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return await res.json();
        } catch (err) {
            console.error('API Error:', err);
            return null;
        }
    },

    summary: () => api.fetch('/stats/summary'),                // summary stats
    hourly: () => api.fetch('/stats/hourly-patterns'),         // hourly trips
    boroughRevenue: () => api.fetch('/stats/borough-revenue'), // borough revenue
    fareDistribution: () => api.fetch('/stats/fare-distribution'),
    routes: () => api.fetch('/stats/top-routes'),
    trips: (limit, offset) => api.fetch(`/trips?limit=${limit}&offset=${offset}`)
};


// CHART CONFIG

const chartConfig = {
    defaults: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: { legend: { display: false } }
    },
    colors: {
        primary: '#4f46e5',
        secondary: '#7c3aed',
        success: '#10b981',
        gradient: (ctx) => {
            const gradient = ctx.createLinearGradient(0, 0, 0, 300);
            gradient.addColorStop(0, 'rgba(79, 70, 229, 0.8)');
            gradient.addColorStop(1, 'rgba(79, 70, 229, 0.2)');
            return gradient;
        }
    }
};

fetch('/api/stats')
  .then(response => response.json())
  .catch(error => console.error("Error fetching stats:", error));

// CHART HELPERS

const charts = {
    destroy(id) {
        if (state.charts[id]) {
            state.charts[id].destroy();
            delete state.charts[id];
        }
    },

    create(id, type, data, options = {}) {
        charts.destroy(id);
        const canvas = ui.get(id);
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        state.charts[id] = new Chart(ctx, { type, data, options: { ...chartConfig.defaults, ...options } });
    },

    bar(id, labels, values, color = chartConfig.colors.primary) {
        charts.create(id, 'bar', {
            labels,
            datasets: [{ data: values, backgroundColor: color, borderRadius: 6 }]
        }, {
            scales: {
                y: { beginAtZero: true, grid: { color: '#e5e7eb' } },
                x: { grid: { display: false } }
            }
        });
    },

    line(id, labels, values, color = chartConfig.colors.primary) {
        charts.create(id, 'line', {
            labels,
            datasets: [{
                data: values,
                borderColor: color,
                backgroundColor: chartConfig.colors.gradient,
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointBackgroundColor: color
            }]
        }, {
            scales: {
                y: { beginAtZero: true, grid: { color: '#e5e7eb' } },
                x: { grid: { display: false } }
            }
        });
    },

    doughnut(id, labels, values) {
        const colors = ['#4f46e5', '#7c3aed', '#ec4899', '#f59e0b', '#10b981'];
        charts.create(id, 'doughnut', {
            labels,
            datasets: [{ data: values, backgroundColor: colors, borderWidth: 2, borderColor: '#fff' }]
        }, { plugins: { legend: { display: true, position: 'bottom' } } });
    }
};


// VIEWS

const views = {
    async dashboard() {
        ui.show('loader');

        const [summary, hourly, boroughs] = await Promise.all([
            api.summary(),
            api.hourly(),
            api.boroughRevenue()
        ]);

        if (summary) {
            ui.setText('stat-trips', format.num(summary.total_trips));
            ui.setText('stat-revenue', format.curr(summary.total_revenue));
            ui.setText('stat-fare', format.curr(summary.avg_fare));
            ui.setText('stat-speed', `${format.dec(summary.avg_speed)} mph`);
        }

        if (hourly) {
            charts.bar(
                'hourly-chart',
                hourly.map(h => `${h.hour}:00`),
                hourly.map(h => h.trip_count)
            );
        }

        if (boroughs) {
            charts.doughnut(
                'borough-chart',
                boroughs.map(b => b.borough),
                boroughs.map(b => b.total_revenue)
            );
        }

        ui.hide('loader');
    },

    async data() {
        ui.show('loader');
        const offset = (state.page - 1) * state.pageSize;
        const [trips, routes] = await Promise.all([
            api.trips(state.pageSize, offset),
            api.routes()
        ]);

        if (trips) {
            state.data.trips = trips; // store for CSV export
            const tbody = ui.get('data-tbody');
            tbody.innerHTML = '';
            trips.forEach(trip => {
                const row = tbody.insertRow();
                row.innerHTML = `
                    <td>${trip.trip_id}</td>
                    <td>${new Date(trip.pickup_datetime).toLocaleString()}</td>
                    <td>${trip.pickup_borough}</td>
                    <td>${trip.dropoff_borough}</td>
                    <td>${format.dec(trip.distance)} mi</td>
                    <td>${format.curr(trip.fare)}</td>
                    <td>${format.dec(trip.speed)} mph</td>
                `;
                row.style.cursor = 'pointer';
                row.onclick = () => showTripDetail(trip);
            });
            ui.setText('page-info', `Page ${state.page}`);
        }

        if (routes) {
            const list = ui.get('routes-list');
            list.innerHTML = '';
            routes.slice(0, 10).forEach(route => {
                const div = document.createElement('div');
                div.className = 'route-item';
                div.innerHTML = `<span>${route.route}</span><span>${format.num(route.trip_count)} trips</span>`;
                list.appendChild(div);
            });
        }

        ui.hide('loader');
    }
};


// TRIP DETAIL

const showTripDetail = (trip) => {
    const msg = [
        'Trip Details',
        '',
        `ID: ${trip.trip_id}`,
        `Pickup: ${trip.pickup_borough} - ${trip.pickup_zone}`,
        `Dropoff: ${trip.dropoff_borough} - ${trip.dropoff_zone}`,
        `Distance: ${format.dec(trip.distance)} miles`,
        `Fare: ${format.curr(trip.fare)}`,
        `Tip: ${format.curr(trip.tip)}`,
        `Total: ${format.curr(trip.total)}`,
        `Speed: ${format.dec(trip.speed)} mph`
    ].join('\n');

    alert(msg);
};

// NAVIGATION

const navigate = (view) => {
    state.view = view;

    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.view === view);
    });

    document.querySelectorAll('.view').forEach(v => {
        v.classList.toggle('active', v.id === `${view}-view`);
    });

    const titles = {
        dashboard: { title: 'Dashboard', subtitle: 'Overview of taxi operations' },
        data: { title: 'Data Explorer', subtitle: 'Browse trip records' }
    };

    ui.setText('page-title', titles[view].title);
    ui.setText('page-subtitle', titles[view].subtitle);

    if (views[view]) views[view]();
};

// CSV EXPORT

const exportCSV = () => {
    const data = state.data.trips;
    if (!data || data.length === 0) { alert('No data to export'); return; }

    const headers = ['ID', 'Time', 'Pickup', 'Dropoff', 'Distance', 'Fare', 'Speed'];
    const rows = data.map(t => [t.trip_id, t.pickup_datetime, t.pickup_borough, t.dropoff_borough, t.distance, t.fare, t.speed]);
    const csv = [headers, ...rows].map(r => r.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `nyc-taxi-${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
};

// INIT

const init = () => {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', e => { e.preventDefault(); navigate(item.dataset.view); });
    });

    ui.get('refresh-btn')?.addEventListener('click', () => { if (views[state.view]) views[state.view](); });
    ui.get('export-btn')?.addEventListener('click', exportCSV);
    ui.get('prev-btn')?.addEventListener('click', () => { if (state.page > 1) { state.page--; views.data(); } });
    ui.get('next-btn')?.addEventListener('click', () => { state.page++; views.data(); });
    ui.get('apply-filter')?.addEventListener('click', () => { state.page = 1; views.data(); });

    navigate('dashboard');
};

document.addEventListener('DOMContentLoaded', init);
