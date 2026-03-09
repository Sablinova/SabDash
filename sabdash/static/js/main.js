/* SabDash — Main JavaScript
   Ports the full 2b.sablinova.com/bot/ interactivity:
   Enter screen, CRT flicker + power-on SFX, floating command background,
   collapsible cogs, search with meta text, scroll-to-top, volume control,
   nav hamburger, keyboard shortcuts, flash auto-dismiss.
*/
(function() {
    'use strict';

    /* =========================================================
       Audio Context (lazy init)
       ========================================================= */
    var audioCtx = null;
    function getAudioCtx() {
        if (!audioCtx) {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        return audioCtx;
    }

    /* =========================================================
       CRT Power-On SFX  (Web Audio API — no files needed)
       Sine sweep 60->2000->800Hz + white noise burst + square beep 1200Hz
       ========================================================= */
    function playCrtOn() {
        try {
            var ctx = getAudioCtx();
            var now = ctx.currentTime;
            var master = ctx.createGain();
            master.gain.setValueAtTime(0.18, now);
            master.connect(ctx.destination);

            // 1) Sine sweep
            var sweep = ctx.createOscillator();
            var sweepGain = ctx.createGain();
            sweep.type = 'sine';
            sweep.frequency.setValueAtTime(60, now);
            sweep.frequency.exponentialRampToValueAtTime(2000, now + 0.15);
            sweep.frequency.exponentialRampToValueAtTime(800, now + 0.4);
            sweepGain.gain.setValueAtTime(0.35, now);
            sweepGain.gain.exponentialRampToValueAtTime(0.001, now + 0.5);
            sweep.connect(sweepGain);
            sweepGain.connect(master);
            sweep.start(now);
            sweep.stop(now + 0.5);

            // 2) White noise burst
            var bufSize = ctx.sampleRate * 0.3;
            var noiseBuf = ctx.createBuffer(1, bufSize, ctx.sampleRate);
            var data = noiseBuf.getChannelData(0);
            for (var i = 0; i < bufSize; i++) {
                data[i] = (Math.random() * 2 - 1) * 0.5;
            }
            var noise = ctx.createBufferSource();
            noise.buffer = noiseBuf;
            var noiseGain = ctx.createGain();
            noiseGain.gain.setValueAtTime(0.25, now);
            noiseGain.gain.exponentialRampToValueAtTime(0.001, now + 0.3);
            noise.connect(noiseGain);
            noiseGain.connect(master);
            noise.start(now);
            noise.stop(now + 0.3);

            // 3) Square beep
            var beep = ctx.createOscillator();
            var beepGain = ctx.createGain();
            beep.type = 'square';
            beep.frequency.setValueAtTime(1200, now + 0.1);
            beepGain.gain.setValueAtTime(0, now);
            beepGain.gain.setValueAtTime(0.08, now + 0.1);
            beepGain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
            beep.connect(beepGain);
            beepGain.connect(master);
            beep.start(now + 0.1);
            beep.stop(now + 0.25);
        } catch(e) {}
    }

    /* =========================================================
       Enter Screen + CRT Flicker Transition
       ========================================================= */
    var hasEntered = false;

    function handleEnter() {
        if (hasEntered) return;
        hasEntered = true;

        var enterScreen = document.getElementById('enterScreen');
        var crtFlicker = document.getElementById('crtFlicker');
        var mainApp = document.getElementById('mainApp');
        var volumeCtrl = document.getElementById('volumeControl');

        if (!enterScreen || !crtFlicker || !mainApp) return;

        // Play CRT power-on SFX
        playCrtOn();

        // Hide enter screen
        enterScreen.classList.add('hidden');

        // Fire CRT flicker transition
        crtFlicker.classList.add('active');

        // After 1s transition completes, show main app
        setTimeout(function() {
            crtFlicker.classList.remove('active');
            mainApp.classList.add('visible');
            if (volumeCtrl) volumeCtrl.classList.add('visible');

            // Start floating command background
            startFloatingCmds();

            // Mark session as entered
            sessionStorage.setItem('sabdash_entered', '1');
        }, 1000);
    }

    function initEnterScreen() {
        var enterScreen = document.getElementById('enterScreen');
        var mainApp = document.getElementById('mainApp');
        var volumeCtrl = document.getElementById('volumeControl');

        if (!enterScreen) return;

        // If already entered this session, skip enter screen
        if (sessionStorage.getItem('sabdash_entered') === '1') {
            hasEntered = true;
            enterScreen.classList.add('hidden');
            if (mainApp) mainApp.classList.add('visible');
            if (volumeCtrl) volumeCtrl.classList.add('visible');
            startFloatingCmds();
            return;
        }

        // Spawn enter screen particles
        spawnEnterParticles();

        // Click anywhere on enter screen to enter
        enterScreen.addEventListener('click', handleEnter);
    }

    function spawnEnterParticles() {
        var container = document.getElementById('enterParticles');
        if (!container) return;
        for (var i = 0; i < 30; i++) {
            var p = document.createElement('div');
            p.className = 'enter-particle';
            p.style.left = (Math.random() * 100) + '%';
            p.style.animationDuration = (6 + Math.random() * 10) + 's';
            p.style.animationDelay = (Math.random() * 8) + 's';
            container.appendChild(p);
        }
    }

    /* =========================================================
       Floating Command Background (#hackerBg)
       Green matrix-style command lines drifting upward
       ========================================================= */
    var cmdLines = [
        '> git status --porcelain', '> docker compose up -d', '> ssh -i key user@host',
        '> systemctl restart nginx', '> python manage.py migrate', '> npm run build',
        '> grep -r "error" /var/log/', '> curl -s localhost:8080/health', '> ls -la /etc/',
        '> chmod 600 ~/.ssh/id_rsa', '> journalctl -u myapp -f', '> rsync -avz src/ dest/',
        '> openssl req -x509 -nodes', '> iptables -L -n', '> df -h | grep /dev/sda',
        '> tar czf backup.tar.gz ./', '> find . -name "*.log"', '> ufw allow 443/tcp',
        '> redis-cli ping', '> pg_dump dbname > db.sql', '> htop --sort-key PERCENT_MEM',
        '> tmux new -s work', '> nmap -sV 192.168.1.0/24', '> dig +short example.com',
        '> ansible-playbook deploy.yml', '> kubectl get pods -A', '> terraform plan',
        '> SELECT * FROM users LIMIT 10;', '> ffmpeg -i in.mp4 out.webm',
        '> cat /proc/cpuinfo | head', '> free -h', '> ss -tlnp',
        '> podman exec -it app sh', '> certbot renew --dry-run', '> lsblk',
        '> sysctl --system', '> adduser --system myapp', '> logrotate -f /etc/logrotate.conf',
        '> mount -o noatime /dev/sdb1 /mnt', '> crontab -l', '> ethtool eth0',
        '> ping -c 4 8.8.8.8', '> traceroute google.com', '> strace -p 1234',
        '> perf top', '> lsof -i :80', '> ip route show',
        '$ [p]set Sablinova 2b Bot', '$ [p]help moderation', '$ [p]cleanup messages 100',
        '$ [p]ban @user spamming', '$ [p]mute @user 30m', '$ [p]warn @user language',
        '$ [p]set showsettings', '$ [p]playlist start favorites', '$ [p]trivia start',
        '$ [p]bank balance', '$ [p]credits transfer @user 500', '$ [p]userinfo @user',
        '$ [p]serverinfo', '$ [p]tag create faq FAQ answer', '$ [p]reactrole add',
        '$ [p]levelset channel #general', '$ [p]customcom add hello Hi there!',
        '$ [p]roletools sticky @role', '$ [p]filter add badword', '$ [p]set prefix !',
        '$ [p]embedset show welcome', '$ [p]automod rules', '$ [p]cog install',
        '> while true; do echo "alive"; sleep 60; done',
        '> watch -n 1 "ss -s"', '> nc -zv host 22', '> ab -n 1000 -c 10 http://localhost/',
        '> git log --oneline --graph -20', '> docker stats --no-stream',
        '> jq ".data.results" api.json', '> sed -i "s/old/new/g" config.yml',
        '> awk "{print $1}" access.log | sort | uniq -c | sort -rn | head',
        '> fail2ban-client status sshd', '> crowdsec metrics',
        '> restic backup /srv/data', '> rclone sync /local remote:bucket',
        '> wireguard-tools genkey', '> tailscale status',
        '> vault kv get secret/api', '> consul members',
        '> prometheus --config.file=prom.yml', '> grafana-cli plugins ls',
        '> envsubst < template.yml > out.yml', '> age -e -r pubkey file.tar.gz',
        '> zstd -19 database.sql', '> btrfs subvolume snapshot / /snap',
        '> caddy reverse-proxy --from :443 --to :8080'
    ];

    var floatInterval = null;

    function spawnFloatCmd() {
        var bg = document.getElementById('hackerBg');
        if (!bg) return;

        var div = document.createElement('div');
        div.className = 'float-cmd';
        div.textContent = cmdLines[Math.floor(Math.random() * cmdLines.length)];
        div.style.left = (Math.random() * 85) + '%';
        div.style.bottom = '-20px';
        div.style.animationDuration = (8 + Math.random() * 6) + 's';
        bg.appendChild(div);

        // Remove after animation
        setTimeout(function() { div.remove(); }, 15000);
    }

    function startFloatingCmds() {
        if (floatInterval) return;
        // Initial burst
        for (var i = 0; i < 15; i++) {
            setTimeout(spawnFloatCmd, i * 80);
        }
        floatInterval = setInterval(spawnFloatCmd, 400);
    }

    /* =========================================================
       Collapsible Cog Blocks
       ========================================================= */
    window.toggleCog = function(btn) {
        var expanded = btn.getAttribute('aria-expanded') === 'true';
        var body = btn.nextElementSibling;
        if (!body) return;

        if (expanded) {
            btn.setAttribute('aria-expanded', 'false');
            body.classList.remove('open');
        } else {
            btn.setAttribute('aria-expanded', 'true');
            body.classList.add('open');
        }
    };

    window.toggleAll = function(expand) {
        var heads = document.querySelectorAll('.cog-head');
        heads.forEach(function(btn) {
            var body = btn.nextElementSibling;
            if (!body) return;
            if (expand) {
                btn.setAttribute('aria-expanded', 'true');
                body.classList.add('open');
            } else {
                btn.setAttribute('aria-expanded', 'false');
                body.classList.remove('open');
            }
        });
    };

    /* =========================================================
       Command Search with Meta Text
       ========================================================= */
    function initSearch() {
        var input = document.getElementById('search');
        var meta = document.getElementById('searchMeta');
        var noResults = document.getElementById('noResults');
        if (!input) return;

        // Count total commands
        var allRows = document.querySelectorAll('.cmd-table tbody tr');
        var totalCmds = allRows.length;

        input.addEventListener('input', function() {
            var q = this.value.toLowerCase().trim();
            var matchCount = 0;

            var categories = document.querySelectorAll('.category');
            categories.forEach(function(cat) {
                var catVisible = false;
                var cogs = cat.querySelectorAll('.cog');

                cogs.forEach(function(cog) {
                    var cogName = (cog.getAttribute('data-cog') || '').toLowerCase();
                    var rows = cog.querySelectorAll('.cmd-table tbody tr');
                    var cogVisible = false;

                    rows.forEach(function(row) {
                        var cmdName = (row.getAttribute('data-cmd') || '').toLowerCase();
                        var descCell = row.querySelector('.desc-cell');
                        var desc = descCell ? descCell.textContent.toLowerCase() : '';

                        if (!q || cmdName.indexOf(q) !== -1 || desc.indexOf(q) !== -1 || cogName.indexOf(q) !== -1) {
                            row.classList.remove('hidden');
                            matchCount++;
                            cogVisible = true;
                        } else {
                            row.classList.add('hidden');
                        }
                    });

                    if (cogVisible || !q) {
                        cog.classList.remove('hidden');
                        catVisible = true;
                        // Auto-expand matching cogs when searching
                        if (q) {
                            var head = cog.querySelector('.cog-head');
                            var body = cog.querySelector('.cog-body');
                            if (head && body) {
                                head.setAttribute('aria-expanded', 'true');
                                body.classList.add('open');
                            }
                        }
                    } else {
                        cog.classList.add('hidden');
                    }
                });

                if (catVisible || !q) {
                    cat.classList.remove('hidden');
                } else {
                    cat.classList.add('hidden');
                }
            });

            // Update meta text
            if (meta) {
                if (q) {
                    meta.textContent = matchCount + ' of ' + totalCmds + ' commands';
                } else {
                    meta.textContent = '';
                    // Collapse all when clearing search
                    toggleAll(false);
                }
            }

            // No results message
            if (noResults) {
                if (q && matchCount === 0) {
                    noResults.classList.add('visible');
                } else {
                    noResults.classList.remove('visible');
                }
            }
        });
    }

    /* =========================================================
       Scroll-to-Top Button
       ========================================================= */
    function initScrollTop() {
        var btn = document.getElementById('scrollTop');
        if (!btn) return;

        window.addEventListener('scroll', function() {
            if (window.scrollY > 500) {
                btn.classList.add('show');
            } else {
                btn.classList.remove('show');
            }
        });
    }

    /* =========================================================
       Volume Control
       ========================================================= */
    function initVolumeControl() {
        var slider = document.getElementById('volumeSlider');
        var icon = document.getElementById('volumeIcon');
        var pct = document.getElementById('volumePct');
        var bgMusic = document.getElementById('bgMusic');
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
            if (bgMusic) bgMusic.volume = val / 100;
        }

        slider.addEventListener('input', function() {
            var val = parseInt(this.value);
            updateIcon(val);
            muted = val === 0;
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

    /* =========================================================
       Nav Hamburger Toggle (mobile)
       ========================================================= */
    function initNavToggle() {
        var toggle = document.getElementById('navToggle');
        var links = document.getElementById('navLinks');
        if (!toggle || !links) return;

        toggle.addEventListener('click', function() {
            links.classList.toggle('open');
        });

        // Close nav when clicking a link (mobile)
        links.querySelectorAll('a').forEach(function(a) {
            a.addEventListener('click', function() {
                links.classList.remove('open');
            });
        });
    }

    /* =========================================================
       Flash Message Auto-Dismiss
       ========================================================= */
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

    /* =========================================================
       Keyboard Shortcuts
       ========================================================= */
    function initKeyboard() {
        document.addEventListener('keydown', function(e) {
            // "/" focuses search (if not already in an input)
            if (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
                e.preventDefault();
                var search = document.getElementById('search');
                if (search) search.focus();
            }
            // Escape blurs search
            if (e.key === 'Escape') {
                var search = document.getElementById('search');
                if (search && document.activeElement === search) {
                    search.blur();
                }
            }
        });
    }

    /* =========================================================
       Hover Sound Effect (subtle)
       ========================================================= */
    function playHoverSfx() {
        try {
            var ctx = getAudioCtx();
            var osc = ctx.createOscillator();
            var gain = ctx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(800, ctx.currentTime);
            osc.frequency.exponentialRampToValueAtTime(1200, ctx.currentTime + 0.06);
            gain.gain.setValueAtTime(0.05, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.10);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start(ctx.currentTime);
            osc.stop(ctx.currentTime + 0.10);
        } catch(e) {}
    }

    function initHoverSounds() {
        var els = document.querySelectorAll('.quick-card, .toc-card, .stat-box');
        els.forEach(function(el) {
            el.addEventListener('mouseenter', playHoverSfx);
        });
    }

    /* =========================================================
       Init
       ========================================================= */
    document.addEventListener('DOMContentLoaded', function() {
        initEnterScreen();
        initScrollTop();
        initVolumeControl();
        initNavToggle();
        initFlashDismiss();
        initKeyboard();
        initSearch();
        initHoverSounds();
    });

})();
