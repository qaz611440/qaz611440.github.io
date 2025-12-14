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

// --- 篩選與搜尋功能 (作品集 Projects) ---
let currentProjectFilter = 'all';
// 注意：這裡改成選取 .project-filters 裡面的按鈕
const projectFilters = document.querySelectorAll('.project-filters button');
const searchInput = document.getElementById('search');
const cards = document.querySelectorAll('.card');

if(projectFilters.length > 0) {
  projectFilters.forEach(btn => {
    btn.addEventListener('click', () => {
      projectFilters.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentProjectFilter = btn.dataset.filter;
      filterProjects();
    });
  });
}

if(searchInput) {
  searchInput.addEventListener('input', () => {
    filterProjects();
  });
}

function filterProjects() {
  const query = searchInput.value.toLowerCase();
  cards.forEach(card => {
    const category = card.dataset.category;
    const text = card.textContent.toLowerCase();
    const matchCategory = (currentProjectFilter === 'all' || category === currentProjectFilter);
    const matchSearch = text.includes(query);

    if (matchCategory && matchSearch) {
      card.classList.remove('hidden');
    } else {
      card.classList.add('hidden');
    }
  });
}

// --- 篩選功能 (技能 Skills) ---
// 新增：專門處理技能的篩選邏輯
const skillFilters = document.querySelectorAll('.skill-filters button');
const skillItems = document.querySelectorAll('.skill-item');

if(skillFilters.length > 0) {
  skillFilters.forEach(btn => {
    btn.addEventListener('click', () => {
      // 移除其他按鈕 active 狀態
      skillFilters.forEach(b => b.classList.remove('active'));
      // 啟用當前按鈕
      btn.classList.add('active');
      
      const filterValue = btn.dataset.filter;
      
      skillItems.forEach(item => {
        if (filterValue === 'all' || item.dataset.category === filterValue) {
          item.classList.remove('hidden');
        } else {
          item.classList.add('hidden');
        }
      });
    });
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

// 原本的代碼已經很好，確認這一塊邏輯運作正常即可
window.onclick = function(event) {
  if (event.target == lightbox) {
    lightbox.style.display = "none";
  }
}

// --- 回到頂部按鈕 ---
const backToTopBtn = document.getElementById("backToTop");

window.onscroll = function() {
  // 顯示/隱藏回到頂部按鈕
  if (document.body.scrollTop > 300 || document.documentElement.scrollTop > 300) {
    backToTopBtn.classList.add("show");
  } else {
    backToTopBtn.classList.remove("show");
  }
  
  // 導覽列 Active 狀態切換
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
    const sectionTop = current.offsetTop - 100; // 減去 Navbar 高度誤差
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

// --- 手機版導覽列優化：點擊後自動捲動按鈕到中間 ---
const navContainer = document.querySelector('.nav-container');

navLinks.forEach(link => {
  link.addEventListener('click', function() {
    // 取得被點擊按鈕的位置
    const scrollLeft = this.offsetLeft - (window.innerWidth / 2) + (this.offsetWidth / 2);
    
    // 平滑捲動導覽列
    navContainer.scrollTo({
      left: scrollLeft,
      behavior: 'smooth'
    });
  });
});

// --- 初始化 ---
document.addEventListener('DOMContentLoaded', () => {
  // 初始化作品集篩選
  const allProjectBtn = document.querySelector('.project-filters button[data-filter="all"]');
  if(allProjectBtn) allProjectBtn.classList.add('active');
  filterProjects();

  // 初始化技能篩選
  const allSkillBtn = document.querySelector('.skill-filters button[data-filter="all"]');
  if(allSkillBtn) allSkillBtn.classList.add('active');
});