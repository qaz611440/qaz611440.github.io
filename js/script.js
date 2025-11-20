// 全裝置粒子特效（手機自動優化）
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
    events: { 
      onhover: { enable: !isMobile, mode: "repulse" },
      ontouch: { enable: true, mode: "repulse" }  // 手指也能推開粒子！
    }
  },
  retina_detect: true
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