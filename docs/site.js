document.documentElement.classList.add('js');
const root = document.documentElement;
const motion = matchMedia('(prefers-reduced-motion: reduce)');
const button = document.querySelector('.theme-toggle');
function applyTheme(theme) {
  root.dataset.theme = theme;
  const dark = theme === 'dark';
  button.setAttribute('aria-pressed', String(dark));
  button.setAttribute('aria-label', `Switch to ${dark ? 'light' : 'dark'} mode`);
  button.querySelector('span').textContent = '';
  button.querySelector('svg').innerHTML = dark
    ? '<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42"/>'
    : '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79Z"/>';
  document.querySelector('meta[name="theme-color"]').content = dark ? '#101815' : '#f4f2eb';
  document.querySelectorAll('img[data-light][data-dark]').forEach(img => {
    img.src = dark ? img.dataset.dark : img.dataset.light;
  });
  document.querySelectorAll('video[data-light][data-dark]').forEach(video=>{video.src=dark?video.dataset.dark:video.dataset.light;if(!video.hidden&&!motion.matches)video.play().catch(()=>{})});
}
applyTheme(root.dataset.theme || 'light');
// One full-screen polygon avoids subpixel seams between separate columns.
let switching = false;
function pixelEdge(progress, reveal) {
 const w=innerWidth,h=innerHeight,columns=14,cell=Math.max(24,Math.round(w/columns));
 const heights=Array.from({length:columns},(_,i)=>{
  const stagger=((i*5)%7)*.018;
  const t=Math.max(0,Math.min(1,(progress-stagger)/.87));
  return t===1?h:Math.min(h,Math.floor(t*(h+cell)/cell)*cell);
 });
 const points=reveal?[[0,h],[w,h]]:[[0,0],[w,0]];
 for(let i=columns-1;i>=0;i--){points.push([Math.round((i+1)*w/columns),heights[i]],[Math.round(i*w/columns),heights[i]])}
 return 'polygon('+points.map(([x,y])=>`${x}px ${y}px`).join(',')+')';
}
function animateCurtain(curtain,reveal){
 return new Promise(resolve=>{
  let start;
  function frame(now){if(start===undefined)start=now;const p=Math.min(1,(now-start)/420);curtain.style.clipPath=pixelEdge(p,reveal);if(p<1)requestAnimationFrame(frame);else resolve()}
  requestAnimationFrame(frame);
 });
}
button.addEventListener('click', async () => {
 if(switching)return;switching=true;
 const theme=root.dataset.theme==='dark'?'light':'dark';
 const update=()=>{applyTheme(theme);try{localStorage.setItem('museum-theme',theme)}catch{}};
 if(motion.matches){update();switching=false;return}
 const curtain=document.createElement('div');curtain.className='theme-curtain';curtain.setAttribute('aria-hidden','true');curtain.style.setProperty('--curtain-color',theme==='dark'?'#101815':'#f4f2eb');curtain.style.clipPath=pixelEdge(0,false);document.body.append(curtain);
 try{await animateCurtain(curtain,false);update();await animateCurtain(curtain,true)}finally{curtain.remove();switching=false}
});
const reveals = document.querySelectorAll('.reveal');
if ('IntersectionObserver' in window && !motion.matches) {
  const observer = new IntersectionObserver(entries => entries.forEach(entry => {
    if (entry.isIntersecting) { entry.target.classList.add('visible'); observer.unobserve(entry.target); }
  }), { threshold: .06 });
  reveals.forEach(el => observer.observe(el));
} else reveals.forEach(el => el.classList.add('visible'));
const year = document.getElementById('year');
if (year) year.textContent = String(new Date().getFullYear());
const progress = document.querySelector('.reading-progress');
let scheduled = false;
function scrollProgress() {
  scheduled = false;
  const height = document.documentElement.scrollHeight - innerHeight;
  progress.style.transform = `scaleX(${height > 0 ? scrollY / height : 0})`;
}
addEventListener('scroll', () => { if (!scheduled) { scheduled = true; requestAnimationFrame(scrollProgress); } }, { passive:true });
addEventListener('resize', scrollProgress); scrollProgress();
const pixels = [...document.querySelectorAll('.brand-pixel')];
const colors = ['#ce9c43','#80a68c','#bd8776','#a099c1','#83aab5'];
let previous = -1, sequence = 0;
setInterval(() => {
  if (motion.matches || document.hidden) return;
  pixels.forEach(p => p.classList.remove('lit'));
  let index; do { index = Math.floor(Math.random() * pixels.length); } while (index === previous && pixels.length > 1);
  if (pixels[index]) { pixels[index].style.setProperty('--pixel-color', colors[sequence++ % colors.length]); pixels[index].classList.add('lit'); previous = index; }
}, 1500);
const viewer = document.querySelector('.image-viewer');
const viewerImage = viewer.querySelector('img');
let originButton;
document.querySelectorAll('.screenshot-button').forEach(trigger => trigger.addEventListener('click', () => {
  const img = trigger.querySelector('img'); viewerImage.src = img.currentSrc || img.src; viewerImage.alt = img.alt;
  originButton = trigger; viewer.showModal();
}));
viewer.querySelector('button').addEventListener('click', () => viewer.close());
viewer.addEventListener('click', e => { if (e.target === viewer) viewer.close(); });
viewer.addEventListener('close', () => originButton?.focus({preventScroll:true}));
document.querySelector('.masthead .brand').addEventListener('click', () => {
  if (motion.matches) return;
  pixels.forEach((p,i) => { p.style.setProperty('--pixel-color', colors[i % colors.length]); p.classList.add('lit'); });
});
const wayCards=[...document.querySelectorAll('.way-card')];
const wayPanel=document.querySelector('.way-detail');
const wayData=[
 {title:'A little closer to the story.',copy:'Open an image, fill the screen and take in the details. Every object has a story to tell.',light:'assets/closer-light.webp',dark:'assets/closer-dark.webp',videoLight:'assets/closer-light.mp4',videoDark:'assets/closer-dark.mp4',alt:'Zooming into a Celeste image in Pixel Museum'},
 {title:'You know it when you hear it.',copy:'Listen to game soundtracks streamed from YouTube. On the cultural timeline, discover film themes, songs, historic voices and everyday sounds that bring a moment back.',light:'assets/listening-light.webp',dark:'assets/listening-dark.webp',alt:'The Journey soundtrack card in Pixel Museum'},
 {title:'Discover. Collect. Take a closer look.',copy:'Exploring unlocks collectible pins. Open them in 3D to turn them around and discover their details.',light:'assets/collection-3d-light.webp',dark:'assets/collection-3d-dark.webp',videoLight:'assets/collection-3d-light.mp4',videoDark:'assets/collection-3d-dark.mp4',alt:'Want to see my collection? - denim jacket pin open in the Pixel Museum 3D viewer'}
];
let selectedWay=2;
function selectWay(i){
 selectedWay=i;wayPanel.classList.remove('is-changing');requestAnimationFrame(()=>wayPanel.classList.add('is-changing'));wayCards.forEach((c,n)=>c.setAttribute('aria-expanded',String(n===i)));
 const d=wayData[i],img=document.getElementById('way-detail-image'),video=document.getElementById('way-detail-video'),dark=root.dataset.theme==='dark';
 img.dataset.light=d.light;img.dataset.dark=d.dark;img.src=dark?d.dark:d.light;img.alt=d.alt;
 video.pause();video.hidden=true;img.hidden=false;video.setAttribute("aria-label",d.alt);
 if(d.videoLight&&!motion.matches){video.dataset.light=d.videoLight;video.dataset.dark=d.videoDark;video.src=dark?d.videoDark:d.videoLight;video.poster=img.src;video.hidden=false;img.hidden=true;video.muted=true;video.play().catch(()=>{video.hidden=true;img.hidden=false})}
 document.getElementById('way-detail-title').textContent=d.title;document.getElementById('way-detail-copy').textContent=d.copy;
}
wayCards.forEach((card,i)=>card.addEventListener('click',()=>selectWay(i)));
const creditsDisclosure=document.querySelector('.source-credit');
creditsDisclosure.addEventListener('toggle',()=>{if(creditsDisclosure.open&&!motion.matches){[...creditsDisclosure.children].filter(el=>el.tagName!=='SUMMARY').forEach(el=>el.animate([{opacity:0,transform:'translateY(-8px)'},{opacity:1,transform:'translateY(0)'}],{duration:320,easing:'ease-out'}))}});

