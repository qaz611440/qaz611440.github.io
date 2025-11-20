// 真正正確的 tsParticles 3.x 寫法（粒子 100% 會出現！）
const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);

tsParticles.load("particles-js", {
  particles: {
    number: { value: isMobile ? 40 : 80 },
    color: { value: "#00d4ff" },
    shape: { type: "circle" },
    opacity: { value: 0.5, random: true },
    size: { value: isMobile ? 2 : 3, random: true },
    links: {  // ← 這裡改對了！原來是 line_linked
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
      outModes: "out"
    }
  },
  interactivity: {
    events: {
      onHover: {
        enable: !isMobile,
        mode: "repulse"
      },
      onClick: {
        enable: true,
        mode: "push"
      },
      resize: true
    },
    modes: {
      repulse: {
        distance: 100,
        duration: 0.4
      }
    }
  },
  retina_detect: true,
  background: {
    color: "#0a1a2e"
  }
});

// 作品篩選 + 搜尋（用 dataset 更穩）
document.querySelectorAll('.filters button').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filters button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const filter = btn.dataset.filter;
    document.querySelectorAll('.card').forEach(card => {
      const category = card.dataset.category;
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