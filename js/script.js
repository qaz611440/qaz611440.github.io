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

// ---------- 這裡開始是完全修正且保證可用的版本 ----------
let currentFilter = 'all';

const filters = document.querySelectorAll('.filters button');
const searchInput = document.getElementById('search');
const cards = document.querySelectorAll('.card');

// 篩選按鈕
filters.forEach(btn => {
  btn.addEventListener('click', () => {
    filters.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentFilter = btn.dataset.filter;
    filterProjects();
  });
});

// 搜尋欄
searchInput.addEventListener('input', () => {
  filterProjects();
});

// 主過濾函數（篩選 + 搜尋完美結合）
function filterProjects() {
  const query = searchInput.value.toLowerCase();

  cards.forEach(card => {
    const category = card.dataset.category;
    const text = card.textContent.toLowerCase();

    const matchCategory = (currentFilter === 'all' || category === currentFilter);
    const matchSearch = text.includes(query);

    if (matchCategory && matchSearch) {
      card.classList.remove('hidden');
    } else {
      card.classList.add('hidden');
    }
  });
}

// 頁面載入完成後立即執行一次（確保一開始顯示「全部」）
document.addEventListener('DOMContentLoaded', () => {
  // 預設顯示全部 + 讓「全部」按鈕有 active
  document.querySelector('.filters button[data-filter="all"]').classList.add('active');
  filterProjects();
});