selectWay(2);

// One crisp pixel follows fine pointers; clickable controls light it up.
if(matchMedia('(hover:hover) and (pointer:fine)').matches){
 const cursor=document.createElement('div');cursor.className='pixel-pointer';cursor.setAttribute('aria-hidden','true');document.body.append(cursor);
 const clickable='a[href],button,summary,[role="button"],input,select,textarea';
 document.addEventListener('pointermove',e=>{if(e.pointerType==='touch')return;cursor.style.left=e.clientX+'px';cursor.style.top=e.clientY+'px';cursor.classList.add('visible');cursor.classList.toggle('clickable',!!document.elementFromPoint(e.clientX,e.clientY)?.closest(clickable));document.documentElement.classList.add('pixel-pointer-active')},{passive:true,capture:true});
 document.addEventListener('pointerout',e=>{if(!e.relatedTarget){cursor.classList.remove('visible');document.documentElement.classList.remove('pixel-pointer-active')}});
 window.addEventListener('blur',()=>{cursor.classList.remove('visible');document.documentElement.classList.remove('pixel-pointer-active')});
}

// Paired screenshots and their two connected timelines share one clock.
const timelineYears=[1963,1989,1999,2013];
const timelineTitles={1963:['Hideo Kojima','The assassination of John F. Kennedy'],1989:['Game Boy','The fall of the Berlin Wall'],1999:['Crash Team Racing','Roberto Benigni at the Academy Awards'],2013:['The Stanley Parable','Random Access Memories by Daft Punk']};
const timelineScreens=[document.querySelector('.app-frame img'),document.querySelector('.culture-frame img')];
const timelineButtons=[...document.querySelectorAll('[data-timeline-year]')];
let timelineIndex=2,timelineElapsed=0,timelineVersion=0;
const onscreen=new Set();
async function setTimeline(index){
 if(index===timelineIndex)return;
 timelineIndex=index;timelineElapsed=0;const version=++timelineVersion,year=timelineYears[index];
 const sources=timelineScreens.map((_,i)=>({light:`assets/timeline-${year}-${i?'culture':'game'}-light.webp`,dark:`assets/timeline-${year}-${i?'culture':'game'}-dark.webp`}));
 await Promise.all(sources.map(pair=>{const im=new Image();im.src=root.dataset.theme==='dark'?pair.dark:pair.light;return im.decode().catch(()=>{})}));
 if(version!==timelineVersion)return;
 timelineScreens.forEach(im=>im.classList.add('changing'));
 setTimeout(()=>{if(version!==timelineVersion)return;timelineButtons.forEach((b,i)=>b.setAttribute('aria-pressed',String(i===index)));const rail=document.querySelector('.two-lines');rail.style.setProperty('--active-index',String(index));rail.classList.remove('year-arrival');requestAnimationFrame(()=>rail.classList.add('year-arrival'));timelineScreens.forEach((im,i)=>{im.dataset.light=sources[i].light;im.dataset.dark=sources[i].dark;im.src=root.dataset.theme==='dark'?sources[i].dark:sources[i].light;im.alt=timelineTitles[year][i]+` on the ${year} timeline`;im.onload=()=>im.classList.remove('changing');if(im.complete)im.classList.remove('changing')})},190);
}
timelineButtons.forEach((b,i)=>b.addEventListener('click',()=>setTimeline(i)));
if('IntersectionObserver' in window){const observation=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting)onscreen.add(e.target);else onscreen.delete(e.target)}),{threshold:.12});document.querySelectorAll('.first-look,.story').forEach(el=>observation.observe(el))}else onscreen.add(document.body);
setInterval(()=>{if(document.hidden||motion.matches||!onscreen.size||document.querySelector('[data-timeline-year]:hover'))return;timelineElapsed+=250;if(timelineElapsed>=4000)setTimeline((timelineIndex+1)%4)},250);
let shadowIndex=0;const shadows=[...document.querySelectorAll('.welcome-shadows img')];shadows[0]?.classList.add('active');
setInterval(()=>{if(document.hidden||motion.matches)return;shadows[shadowIndex]?.classList.remove('active');shadowIndex=(shadowIndex+1)%shadows.length;shadows[shadowIndex]?.classList.add('active')},5500);

// Real gameplay preview: silent, and active only while visible.
const flightPreview=document.querySelector('.flight-preview');
if(flightPreview){let visible=false;const syncFlight=()=>{if(visible&&!document.hidden&&!motion.matches)flightPreview.play().catch(()=>{});else flightPreview.pause()};new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;syncFlight()},{threshold:.15}).observe(flightPreview);document.addEventListener('visibilitychange',syncFlight);motion.addEventListener('change',syncFlight)}

// Start quietly; play only while the teaser is visible and the page is active.
(() => {
  const video = document.querySelector('#museum-teaser');
  if (!video) return;
  let inView = false;
  video.defaultMuted = true;
  video.muted = true;
  const updatePlayback = () => {
    if (inView && !document.hidden) video.play().catch(() => {});
    else video.pause();
  };
  const observer = new IntersectionObserver(([entry]) => {
    inView = entry.isIntersecting;
    updatePlayback();
  }, { threshold: 0 });
  observer.observe(video);
  document.addEventListener('visibilitychange', updatePlayback);
})();
