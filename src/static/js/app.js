let activeFilter = 'all';

// Fetch games
function updateStats() {
    const withPrice = allGames.filter(g => g.price !== null);
    const down = allGames.filter(g => g.trend === 'down').length;
    const up = allGames.filter(g => g.trend === 'up').length;
    const avg = withPrice.length
        ? (withPrice.reduce((s, g) => s + g.price, 0) / withPrice.length).toFixed(2)
        : '—';

    document.getElementById('stat-total').textContent = allGames.length;
    document.getElementById('stat-down').textContent = down;
    document.getElementById('stat-up').textContent = up;
    document.getElementById('stat-avg').textContent = avg !== '—' ? avg + '€' : '—';
}

function renderGames() {
    const query = document.getElementById('search').value.toLowerCase();
    let games = allGames;

    if (query) games = games.filter(g => g.title.toLowerCase().includes(query));
    if (activeFilter === 'up') games = games.filter(g => g.trend === 'up');
    if (activeFilter === 'down') games = games.filter(g => g.trend === 'down');

    const container = document.getElementById('games-container');

    if (!games.length) {
        container.innerHTML = '<div class="empty"><div class="empty-icon">🎮</div><p>AUCUN JEU TROUVÉ</p></div>';
        return;
    }

    container.innerHTML = `<div class="games-grid">${games.map(gameCard).join('')}</div>`;

    container.querySelectorAll('.game-card').forEach(card => {
        card.addEventListener('click', () => openModal(card.dataset.id));
    });
}

function gameCard(game) {
    const trendBadge = game.trend === 'up'
        ? '<span class="trend-badge trend-up">▲ HAUSSE</span>'
        : game.trend === 'down'
        ? '<span class="trend-badge trend-down">▼ BAISSE</span>'
        : '';

    const img = game.image_url
        ? `<img class="game-card-image" src="${game.image_url}" alt="${game.title}" loading="lazy">`
        : `<div class="game-card-image-placeholder">🎮</div>`;

    const price = game.price != null
        ? `<span class="game-price">${game.price.toFixed(2)}€</span>`
        : `<span class="game-price no-price">N/A</span>`;

    const arrow = game.trend === 'up' ? '▲' : game.trend === 'down' ? '▼' : '';
    const arrowColor = game.trend === 'up' ? 'var(--orange)' : game.trend === 'down' ? 'var(--green)' : 'transparent';

    return `
        <div class="game-card" data-id="${game.id}">
            ${img}
            ${trendBadge}
            <div class="game-card-body">
                <div class="game-title">${game.title}</div>
                <div class="game-price-row">
                    ${price}
                    <span class="game-trend-arrow" style="color:${arrowColor}">${arrow}</span>
                </div>
            </div>
        </div>
    `;
}

async function openModal(gameId) {
    const game = allGames.find(g => g.id == gameId);
    if (!game) return;

    document.getElementById('modal-title').textContent = game.title;
    document.getElementById('modal-price').textContent = game.price ? game.price.toFixed(2) + '€' : 'N/A';
    document.getElementById('modal-img').src = game.image_url || '';
    document.getElementById('modal').classList.add('open');

    try {
        const res = await fetch(`/api/game/${gameId}/prices`);
        const prices = await res.json();
        renderChart(prices);
        renderPriceHistory(prices);
    } catch (e) {}
}

