// 真正正確的 tsParticles 3.x 寫法（粒子超美、手機也超順！）
const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);

tsParticles.load("particles-js", {
  background: {
    color: { value: "#0a1a2e" }
  },
  fpsLimit: 120,
  particles: {
    number: { value: isMobile ? 40 : 80, density: { enable: true, value_area: 800 } },
    color: { value: "#00d4ff" },
    shape: { type: "circle" },
    opacity: { value: 0.5, random: true, anim: { enable: true, speed:  1, sync: false } },
    size: { value: isMobile ? 2.5 : 3.5, random: true },
    links: {
      enable: true,
      distance: 150,
      color: "#00d4ff",
      opacity: 0.3,
      width: 1
    },
    move: {
      enable: true,
      speed: isMobile ? 2 : 3,
      direction: "none",
      random: false,
      straight: false,
      outModes: { default: "out" }
    }
  },
  interactivity: {
    detect_on: "canvas",
    events: {
      onHover: { enable: !isMobile, mode: "repulse" },
      onClick: { enable: true, mode: "push" },
      resize: true
    },
    modes: {
      repulse: { distance: 100, duration: 0.4 },
      push: { quantity: 4 }
    }
  },
  detectRetina: true
});

// 作品篩選 + 搜尋（完美運作）
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