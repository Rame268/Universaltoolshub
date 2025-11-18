// Global small helpers. Nothing malicious, just convenience.
(function(){
  // Prevent double form submission in simple cases
  document.addEventListener('submit', function(ev){
    const btn = ev.target.querySelector('button[type="submit"]');
    if (btn){
      btn.disabled = true;
      setTimeout(()=> btn.disabled = false, 1500);
    }
  });
})();
