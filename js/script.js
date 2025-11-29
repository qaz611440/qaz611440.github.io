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

// --- 篩選與搜尋功能 ---
let currentFilter = 'all';
const filters = document.querySelectorAll('.filters button');
const searchInput = document.getElementById('search');
const cards = document.querySelectorAll('.card');

filters.forEach(btn => {
  btn.addEventListener('click', () => {
    filters.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentFilter = btn.dataset.filter;
    filterProjects();
  });
});

searchInput.addEventListener('input', () => {
  filterProjects();
});

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

// --- 燈箱控制 ---
const lightbox = document.getElementById('imageLightbox');
const lightboxImg = document.getElementById('lightboxImg');

function openImage(src) {
  lightbox.style.display = "block";
  lightboxImg.src = src;
}

function closeLightbox() {
  lightbox.style.display = "none";
}

window.onclick = function(event) {
  if (event.target == lightbox) {
    lightbox.style.display = "none";
  }
}

// --- 回到頂部按鈕 ---
const backToTopBtn = document.getElementById("backToTop");

window.onscroll = function() {
  if (document.body.scrollTop > 300 || document.documentElement.scrollTop > 300) {
    backToTopBtn.classList.add("show");
  } else {
    backToTopBtn.classList.remove("show");
  }
  highlightNav();
};

backToTopBtn.addEventListener("click", function() {
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

// --- 導覽列滾動監聽 ---
const sections = document.querySelectorAll("section");
const navLinks = document.querySelectorAll(".nav-link");

function highlightNav() {
  let scrollY = window.scrollY;
  
  sections.forEach(current => {
    const sectionHeight = current.offsetHeight;
    const sectionTop = current.offsetTop - 100; 
    const sectionId = current.getAttribute("id");
    
    if (scrollY > sectionTop && scrollY <= sectionTop + sectionHeight) {
      navLinks.forEach(link => {
        link.classList.remove("active");
        if (link.getAttribute("href").includes(sectionId)) {
          link.classList.add("active");
        }
      });
    }
  });
}

// --- 初始化 ---
document.addEventListener('DOMContentLoaded', () => {
  document.querySelector('.filters button[data-filter="all"]').classList.add('active');
  filterProjects();
});