const API_BASE = 'http://localhost:5000/api';

/* =============================
   GLOBAL STATE
============================= */
const state = {
    view: 'dashboard',
    page: 1,
    pageSize: 50,
    charts: {},
    data: {}
};

/* =============================
   FORMATTERS (fixed zero bug)
============================= */
const format = {
    num: (n) =>
        n !== null && n !== undefined
            ? Number(n).toLocaleString()
            : '--',

    curr: (n) =>
        n !== null && n !== undefined
            ? `$${Number(n).toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2
              })}`
            : '--',

    dec: (n, d = 1) =>
        n !== null && n !== undefined
            ? Number(n).toFixed(d)
            : '--'
};

/* =============================
   UI HELPERS
============================= */
const ui = {
    show: (id) => document.getElementById(id)?.classList.remove('hidden'),
    hide: (id) => document.getElementById(id)?.classList.add('hidden'),
    get: (id) => document.getElementById(id),
    setText: (id, text) => {
        const el = document.getElementById(id);
        if (el) el.textContent = text;
    }
};

/* =============================
   API LAYER
============================= */
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

    overview: () => api.fetch('/stats/overview'),
    hourly: () => api.fetch('/stats/hourly'),
    boroughs: () => api.fetch('/stats/boroughs'),
    daily: () => api.fetch('/stats/daily'),
    timeCategories: () => api.fetch('/stats/time-categories'),
    routes: () => api.fetch('/stats/top-routes'),
    trips: (limit, offset) =>
        api.fetch(`/trips?limit=${limit}&offset=${offset}`)
};

/* =============================
   CHART HELPERS
============================= */
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

        state.charts[id] = new Chart(ctx, {
            type,
            data,
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: { legend: { display: false } },
                ...options
            }
        });
    }
};

/* =============================
   VIEWS
============================= */
const views = {
    async dashboard() {
        ui.show('loader');

        const [overview, hourly, boroughs] = await Promise.all([
            api.overview(),
            api.hourly(),
            api.boroughs()
        ]);

        if (overview) {
            ui.setText('stat-trips', format.num(overview.total_trips));
            ui.setText('stat-revenue', format.curr(overview.total_revenue));
            ui.setText('stat-fare', format.curr(overview.avg_fare));
            ui.setText(
                'stat-speed',
                `${format.dec(overview.avg_speed)} mph`
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
            /* 🔥 FIXED: map backend field names properly */
            state.data.trips = trips.map(t => ({
                ...t,
                pickup_datetime: t.tpep_pickup_datetime,
                distance: t.trip_distance,
                fare: t.fare_amount,
                tip: t.tip_amount,
                total: t.total_amount,
                speed: t.trip_speed_mph
            }));

            const tbody = ui.get('data-tbody');
            tbody.innerHTML = '';

            state.data.trips.forEach(trip => {
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
                div.innerHTML = `
                    <span>${route.route}</span>
                    <span>${format.num(route.trip_count)} trips</span>
                `;
                list.appendChild(div);
            });
        }

        ui.hide('loader');
    }
};

/* =============================
   TRIP DETAIL (no undefined)
============================= */
const showTripDetail = (trip) => {
    alert(`
Trip ID: ${trip.trip_id}
Pickup: ${trip.pickup_borough} - ${trip.pickup_zone}
Dropoff: ${trip.dropoff_borough} - ${trip.dropoff_zone}
Distance: ${format.dec(trip.distance)} miles
Fare: ${format.curr(trip.fare)}
Tip: ${format.curr(trip.tip)}
Total: ${format.curr(trip.total)}
Speed: ${format.dec(trip.speed)} mph
`);
};

/* =============================
   EXPORT CSV (uses mapped data)
============================= */
const exportCSV = () => {
    const data = state.data.trips;
    if (!data || data.length === 0) {
        alert('No data to export');
        return;
    }

    const headers = ['ID', 'Time', 'Pickup', 'Dropoff', 'Distance', 'Fare', 'Speed'];

    const rows = data.map(t => [
        t.trip_id,
        t.pickup_datetime,
        t.pickup_borough,
        t.dropoff_borough,
        t.distance,
        t.fare,
        t.speed
    ]);

    const csv = [headers, ...rows]
        .map(r => r.join(','))
        .join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = `nyc-taxi-${Date.now()}.csv`;
    a.click();

    URL.revokeObjectURL(url);
};

/* =============================
   NAVIGATION
============================= */
const navigate = (view) => {
    state.view = view;

    document.querySelectorAll('.nav-item').forEach(item =>
        item.classList.toggle('active', item.dataset.view === view)
    );

    document.querySelectorAll('.view').forEach(v =>
        v.classList.toggle('active', v.id === `${view}-view`)
    );

    if (views[view]) views[view]();
};

/* INIT */

const init = () => {
    document.querySelectorAll('.nav-item').forEach(item =>
        item.addEventListener('click', e => {
            e.preventDefault();
            navigate(item.dataset.view);
        })
    );

    ui.get('refresh-btn')?.addEventListener('click', () => {
        if (views[state.view]) views[state.view]();
    });

    ui.get('export-btn')?.addEventListener('click', exportCSV);

    ui.get('prev-btn')?.addEventListener('click', () => {
        if (state.page > 1) {
            state.page--;
            views.data();
        }
    });

    ui.get('next-btn')?.addEventListener('click', () => {
        state.page++;
        views.data();
    });

    navigate('dashboard');
};

document.addEventListener('DOMContentLoaded', init);
