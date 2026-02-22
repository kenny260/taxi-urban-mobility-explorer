const API_BASE = '/api'; // same origin safer than hardcoding localhost

const state = {
    view: 'dashboard',
    page: 1,
    pageSize: 50,
    charts: {},
    data: {}
};

<<<<<<< HEAD
/* =========================
   Formatting Helpers
========================= */
const format = {
    num: (n) => (n || n === 0) ? n.toLocaleString() : '--',
    curr: (n) => (n || n === 0)
        ? `$${Number(n).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
        : '--',
    dec: (n, d = 1) => (n || n === 0) ? Number(n).toFixed(d) : '--'
};

/* =========================
   UI Helpers
========================= */
const ui = {
    show: (id) => document.getElementById(id)?.classList.remove('hidden'),
    hide: (id) => document.getElementById(id)?.classList.add('hidden'),
    get: (id) => document.getElementById(id),
    setText: (id, text) => {
        const el = document.getElementById(id);
        if (el) el.textContent = text;
    }
};

/* =========================
   API Layer
========================= */
const api = {
    async fetch(endpoint) {
        try {
            const res = await fetch(`${API_BASE}${endpoint}`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return await res.json();
        } catch (err) {
            console.error(`API Error (${endpoint}):`, err);
            return null;
        }
    },
    summary: () => api.fetch('/stats/summary'),
    hourly: () => api.fetch('/stats/hourly-patterns'),
    boroughRevenue: () => api.fetch('/stats/borough-revenue'),
    dailyRevenue: () => api.fetch('/stats/daily-revenue'),
    timeCategories: () => api.fetch('/stats/time-categories'),
    routes: () => api.fetch('/stats/top-routes'),
    trips: (limit, offset) => api.fetch(`/trips?limit=${limit}&offset=${offset}`)
};

/* =========================
   Chart Configuration
========================= */
const chartDefaults = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
        legend: { display: false }
    },
    scales: {
        y: { beginAtZero: true, grid: { color: '#e5e7eb' } },
        x: { grid: { display: false } }
    }
};

const charts = {
    destroy(id) {
        if (state.charts[id]) {
            state.charts[id].destroy();
            delete state.charts[id];
        }
    },

    create(id, config) {
        charts.destroy(id);
        const canvas = ui.get(id);
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        state.charts[id] = new Chart(ctx, config);
    },

    bar(id, labels, values, color = '#4f46e5') {
        charts.create(id, {
            type: 'bar',
            data: {
                labels,
                datasets: [{
                    data: values,
                    backgroundColor: color,
                    borderRadius: 6
                }]
            },
            options: chartDefaults
        });
    },

    line(id, labels, values, color = '#4f46e5') {
        charts.create(id, {
            type: 'line',
            data: {
                labels,
                datasets: [{
                    data: values,
                    borderColor: color,
                    backgroundColor: `${color}33`,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4
                }]
            },
            options: chartDefaults
        });
    },

    doughnut(id, labels, values) {
        charts.create(id, {
            type: 'doughnut',
            data: {
                labels,
                datasets: [{
                    data: values,
                    backgroundColor: [
                        '#4f46e5',
                        '#7c3aed',
                        '#ec4899',
                        '#f59e0b',
                        '#10b981'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: true, position: 'bottom' }
                }
            }
        });
    }
};

/* =========================
   Views
========================= */
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
        }

        if (hourly?.length) {
            charts.bar(
                'hourly-chart',
                hourly.map(h => `${h.hour}:00`),
                hourly.map(h => h.trip_count)
            );
        }

        if (boroughs?.length) {
            charts.doughnut(
                'borough-chart',
                boroughs.map(b => b.borough),
                boroughs.map(b => b.total_revenue)
            );
        }

        ui.hide('loader');
    },

    async analytics() {
        ui.show('loader');

        const [daily, timeCategories] = await Promise.all([
            api.dailyRevenue(),
            api.timeCategories()
        ]);

        if (daily?.length) {
            charts.line(
                'daily-chart',
                daily.map(d => d.date),
                daily.map(d => d.total_revenue)
            );
        }

        if (timeCategories?.length) {
            charts.bar(
                'time-chart',
                timeCategories.map(t => t.time_category),
                timeCategories.map(t => t.avg_fare),
                '#7c3aed'
            );

            charts.bar(
                'speed-chart',
                timeCategories.map(t => t.time_category),
                timeCategories.map(t => t.avg_speed),
                '#10b981'
            );
        }

        ui.hide('loader');
    },

    async data() {
        ui.show('loader');

        const offset = (state.page - 1) * state.pageSize;
        const trips = await api.trips(state.pageSize, offset);

        if (trips?.length) {
            state.data.trips = trips;

            const tbody = ui.get('data-tbody');
            tbody.innerHTML = '';

            trips.forEach(trip => {
                const row = tbody.insertRow();
                row.innerHTML = `
                    <td>${trip.trip_id}</td>
                    <td>${trip.pickup_datetime}</td>
                    <td>${trip.pickup_borough}</td>
                    <td>${trip.dropoff_borough}</td>
                    <td>${format.dec(trip.distance)} mi</td>
                    <td>${format.curr(trip.fare)}</td>
                    <td>${format.dec(trip.speed)} mph</td>
                `;
            });

            ui.setText('page-info', `Page ${state.page}`);
        }

        ui.hide('loader');
    }
};

/* =========================
   Navigation
========================= */
const navigate = (view) => {
    state.view = view;

    document.querySelectorAll('.view')
        .forEach(v => v.classList.toggle('active', v.id === `${view}-view`));

    if (views[view]) views[view]();
};

/* =========================
   CSV Export
========================= */
const exportCSV = () => {
    const data = state.data.trips;
    if (!data?.length) return alert('No data to export');

    const headers = Object.keys(data[0]);
    const rows = data.map(obj => headers.map(h => obj[h]));

    const csv = [headers, ...rows].map(r => r.join(',')).join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');

    a.href = url;
    a.download = `nyc-taxi-${Date.now()}.csv`;
    a.click();

    URL.revokeObjectURL(url);
};

/* =========================
   Init
========================= */
const init = () => {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', e => {
            e.preventDefault();
            navigate(item.dataset.view);
        });
    });

    ui.get('refresh-btn')?.addEventListener('click', () => {
        if (views[state.view]) views[state.view]();
    });

    ui.get('export-btn')?.addEventListener('click', exportCSV);

    navigate('dashboard');
};

document.addEventListener('DOMContentLoaded', init);
=======
@stats_bp.route("/borough-revenue")
def borough_revenue():
    """Alias for boroughs endpoint"""
    return boroughs()

@stats_bp.route("/overview")
def overview():
    """Get overall statistics"""
    conn = None
    try:
        conn = get_connection()
        row = conn.execute("""
            SELECT
                COUNT(*) AS total_trips,
                ROUND(SUM(total_amount), 2) AS total_revenue,
                ROUND(AVG(total_amount), 2) AS avg_fare,
                ROUND(AVG(trip_distance), 2) AS avg_distance,
                ROUND(AVG(trip_speed_mph), 2) AS avg_speed,
                ROUND(AVG(tip_percentage), 2) AS avg_tip_pct
            FROM trips
        """).fetchone()
        return jsonify(dict(row))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

@stats_bp.route("/hourly")
def hourly():
    """Get hourly demand patterns"""
    try:
        return jsonify(cached_query("SELECT * FROM v_hourly_demand"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@stats_bp.route("/boroughs")
def boroughs():
    """Get borough statistics"""
    try:
        return jsonify(cached_query("SELECT * FROM v_borough_revenue"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@stats_bp.route("/daily")
def daily():
    """Get daily revenue statistics"""
    try:
        return jsonify(cached_query("SELECT * FROM v_daily_revenue"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@stats_bp.route("/time-categories")
def time_categories():
    """Get time category statistics"""
    try:
        return jsonify(cached_query("SELECT * FROM v_time_category_stats"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@stats_bp.route("/top-routes")
def top_routes():
    """Get top routes sorted by trip count"""
    conn = None
    try:
        conn = get_connection()
        rows = conn.execute("""
            SELECT
                route,
                pickup_zone,
                dropoff_zone,
                trip_count,
                avg_fare,
                avg_distance,
                avg_speed
            FROM v_top_routes
            LIMIT 20
        """).fetchall()
        routes = [dict(row) for row in rows]
        sorted_routes = quicksort_routes(routes)
        return jsonify(sorted_routes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

@stats_bp.route("/summary")
def summary():
    """Legacy endpoint"""
    conn = None
    try:
        conn = get_connection()
        row = conn.execute("""
            SELECT
                COUNT(*) AS total_trips,
                ROUND(AVG(fare_amount), 2) AS avg_fare,
                ROUND(SUM(trip_distance), 2) AS total_distance,
                ROUND(SUM(total_amount), 2) AS total_revenue
            FROM trips
        """).fetchone()
        return jsonify(dict(row))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

@stats_bp.route("/hourly-patterns")
def hourly_patterns():
    """Legacy endpoint"""
    try:
        return jsonify(cached_query("SELECT * FROM v_hourly_demand"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@stats_bp.route("/fare-distribution")
def fare_distribution():
    """Get fare distribution"""
    conn = None
    try:
        conn = get_connection()
        rows = conn.execute("""
            SELECT
                ROUND(fare_amount, 0) as fare_bucket,
                COUNT(*) as trip_count
            FROM trips
            GROUP BY fare_bucket
            ORDER BY fare_bucket
        """).fetchall()
        return jsonify([dict(row) for row in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()
@stats_bp.route("/daily-revenue")
def daily_revenue():
    """Alias for daily endpoint"""
    return daily()

@stats_bp.route("/time-category-stats")
def time_category_stats():
    """Alias for time-categories endpoint"""
    return time_categories()
>>>>>>> 572e0b9 (debugging)
