import re

with open('sky/admin.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Login
old_login = """    if (!valid) { shakeForm('loginForm'); return; }

    showToast('Login successful! Redirecting...');
    setTimeout(() => showDashboard(email), 1200);
    generateCaptcha('login');"""
new_login = """    if (!valid) { shakeForm('loginForm'); return; }
    const remember = document.getElementById('loginRemember') ? document.getElementById('loginRemember').checked : false;
    fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email, password: password, remember_me: remember })
    }).then(res => res.json()).then(data => {
        if (data.error) {
            showError('loginEmailErr', data.error);
            shakeForm('loginForm');
            generateCaptcha('login');
        } else {
            showToast('Login successful! Redirecting...');
            setTimeout(() => { showDashboard(data.email || email); loadOpportunities(); }, 1200);
            generateCaptcha('login');
        }
    });"""
content = content.replace(old_login, new_login)

# 2. Signup
old_signup = """    if (!valid) { shakeForm('signupForm'); return; }
    showToast('Account created successfully!');
    generateCaptcha('signup');
    this.reset(); checkStrength('');
    setTimeout(() => showPage('loginPage'), 1500);"""
new_signup = """    if (!valid) { shakeForm('signupForm'); return; }
    fetch('/api/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ full_name: name, email: email, password: password, confirm_password: confirmPassword })
    }).then(res => res.json()).then(data => {
        if (data.error) {
            showError('signupEmailErr', data.error);
            shakeForm('signupForm');
            generateCaptcha('signup');
        } else {
            showToast('Account created successfully!');
            generateCaptcha('signup');
            document.getElementById('signupForm').reset();
            checkStrength('');
            setTimeout(() => showPage('loginPage'), 1500);
        }
    });"""
content = content.replace(old_signup, new_signup)

# 3. Forgot
old_forgot = """    if (!valid) { shakeForm('forgotForm'); return; }
    showToast('Reset link sent to your email!');
    generateCaptcha('forgot');
    this.reset();"""
new_forgot = """    if (!valid) { shakeForm('forgotForm'); return; }
    fetch('/api/forgot_password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email })
    }).then(res => res.json()).then(data => {
        showToast('Reset link sent to your email!');
        generateCaptcha('forgot');
        document.getElementById('forgotForm').reset();
    });"""
content = content.replace(old_forgot, new_forgot)

# 4. Logout
old_logout = """function handleLogout() {
    document.getElementById('dashboardWrapper').classList.remove('active');
    document.getElementById('authWrapper').style.display = 'flex';
    document.body.style.alignItems = '';
    showToast('Signed out successfully');
    showPage('loginPage');
}"""
new_logout = """function handleLogout() {
    fetch('/api/logout', { method: 'POST' }).then(() => {
        document.getElementById('dashboardWrapper').classList.remove('active');
        document.getElementById('authWrapper').style.display = 'flex';
        document.body.style.alignItems = '';
        showToast('Signed out successfully');
        showPage('loginPage');
        document.querySelector('.opportunities-grid').innerHTML = '';
    });
}"""
content = content.replace(old_logout, new_logout)

# 5. Opportunity Management Block
opp_block_start = "document.getElementById('opportunityForm').addEventListener('submit', function(e) {"
opp_block_end = "            this.reset();\n        });"

# Extract everything between these
pattern = re.compile(re.escape(opp_block_start) + r'.*?' + re.escape(opp_block_end), re.DOTALL)

new_opp_block = """let editingOpportunityId = null;

function renderOpportunity(opp) {
    const card = document.createElement('div');
    card.className = 'opportunity-card';
    card.dataset.id = opp.id;

    const skills = opp.skills ? opp.skills.split(',').map(s => s.trim()).filter(Boolean) : [];
    
    const headerHtml = `
        <div class="opportunity-card-header">
            <h5>${escapeHtml(opp.name)}</h5>
            <div class="opportunity-meta">
                <span><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>${escapeHtml(opp.duration)}</span>
                <span><svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>${escapeHtml(opp.start_date)}</span>
            </div>
        </div>
        <p class="opportunity-description">${escapeHtml(opp.description)}</p>
    `;

    const skillsHtml = `<div class="opportunity-skills"><div class="opportunity-skills-label">Skills You'll Gain</div><div class="skills-tags">
        ${skills.map(s => `<span class="skill-tag">${escapeHtml(s)}</span>`).join('')}
    </div></div>`;

    const applicantsCount = opp.max_applicants ? `${parseInt(opp.max_applicants, 10)} applicants` : '0 applicants';
    const footerHtml = `
        <div class="opportunity-footer">
            <span class="applicants-count">${escapeHtml(applicantsCount)}</span>
            <div style="display:flex;gap:8px;">
                <button class="view-course-btn" style="width: auto; padding: 8px; background:transparent; border:1px solid var(--qf-primary); color:var(--qf-primary);" onclick='editOpportunity(${JSON.stringify(opp).replace(/'/g, "&#39;")})'>Edit</button>
                <button class="view-course-btn" style="width: auto; padding: 8px; background:transparent; border:1px solid #d32f2f; color:#d32f2f;" onclick="deleteOpportunity(${opp.id})">Delete</button>
                <button class="view-course-btn view-details-btn" style="width: auto; padding: 8px 16px;">View Details</button>
            </div>
        </div>
    `;

    card.innerHTML = headerHtml + skillsHtml + footerHtml;

    const viewBtn = card.querySelector('.view-details-btn');
    viewBtn.addEventListener('click', function() {
        openOpportunityDetails(opp.name, {
            duration: opp.duration,
            startDate: opp.start_date,
            description: opp.description,
            skills: skills,
            applicants: opp.max_applicants ? parseInt(opp.max_applicants, 10) : 0,
            futureOpportunities: opp.future_opportunities,
            prerequisites: ''
        });
    });

    return card;
}

function loadOpportunities() {
    fetch('/api/opportunities').then(res => res.json()).then(data => {
        const grid = document.querySelector('.opportunities-grid');
        const emptyState = document.getElementById('emptyOpportunitiesState');
        
        // Remove all existing cards
        document.querySelectorAll('.opportunity-card').forEach(c => c.remove());
        
        if (data.length === 0) {
            if (emptyState) emptyState.style.display = 'block';
        } else {
            if (emptyState) emptyState.style.display = 'none';
            data.forEach(opp => {
                grid.appendChild(renderOpportunity(opp));
            });
        }
    });
}

window.deleteOpportunity = function(id) {
    if (confirm('Are you sure you want to delete this opportunity?')) {
        fetch('/api/opportunities/' + id, { method: 'DELETE' }).then(res => res.json()).then(data => {
            if (data.success) {
                showToast('Opportunity deleted.');
                const card = document.querySelector('.opportunity-card[data-id="'+id+'"]');
                if (card) card.remove();
                if (document.querySelectorAll('.opportunity-card').length === 0) {
                    const emptyState = document.getElementById('emptyOpportunitiesState');
                    if (emptyState) emptyState.style.display = 'block';
                }
            }
        });
    }
};

window.editOpportunity = function(opp) {
    editingOpportunityId = opp.id;
    document.getElementById('oppName').value = opp.name;
    document.getElementById('oppDuration').value = opp.duration;
    document.getElementById('oppStartDate').value = opp.start_date;
    document.getElementById('oppDescription').value = opp.description;
    document.getElementById('oppSkills').value = opp.skills;
    document.getElementById('oppCategory').value = opp.category;
    document.getElementById('oppFuture').value = opp.future_opportunities;
    document.getElementById('oppMaxApplicants').value = opp.max_applicants || '';
    
    openOpportunityModal();
};

document.getElementById('opportunityForm').addEventListener('submit', function(e) {
    e.preventDefault();

    const payload = {
        name: document.getElementById('oppName').value.trim(),
        duration: document.getElementById('oppDuration').value.trim(),
        start_date: document.getElementById('oppStartDate').value,
        description: document.getElementById('oppDescription').value.trim(),
        skills: document.getElementById('oppSkills').value.trim(),
        category: document.getElementById('oppCategory').value,
        future_opportunities: document.getElementById('oppFuture').value.trim(),
        max_applicants: document.getElementById('oppMaxApplicants').value.trim()
    };

    if (!payload.name || !payload.duration || !payload.start_date || !payload.description || !payload.skills || !payload.category || !payload.future_opportunities) {
        showToast('Please fill all required fields');
        return;
    }

    if (editingOpportunityId) {
        fetch('/api/opportunities/' + editingOpportunityId, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        }).then(res => res.json()).then(data => {
            if (data.success) {
                showToast('Opportunity updated successfully!');
                closeOpportunityModal();
                this.reset();
                editingOpportunityId = null;
                loadOpportunities();
            } else {
                showToast(data.error || 'Update failed');
            }
        });
    } else {
        fetch('/api/opportunities', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        }).then(res => res.json()).then(data => {
            if (data.success) {
                showToast('Opportunity created successfully!');
                closeOpportunityModal();
                this.reset();
                loadOpportunities();
            } else {
                showToast(data.error || 'Creation failed');
            }
        });
    }
});

// Session check on load
document.addEventListener('DOMContentLoaded', () => {
    fetch('/api/check_session').then(res => res.json()).then(data => {
        if (data.logged_in) {
            showDashboard(data.email);
            loadOpportunities();
        }
    });
});"""

content = pattern.sub(new_opp_block, content)

with open('sky/admin.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patching complete!")
