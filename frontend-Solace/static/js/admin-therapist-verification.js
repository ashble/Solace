/* ==========================================================================
   Solace - Therapist Verification page, admin
   (templates/admin-therapist-verification.html)

   Table of contents
     1. Therapist data (edit this to change the sample applications)
     2. Small helpers
     3. Status filters
     4. Review popup
     5. Document preview popup
     6. Approve and reject
     7. Closing popups
     8. Start
   ========================================================================== */
(function () {
  'use strict';

  /* ======================================================================
     1. THERAPIST DATA
     Each key matches a data-id on a table row in the HTML.
     ====================================================================== */
  var therapistsData = {
    1: { name: 'Dr. Zayne Li', role: 'Licensed Clinical Therapist', specialty: 'Anxiety · Depression', license: 'LIC-12345', experience: '6 Years', hours: '8:00 AM - 5:00 PM', status: 'Pending', certSpecialty: 'Psychiatry & Mental Health Counseling', licenseId: 'LIC-98421-MD' },
    2: { name: 'Dr. Clara Oswald', role: 'Licensed Trauma Therapist', specialty: 'Trauma & PTSD', license: 'LIC-23456', experience: '4 Years', hours: '9:00 AM - 6:00 PM', status: 'Pending', certSpecialty: 'Trauma & Stress Disorders', licenseId: 'LIC-77310-TR' },
    3: { name: 'Dr. Heinz Doofenshmirtz', role: 'Behavioral Therapist', specialty: 'Behavioral Therapy', license: 'LIC-34567', experience: '9 Years', hours: '10:00 AM - 7:00 PM', status: 'In Review', certSpecialty: 'Behavioral Therapy', licenseId: 'LIC-55672-BT' },
    4: { name: 'Dr. Meredith Grey', role: 'Clinical Psychiatrist', specialty: 'Clinical Psychiatry', license: 'LIC-45678', experience: '12 Years', hours: '8:00 AM - 4:00 PM', status: 'In Review', certSpecialty: 'Clinical Psychiatry', licenseId: 'LIC-40218-CP' },
    5: { name: 'Dr. Shaun Murphy', role: 'Youth Psychologist', specialty: 'Youth Psychology', license: 'LIC-56789', experience: '5 Years', hours: '9:00 AM - 5:00 PM', status: 'Approved', certSpecialty: 'Child & Adolescent Psychology', licenseId: 'LIC-61905-YP' },
    6: { name: 'Dr. Gregory House', role: 'Neuropsychologist', specialty: 'Diagnostics & Neuropsychology', license: 'LIC-67890', experience: '15 Years', hours: '11:00 AM - 7:00 PM', status: 'Approved', certSpecialty: 'Neuropsychology', licenseId: 'LIC-33847-NP' },
    7: { name: 'Dr. Hannibal Lecter', role: 'Forensic Psychologist', specialty: 'Forensic Psychology', license: 'LIC-78901', experience: '20 Years', hours: '6:00 PM - 12:00 AM', status: 'Rejected', rejectionReason: 'Credentials expired or unverified by board registrar.', certSpecialty: 'Forensic Psychology', licenseId: 'LIC-00001-FP' },
    8: { name: 'Dr. Walter White', role: 'Pharmacology Counselor', specialty: 'Substance Abuse & Pharmacology', license: 'LIC-89012', experience: '8 Years', hours: '7:00 AM - 3:00 PM', status: 'Rejected', rejectionReason: 'Submitted license number does not match state board records.', certSpecialty: 'Substance Abuse & Pharmacology', licenseId: 'LIC-00002-SP' }
  };

  // What each status shows in the table
  var STATUS_INFO = {
    'Pending':   { cssClass: 'status-pending',   verification: 'Ongoing',            action: 'Review',       isReview: true },
    'In Review': { cssClass: 'status-in-review', verification: 'Under Evaluation',   action: 'Review',       isReview: true },
    'Approved':  { cssClass: 'status-approved',  verification: 'Verified',           action: 'View Details', isReview: false },
    'Rejected':  { cssClass: 'status-rejected',  verification: 'Failed Verification', action: 'View Reason', isReview: false }
  };

  var DOCUMENTS = {
    license: { title: 'State Board Medical License', subtitle: 'Official Credential Verification Record', certName: 'Certificate of Professional Licensure', docId: 'DOC-VER-2025' },
    degree:  { title: 'Doctoral Degree Certification', subtitle: 'University Registry Record', certName: 'Doctor of Psychology Degree', docId: 'DOC-DEG-2025' }
  };

  var currentId = null;
  var currentFilter = 'all';

  /* ======================================================================
     2. SMALL HELPERS
     ====================================================================== */
  function $(id) { return document.getElementById(id); }

  function openModal(id) { $(id).classList.add('is-open'); }
  function closeModal(id) { $(id).classList.remove('is-open'); }

  function letterFor(name) {
    var clean = String(name || '').replace(/^(dr|mr|mrs|ms)\.?\s+/i, '').trim();
    return clean ? clean.charAt(0).toUpperCase() : '';
  }

  function rowFor(id) {
    return document.querySelector('.therapist-row[data-id="' + id + '"]');
  }

  function badgeHtml(status, large) {
    var span = document.createElement('span');
    span.className = 'status-badge ' + STATUS_INFO[status].cssClass + (large ? ' is-large' : '');
    span.textContent = status;
    return span;
  }

  function fillAvatars() {
    document.querySelectorAll('[data-avatar-auto]').forEach(function (avatar) {
      var name = avatar.parentElement.querySelector('span');
      avatar.textContent = letterFor(name ? name.textContent : '');
    });
    document.querySelectorAll('[data-avatar-from]').forEach(function (avatar) {
      var source = $(avatar.getAttribute('data-avatar-from'));
      avatar.textContent = letterFor(source ? source.textContent : '');
    });
  }

  /* ======================================================================
     3. STATUS FILTERS
     ====================================================================== */
  function applyFilter() {
    var rows = document.querySelectorAll('.therapist-row');
    var visible = 0;
    rows.forEach(function (row) {
      var show = currentFilter === 'all' || row.getAttribute('data-status') === currentFilter;
      row.classList.toggle('is-hidden', !show);
      if (show) visible += 1;
    });
    $('pagination-summary').textContent = visible === 0
      ? 'No users found'
      : 'Showing 1–' + visible + ' of ' + visible + ' users';
  }

  function setupFilters() {
    $('status-filter-group').addEventListener('click', function (event) {
      var pill = event.target.closest('.filter-pill');
      if (!pill) return;
      currentFilter = pill.getAttribute('data-filter');
      document.querySelectorAll('.filter-pill').forEach(function (other) {
        other.classList.toggle('is-active', other === pill);
      });
      applyFilter();
    });
  }

  /* ======================================================================
     4. REVIEW POPUP
     ====================================================================== */
  function openReviewModal(id) {
    var t = therapistsData[id];
    if (!t) return;
    currentId = id;

    $('modal-avatar').textContent = letterFor(t.name);
    $('modal-name').textContent = t.name;
    $('modal-role').textContent = t.role;
    $('modal-specialty').textContent = t.specialty;
    $('modal-license').textContent = t.license;
    $('modal-experience').textContent = t.experience;
    $('modal-hours').textContent = t.hours;

    var badgeBox = $('modal-status-badge');
    badgeBox.textContent = '';
    badgeBox.appendChild(badgeHtml(t.status, true));

    // Rejection reason is only shown for rejected applications
    var rejected = t.status === 'Rejected';
    $('modal-rejection-banner').classList.toggle('is-visible', rejected);
    if (rejected) $('modal-rejection-text').textContent = t.rejectionReason || 'No reason was recorded.';

    // Approve / Reject buttons are only for applications still waiting for a decision
    var decided = t.status === 'Approved' || t.status === 'Rejected';
    document.querySelector('#modal-action-bar .review-buttons').hidden = decided;
    $('modal-decision-state').textContent =
      t.status === 'Approved' ? 'Status: Verified' :
      t.status === 'Rejected' ? 'Status: Rejected' : 'Status: Under Review';

    openModal('reviewModalOverlay');
  }

  function setupReview() {
    $('therapist-table-body').addEventListener('click', function (event) {
      var button = event.target.closest('.row-action-button');
      if (!button) return;
      var row = button.closest('.therapist-row');
      openReviewModal(row.getAttribute('data-id'));
    });
  }

  /* ======================================================================
     5. DOCUMENT PREVIEW POPUP
     ====================================================================== */
  function setupPreview() {
    document.querySelectorAll('.preview-button').forEach(function (button) {
      button.addEventListener('click', function () {
        var doc = DOCUMENTS[button.getAttribute('data-doc-type')];
        var t = therapistsData[currentId];
        if (!doc || !t) return;

        $('preview-doc-title').textContent = doc.title;
        $('preview-doc-subtitle').textContent = doc.subtitle;
        $('preview-doc-certname').textContent = doc.certName;
        $('preview-doc-therapist').textContent = t.name;
        $('preview-doc-specialty').textContent = t.certSpecialty;
        $('preview-doc-license-id').textContent = t.licenseId;
        document.querySelector('.preview-footer-id').textContent = doc.docId;
        openModal('docPreviewModal');
      });
    });
  }

  /* ======================================================================
     6. APPROVE AND REJECT
     ====================================================================== */
  // Updates the data, the table row and the filters after a decision
  function setStatus(id, status) {
    var t = therapistsData[id];
    var info = STATUS_INFO[status];
    var row = rowFor(id);
    t.status = status;

    row.setAttribute('data-status', status);
    var badgeCell = row.querySelector('.status-badge-cell');
    badgeCell.textContent = '';
    badgeCell.appendChild(badgeHtml(status, false));
    row.querySelector('.verification-status-cell').textContent = info.verification;

    var button = row.querySelector('.row-action-button');
    button.textContent = info.action;
    button.classList.toggle('is-review', info.isReview);

    applyFilter();
  }

  function setupDecisions() {
    $('open-approve-btn').addEventListener('click', function () {
      $('approve-therapist-name').textContent = therapistsData[currentId].name;
      openModal('approveConfirmModal');
    });

    $('open-reject-btn').addEventListener('click', function () {
      $('reject-therapist-name').textContent = therapistsData[currentId].name;
      $('rejection-reason-input').value = '';
      openModal('rejectConfirmModal');
      $('rejection-reason-input').focus();
    });

    $('confirm-approve-btn').addEventListener('click', function () {
      setStatus(currentId, 'Approved');
      closeModal('approveConfirmModal');
      closeModal('reviewModalOverlay');
    });

    $('confirm-reject-btn').addEventListener('click', function () {
      var input = $('rejection-reason-input');
      var reason = input.value.trim();
      if (!reason) {                       // a reason is required
        input.setAttribute('aria-invalid', 'true');
        input.focus();
        return;
      }
      input.removeAttribute('aria-invalid');
      therapistsData[currentId].rejectionReason = reason;
      setStatus(currentId, 'Rejected');
      closeModal('rejectConfirmModal');
      closeModal('reviewModalOverlay');
    });

    $('rejection-reason-input').addEventListener('input', function () {
      this.removeAttribute('aria-invalid');
    });
  }

  /* ======================================================================
     7. CLOSING POPUPS - x buttons, clicking the dark background, Escape
     ====================================================================== */
  function setupClosing() {
    document.querySelectorAll('[data-close-modal]').forEach(function (button) {
      button.addEventListener('click', function () {
        closeModal(button.getAttribute('data-close-modal'));
      });
    });

    document.querySelectorAll('.modal-overlay').forEach(function (overlay) {
      overlay.addEventListener('click', function (event) {
        if (event.target === overlay) overlay.classList.remove('is-open');
      });
    });

    // Escape closes only the popup on top (highest in the stacking order)
    document.addEventListener('keydown', function (event) {
      if (event.key !== 'Escape') return;
      var order = ['docPreviewModal', 'approveConfirmModal', 'rejectConfirmModal', 'reviewModalOverlay'];
      for (var i = 0; i < order.length; i++) {
        if ($(order[i]).classList.contains('is-open')) { closeModal(order[i]); break; }
      }
    });
  }

  /* ======================================================================
     8. START
     ====================================================================== */
  document.addEventListener('DOMContentLoaded', function () {
    fillAvatars();
    setupFilters();
    setupReview();
    setupPreview();
    setupDecisions();
    setupClosing();
    applyFilter();
  });
})();
