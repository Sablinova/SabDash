/* SabDash — Main JavaScript
   Particles, hover SFX, easter egg, volume control, flash auto-dismiss
*/

(function() {
    'use strict';

    // === Audio Context (lazy init) ===
    var audioCtx = null;
    function getAudioCtx() {
        if (!audioCtx) {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        return audioCtx;
    }

    // === Particles ===
    function initParticles() {
        var container = document.getElementById('particles');
        if (!container) return;
        var count = 30;
        for (var i = 0; i < count; i++) {
            var p = document.createElement('div');
            p.className = 'particle';
            p.style.left = (Math.random() * 100) + '%';
            p.style.top = (Math.random() * 100) + '%';
            var dur = 8 + Math.random() * 15;
            var delay = Math.random() * 10;
            p.style.animationDuration = dur + 's';
            p.style.animationDelay = delay + 's';
            container.appendChild(p);
        }
    }

    // === Hover Sound Effect ===
    function playHoverSfx() {
        try {
            var ctx = getAudioCtx();
            var osc = ctx.createOscillator();
            var gain = ctx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(800, ctx.currentTime);
            osc.frequency.exponentialRampToValueAtTime(1200, ctx.currentTime + 0.06);
            gain.gain.setValueAtTime(0.08, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.12);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start(ctx.currentTime);
            osc.stop(ctx.currentTime + 0.12);
        } catch(e) {}
    }

    function initHoverSounds() {
        var cards = document.querySelectorAll('.stat-card, .project-card');
        cards.forEach(function(card) {
            card.addEventListener('mouseenter', playHoverSfx);
        });
    }

    // === Logo Easter Egg (5 clicks = spin) ===
    function initEasterEgg() {
        var logo = document.getElementById('dashLogo');
        if (!logo) return;
        var clicks = [];
        logo.addEventListener('click', function() {
            var now = Date.now();
            clicks.push(now);
            // Keep only clicks within last 2 seconds
            clicks = clicks.filter(function(t) { return now - t < 2000; });
            if (clicks.length >= 5) {
                clicks = [];
                logo.style.animation = 'logoRoll 1.2s ease-in-out';
                // Play whoosh
                try {
                    var ctx = getAudioCtx();
                    var osc = ctx.createOscillator();
                    var gain = ctx.createGain();
                    osc.type = 'sawtooth';
                    osc.frequency.setValueAtTime(200, ctx.currentTime);
                    osc.frequency.exponentialRampToValueAtTime(2000, ctx.currentTime + 0.6);
                    osc.frequency.exponentialRampToValueAtTime(100, ctx.currentTime + 1.2);
                    gain.gain.setValueAtTime(0.06, ctx.currentTime);
                    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 1.2);
                    osc.connect(gain);
                    gain.connect(ctx.destination);
                    osc.start(ctx.currentTime);
                    osc.stop(ctx.currentTime + 1.2);
                } catch(e) {}
                setTimeout(function() {
                    logo.style.animation = 'logoPulse 4s ease-in-out infinite';
                }, 1300);
            }
        });
    }

    // === Volume Control ===
    function initVolumeControl() {
        var slider = document.getElementById('volumeSlider');
        var icon = document.getElementById('volumeIcon');
        var pct = document.getElementById('volumePct');
        if (!slider || !icon || !pct) return;

        var muted = false;
        var prevVol = 10;

        function updateIcon(val) {
            if (val === 0) {
                icon.textContent = '\uD83D\uDD07'; // muted
            } else if (val < 40) {
                icon.textContent = '\uD83D\uDD09'; // low
            } else {
                icon.textContent = '\uD83D\uDD0A'; // high
            }
            pct.textContent = val + '%';
        }

        slider.addEventListener('input', function() {
            var val = parseInt(this.value);
            updateIcon(val);
            muted = val === 0;
            // TODO: apply to background music when added
        });

        icon.addEventListener('click', function() {
            if (muted) {
                slider.value = prevVol;
                updateIcon(prevVol);
                muted = false;
            } else {
                prevVol = parseInt(slider.value) || 10;
                slider.value = 0;
                updateIcon(0);
                muted = true;
            }
        });

        updateIcon(parseInt(slider.value));
    }

    // === Flash Message Auto-Dismiss ===
    function initFlashDismiss() {
        var flashes = document.querySelectorAll('.flash');
        flashes.forEach(function(flash) {
            setTimeout(function() {
                flash.style.opacity = '0';
                flash.style.transform = 'translateY(-10px)';
                flash.style.transition = 'all 0.4s ease';
                setTimeout(function() { flash.remove(); }, 400);
            }, 5000);
        });
    }

    // === Init ===
    document.addEventListener('DOMContentLoaded', function() {
        initParticles();
        initHoverSounds();
        initEasterEgg();
        initVolumeControl();
        initFlashDismiss();
    });
})();
