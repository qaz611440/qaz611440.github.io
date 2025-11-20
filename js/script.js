// 粒子背景
particlesJS('particles-js', {
  particles: {
    number: { value: 80, density: { enable: true, value_area: 800 } },
    color: { value: '#00d4ff' },
    shape: { type: 'circle' },
    opacity: { value: 0.5, random: true },
    size: { value: 3, random: true },
    line_linked: { enable: true, distance: 150, color: '#00d4ff', opacity: 0.2, width: 1 },
    move: { enable: true, speed: 2 }
  },
  interactivity: { events: { onhover: { enable: true, mode: 'repulse' } } }
});

// 作品篩選 + 搜尋（使用 class toggle 避免布局衝突，並讓搜尋基於當前篩選結果）
let currentFilter = 'all'; // 追蹤當前篩選類別

// 篩選功能
document.querySelectorAll('.filters button').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filters button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentFilter = btn.dataset.filter;
    applyFiltersAndSearch(); // 應用篩選並重新應用搜尋
  });
});

// 搜尋功能
document.getElementById('search').addEventListener('input', function() {
  applyFiltersAndSearch(); // 每次輸入都重新應用篩選 + 搜尋
});

// 組合應用篩選和搜尋的函數
function applyFiltersAndSearch() {
  const query = document.getElementById('search').value.toLowerCase();
  document.querySelectorAll('.card').forEach(card => {
    const matchesFilter = (currentFilter === 'all' || card.dataset.category === currentFilter);
    const text = card.textContent.toLowerCase();
    const matchesSearch = text.includes(query);
    card.classList.toggle('hidden', !(matchesFilter && matchesSearch));
  });
}

// 頁面載入時初始應用（顯示全部）
window.addEventListener('load', () => {
  applyFiltersAndSearch();
});