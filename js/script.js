// tsParticles 輕量粒子（手機自動關閉）
const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
if (!isMobile) {
  tsParticles.load("particles-js", {
    particles: {
      number: { value: 60 },
      color: { value: "#00d4ff" },
      shape: { type: "circle" },
      opacity: { value: 0.5, random: true },
      size: { value: 3, random: true },
      line_linked: { enable: true, distance: 150, color: "#00d4ff", opacity: 0.2, width: 1 },
      move: { enable: true, speed: 2 }
    },
    interactivity: { events: { onhover: { enable: true, mode: "repulse" } } },
    retina_detect: true
  });
}

// 語言切換
document.getElementById('lang-toggle').addEventListener('click', function() {
  const isEN = this.textContent.includes('EN');
  this.textContent = isEN ? '🌐 中文' : '🌐 EN';
  document.querySelectorAll('[data-en]').forEach(el => {
    if (isEN) {
      el.textContent = el.getAttribute('data-en');
      if (el.hasAttribute('data-en-placeholder')) el.placeholder = el.getAttribute('data-en-placeholder');
    } else {
      location.reload(); // 簡單做法：中文版直接重刷（因為中文是預設）
    }
  });
});

// 主題、篩選、搜尋保持原本邏輯（直接沿用你原本的）
document.getElementById('theme').addEventListener('change', e => {
  document.body.classList.toggle('dark', e.target.checked);
});

document.querySelectorAll('.filters button').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filters button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const filter = btn.getAttribute('data-filter');
    document.querySelectorAll('.card').forEach(card => {
      const category = card.getAttribute('data-category');
      card.style.display = (filter === 'all' || category === filter) ? 'block' : 'none';
    });
  });
});

document.getElementById('search').addEventListener('input', function() {
  const query = this.value.toLowerCase();
  document.querySelectorAll('.card').forEach(card => {
    const text = card.textContent.toLowerCase();
    card.style.display = text.includes(query) ? 'block' : 'none';
  });
});