function renderChart(prices) {
    const canvas = document.getElementById('price-chart');
    canvas.width = canvas.parentElement.offsetWidth;
    canvas.height = 220;
    const ctx = canvas.getContext('2d');

    if (!prices.length) {
        ctx.fillStyle = '#5a6070';
        ctx.font = '12px Share Tech Mono';
        ctx.textAlign = 'center';
        ctx.fillText('PAS ASSEZ DE DONNÉES', canvas.width / 2, 110);
        return;
    }

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const pad = { top: 20, right: 20, bottom: 30, left: 55 };
    const w = canvas.width - pad.left - pad.right;
    const h = canvas.height - pad.top - pad.bottom;

    const vals = prices.map(p => p.price);
    const minV = Math.min(...vals) * 0.95;
    const maxV = Math.max(...vals) * 1.05;

    const xScale = i => pad.left + (i / (prices.length - 1 || 1)) * w;
    const yScale = v => pad.top + h - ((v - minV) / (maxV - minV || 1)) * h;

    // Grid lines
    ctx.strokeStyle = 'rgba(255,255,255,0.04)';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
        const y = pad.top + (h / 4) * i;
        ctx.beginPath();
        ctx.moveTo(pad.left, y);
        ctx.lineTo(pad.left + w, y);
        ctx.stroke();
    }

    // Area gradient
    const grad = ctx.createLinearGradient(0, pad.top, 0, pad.top + h);
    grad.addColorStop(0, 'rgba(232,0,45,0.3)');
    grad.addColorStop(1, 'rgba(232,0,45,0)');

    ctx.beginPath();
    prices.forEach((p, i) => {
        i === 0 ? ctx.moveTo(xScale(i), yScale(p.price)) : ctx.lineTo(xScale(i), yScale(p.price));
    });
    ctx.lineTo(xScale(prices.length - 1), pad.top + h);
    ctx.lineTo(xScale(0), pad.top + h);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();

    // Line
    ctx.beginPath();
    prices.forEach((p, i) => {
        i === 0 ? ctx.moveTo(xScale(i), yScale(p.price)) : ctx.lineTo(xScale(i), yScale(p.price));
    });
    ctx.strokeStyle = '#e8002d';
    ctx.lineWidth = 2;
    ctx.shadowColor = 'rgba(232,0,45,0.6)';
    ctx.shadowBlur = 8;
    ctx.stroke();
    ctx.shadowBlur = 0;

    // Y labels
    ctx.fillStyle = '#5a6070';
    ctx.font = '10px Share Tech Mono';
    ctx.textAlign = 'right';
    [minV, (minV + maxV) / 2, maxV].forEach(v => {
        ctx.fillText(v.toFixed(0) + '€', pad.left - 6, yScale(v) + 4);
    });

    // Dots
    prices.forEach((p, i) => {
        ctx.beginPath();
        ctx.arc(xScale(i), yScale(p.price), 3, 0, Math.PI * 2);
        ctx.fillStyle = '#e8002d';
        ctx.shadowColor = 'rgba(232,0,45,0.8)';
        ctx.shadowBlur = 6;
        ctx.fill();
        ctx.shadowBlur = 0;
    });
}

function renderPriceHistory(prices) {
    const tbody = document.getElementById('price-history-body');
    if (!prices.length) {
        tbody.innerHTML = '<tr><td colspan="3" style="color:var(--text-muted);text-align:center;padding:20px">Aucun historique</td></tr>';
        return;
    }

    tbody.innerHTML = prices.slice().reverse().map((p, i, arr) => {
        const prev = arr[i + 1];
        let variation = '—';
        let color = 'var(--text-muted)';
        if (prev) {
            const diff = p.price - prev.price;
            if (diff > 0) { variation = `▲ +${diff.toFixed(2)}€`; color = 'var(--orange)'; }
            else if (diff < 0) { variation = `▼ ${diff.toFixed(2)}€`; color = 'var(--green)'; }
            else { variation = '— stable'; }
        }
        return `
            <tr>
                <td>${new Date(p.scraped_at).toLocaleDateString('fr-FR')}</td>
                <td>${p.price.toFixed(2)}€</td>
                <td style="color:${color}">${variation}</td>
            </tr>
        `;
    }).join('');
}

// Event listeners
document.getElementById('filter-up').addEventListener('click', () => {
    activeFilter = activeFilter === 'up' ? 'all' : 'up';
    document.getElementById('filter-up').classList.toggle('active', activeFilter === 'up');
    document.getElementById('filter-down').classList.remove('active');
    renderGames();
});

document.getElementById('filter-down').addEventListener('click', () => {
    activeFilter = activeFilter === 'down' ? 'all' : 'down';
    document.getElementById('filter-down').classList.toggle('active', activeFilter === 'down');
    document.getElementById('filter-up').classList.remove('active');
    renderGames();
});

document.getElementById('filter-all').addEventListener('click', () => {
    activeFilter = 'all';
    document.getElementById('filter-up').classList.remove('active');
    document.getElementById('filter-down').classList.remove('active');
    renderGames();
});

document.getElementById('search').addEventListener('input', renderGames);

document.getElementById('modal-close').addEventListener('click', () => {
    document.getElementById('modal').classList.remove('open');
});

document.getElementById('modal').addEventListener('click', e => {
    if (e.target === document.getElementById('modal')) {
        document.getElementById('modal').classList.remove('open');
    }
});
updateStats();
renderGames();