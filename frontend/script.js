const API_BASE = 'http://localhost:5000/api';

const state = {
    view: 'dashboard',
    page: 1,
    pageSize: 50,
    charts: {},
    data: {}
};

const format = {
    num: (n) => n ? n.toLocaleString() : '--',
    curr: (n) => n ? `$${n.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}` : '--',
    dec: (n, d = 1) => n ? n.toFixed(d) : '--'
};

const ui = {
    show: (id) => document.getElementById(id).classList.remove('hidden'),
    hide: (id) => document.getElementById(id).classList.add('hidden'),
    get: (id) => document.getElementById(id),
    setText: (id, text) => {
        const el = document.getElementById(id);
        if (el) el.textContent = text;
    }
};

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
    trips: (limit, offset) => api.fetch(`/trips?limit=${limit}&offset=${offset}`)
};

const chartConfig = {
    defaults: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: { display: false }
        }
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
            options: { ...chartConfig.defaults, ...options }
        });
    },
    
    bar(id, labels, values, color = chartConfig.colors.primary) {
        charts.create(id, 'bar', {
            labels,
            datasets: [{
                data: values,
                backgroundColor: color,
                borderRadius: 6
            }]
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
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: '#fff'
            }]
        }, {
            plugins: {
                legend: { display: true, position: 'bottom' }
            }
        });
    }
};

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
            ui.setText('stat-speed', `${format.dec(overview.avg_speed)} mph`);
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
    
    async analytics() {
        ui.show('loader');
        
        const [daily, timeCategories] = await Promise.all([
            api.daily(),
            api.timeCategories()
        ]);
        
        if (daily) {
            charts.line(
                'daily-chart',
                daily.map(d => d.date.split('-')[2]),
                daily.map(d => d.total_trips)
            );
        }
        
        if (timeCategories) {
            const labels = {
                'late_night': 'Late Night',
                'morning_rush': 'Morning',
                'midday': 'Midday',
                'evening_rush': 'Evening',
                'night': 'Night'
            };
            
            charts.bar(
                'time-chart',
                timeCategories.map(t => labels[t.time_category]),
                timeCategories.map(t => t.avg_fare),
                chartConfig.colors.secondary
            );
            
            charts.bar(
                'speed-chart',
                timeCategories.map(t => labels[t.time_category]),
                timeCategories.map(t => t.avg_speed),
                chartConfig.colors.success
            );
        }
        
        ui.hide('loader');
    },
    
    async insights() {
        ui.show('loader');
        
        if (!state.data.hourly) state.data.hourly = await api.hourly();
        if (!state.data.boroughs) state.data.boroughs = await api.boroughs();
        if (!state.data.timeCategories) state.data.timeCategories = await api.timeCategories();
        
        const { hourly, boroughs, timeCategories } = state.data;
        
        if (hourly) {
            const rush = hourly.filter(h => h.hour >= 7 && h.hour <= 9);
            const offPeak = hourly.filter(h => h.hour >= 10 && h.hour <= 15);
            const rushAvg = rush.reduce((s, h) => s + h.avg_fare, 0) / rush.length;
            const offPeakAvg = offPeak.reduce((s, h) => s + h.avg_fare, 0) / offPeak.length;
            const diff = ((rushAvg - offPeakAvg) / offPeakAvg * 100).toFixed(1);
            
            ui.setText('insight-1-value', `+${diff}% Higher`);
            ui.setText('insight-1-text', 
                `Morning rush hour (7-9am) fares average ${format.curr(rushAvg)}, which is ${diff}% higher than midday rates of ${format.curr(offPeakAvg)}. This premium reflects peak demand and congestion.`);
            
            charts.line(
                'insight-1-chart',
                hourly.map(h => `${h.hour}h`),
                hourly.map(h => h.avg_fare)
            );
        }
        
        if (boroughs) {
            const total = boroughs.reduce((s, b) => s + b.total_trips, 0);
            const manhattan = boroughs.find(b => b.borough === 'Manhattan');
            const pct = ((manhattan.total_trips / total) * 100).toFixed(1);
            
            ui.setText('insight-2-value', `${pct}% Market Share`);
            ui.setText('insight-2-text', 
                `Manhattan dominates with ${format.num(manhattan.total_trips)} trips (${pct}% of total), generating ${format.curr(manhattan.total_revenue)}. This concentration reveals opportunities for improved service distribution.`);
            
            charts.doughnut(
                'insight-2-chart',
                boroughs.map(b => b.borough),
                boroughs.map(b => b.total_trips)
            );
        }
        
        if (timeCategories) {
            const sorted = [...timeCategories].sort((a, b) => b.avg_speed - a.avg_speed);
            const fastest = sorted[0];
            const slowest = sorted[sorted.length - 1];
            const speedDiff = ((fastest.avg_speed - slowest.avg_speed) / slowest.avg_speed * 100).toFixed(1);
            
            const labels = {
                'late_night': 'Late Night',
                'morning_rush': 'Morning Rush',
                'midday': 'Midday',
                'evening_rush': 'Evening Rush',
                'night': 'Night'
            };
            
            ui.setText('insight-3-value', `${speedDiff}% Variance`);
            ui.setText('insight-3-text', 
                `${labels[fastest.time_category]} trips average ${format.dec(fastest.avg_speed)} mph versus ${format.dec(slowest.avg_speed)} mph during ${labels[slowest.time_category]}. Off-peak travel significantly reduces journey times.`);
            
            charts.bar(
                'insight-3-chart',
                timeCategories.map(t => labels[t.time_category]),
                timeCategories.map(t => t.avg_speed),
                chartConfig.colors.success
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
            const tbody = ui.get('data-tbody');
            tbody.innerHTML = '';
            
            trips.forEach(trip => {
                const row = tbody.insertRow();
                row.innerHTML = `
                    <td>${trip.trip_id}</td>
                    <td>${new Date(trip.pickup_datetime).toLocaleString('en-US', { 
                        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' 
                    })}</td>
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
        analytics: { title: 'Analytics', subtitle: 'Detailed performance metrics' },
        insights: { title: 'Insights', subtitle: 'Data-driven discoveries' },
        data: { title: 'Data Explorer', subtitle: 'Browse trip records' }
    };
    
    ui.setText('page-title', titles[view].title);
    ui.setText('page-subtitle', titles[view].subtitle);
    
    if (views[view]) views[view]();
};

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
    
    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `nyc-taxi-${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
};

const init = () => {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            navigate(item.dataset.view);
        });
    });
    
    ui.get('refresh-btn').addEventListener('click', () => {
        if (views[state.view]) views[state.view]();
    });
    
    ui.get('export-btn').addEventListener('click', exportCSV);
    
    ui.get('prev-btn').addEventListener('click', () => {
        if (state.page > 1) {
            state.page--;
            views.data();
        }
    });
    
    ui.get('next-btn').addEventListener('click', () => {
        state.page++;
        views.data();
    });
    
    ui.get('apply-filter').addEventListener('click', () => {
        state.page = 1;
        views.data();
    });
    
    navigate('dashboard');
};

document.addEventListener('DOMContentLoaded', init);