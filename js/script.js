// 全裝置粒子特效（手機自動優化，超順超美！）
const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);

tsParticles.load("particles-js", {
  particles: {
    number: { value: isMobile ? 30 : 60 },
    color: { value: "#00d4ff" },
    shape: { type: "circle" },
    opacity: { value: 0.5, random: true },
    size: { value: isMobile ? 2 : 3, random: true },
    line_linked: { enable: true, distance: 150, color: "#00d4ff", opacity: 0.2, width: 1 },
    move: { enable: true, speed: isMobile ? 1.5 : 2 }
  },
  interactivity: {
    events: { onhover: { enable: !isMobile, mode: "repulse" } },  // 手機關 hover 互動
    ontouch: { enable: true, mode: "repulse" }  // 手機可以用手指推開粒子！
  },
  retina_detect: true
});

// 深色模式
document.getElementById('theme').addEventListener('change', e => {
  document.body.classList.toggle('dark', e.target.checked);
});

// 作品篩選 + 搜尋
document.querySelectorAll('.filters button').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filters button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const filter = btn.dataset.filter;
    document.querySelectorAll('.card').forEach(card => {
      card.style.display = (filter === 'all' || card.dataset.category === filter) ? 'block' : 'none';
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