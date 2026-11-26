/* ==========================================================================
   Table of contents
     1. Conversation data (edit this to change the sample chats)
     2. Small helpers
     3. Avatars
     4. Rendering a conversation
     5. Switching conversations
     6. Sending messages and the typing indicator
     7. Report Message popup
     8. New Chat popup
     9. Toast
    10. Start
   ========================================================================== */
(function () {
  'use strict';

  /* ======================================================================
     1. CONVERSATION DATA
     ====================================================================== */
  var conversationData = {
    '235': {
      name: 'Anonymous 235',
      messages: [
        { from: 'them', text: 'Hi there, how has your week been going so far?' },
        { from: 'me', text: "Pretty rough, but I'm trying to take it one day at a time." },
        { from: 'them', text: "That's completely okay. Do you want to talk about what's been weighing on you?" }
      ]
    },
    '359': {
      name: 'Anonymous 359',
      messages: [
        { from: 'them', text: 'Hey! I saw your post in the support group.' },
        { from: 'me', text: 'Thanks for reaching out, it really means a lot.' }
      ]
    },
    '964': {
      name: 'Anonymous 964',
      messages: [
        { from: 'them', text: 'Have you tried the breathing exercise we talked about?' }
      ]
    },
    '179': {
      name: 'Anonymous 179',
      messages: [
        { from: 'me', text: 'Good morning! Just checking in.' },
        { from: 'them', text: 'Good morning! Doing a bit better today.' }
      ]
    }
  };

  var REPLIES = [
    'I hear you. Thank you for sharing that with me.',
    'That sounds really difficult. How are you feeling right now?',
    "I'm glad you told me. You're not alone in this.",
    'Take your time, I am here to listen.'
  ];

  var activeId = '235';
  var replyIndex = 0;
  var reportTarget = null;
  var typingTimer = null;

  /* ======================================================================
     2. SMALL HELPERS
     ====================================================================== */
  function $(id) { return document.getElementById(id); }

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function openModal(node) { node.classList.add('is-open'); }
  function closeModal(node) { node.classList.remove('is-open'); }

  /* ======================================================================
     3. AVATARS 
     ====================================================================== */
  function letterFor(name) {
    var clean = String(name || '').replace(/^(dr|mr|mrs|ms)\.?\s+/i, '').trim();
    return clean ? clean.charAt(0).toUpperCase() : '';
  }

  function fillAvatars(root) {
    (root || document).querySelectorAll('[data-avatar-auto]').forEach(function (avatar) {
      var name = avatar.parentElement && avatar.parentElement.querySelector('.contact-name');
      avatar.textContent = letterFor(name ? name.textContent : '');
    });
    (root || document).querySelectorAll('[data-avatar-from]').forEach(function (avatar) {
      var source = $(avatar.getAttribute('data-avatar-from'));
      avatar.textContent = letterFor(source ? source.textContent : '');
    });
  }

  /* ======================================================================
     4. RENDERING A CONVERSATION
     ====================================================================== */
  function buildIncoming(conv, msg, index) {
    var row = el('div', 'message-incoming');
    var avatar = el('div', 'avatar avatar-sm', letterFor(conv.name));
    var body = el('div', 'message-body');
    body.appendChild(el('div', 'bubble-in', msg.text));

    var report = el('button', 'report-trigger-btn', '···');
    report.type = 'button';
    report.title = 'Report message';
    report.setAttribute('aria-label', 'Report message');
    report.setAttribute('data-message-index', String(index));
    body.appendChild(report);

    row.appendChild(avatar);
    row.appendChild(body);
    return row;
  }

  function buildOutgoing(msg) {
    var row = el('div', 'message-outgoing');
    var bubble = el('div', 'bubble-out');
    bubble.appendChild(el('span', '', msg.text));
    bubble.appendChild(el('span', 'message-read-mark', '✓✓'));
    row.appendChild(bubble);
    return row;
  }

  function buildFlagged(reason) {
    var row = el('div', 'flagged-row');
    var banner = el('div', 'flagged-banner');
    banner.appendChild(el('div', 'flagged-title', 'Message reported for review'));
    if (reason) banner.appendChild(el('div', 'flagged-quote', '"' + reason + '"'));
    row.appendChild(banner);
    return row;
  }

  function renderConversation(animateLast) {
    var box = $('chat-messages-box');
    var conv = conversationData[activeId];
    box.textContent = '';

    var divider = el('div', 'message-divider');
    divider.appendChild(el('div', 'message-divider-line'));
    divider.appendChild(el('span', 'message-divider-label', 'Today'));
    box.appendChild(divider);

    conv.messages.forEach(function (msg, index) {
      var node = msg.from === 'me' ? buildOutgoing(msg) : buildIncoming(conv, msg, index);
      if (animateLast && index === conv.messages.length - 1) node.classList.add('message-animate');
      box.appendChild(node);
      if (msg.flagged) box.appendChild(buildFlagged(msg.flagged));
    });

    box.scrollTop = box.scrollHeight;
  }

  /* ======================================================================
     5. SWITCHING CONVERSATIONS
     ====================================================================== */
  function hideTyping() {
    clearTimeout(typingTimer);
    $('typing-indicator').classList.remove('is-visible');
  }

  function openConversation(id) {
    if (!conversationData[id]) return;
    activeId = id;
    hideTyping();

    document.querySelectorAll('.contact-pill').forEach(function (pill) {
      pill.classList.toggle('is-active', pill.getAttribute('data-contact-id') === id);
    });

    var name = conversationData[id].name;
    $('active-chat-title').textContent = name;
    $('typing-author').textContent = name;
    fillAvatars($('typing-indicator'));
    renderConversation(false);
  }

  /* ======================================================================
     6. SENDING MESSAGES AND THE TYPING INDICATOR
     ====================================================================== */
  function showReply(id) {
    var conv = conversationData[id];
    $('typing-author').textContent = conv.name;
    fillAvatars($('typing-indicator'));
    $('typing-indicator').classList.add('is-visible');

    typingTimer = setTimeout(function () {
      $('typing-indicator').classList.remove('is-visible');
      conv.messages.push({ from: 'them', text: REPLIES[replyIndex % REPLIES.length] });
      replyIndex += 1;
      if (activeId === id) renderConversation(true);
    }, 1800);
  }

  function sendMessage(text) {
    var conv = conversationData[activeId];
    conv.messages.push({ from: 'me', text: text });
    renderConversation(true);
    hideTyping();
    showReply(activeId);
  }

  function setupSending() {
    $('chat-input-form').addEventListener('submit', function (event) {
      event.preventDefault();
      var input = $('chat-message-input');
      var text = input.value.trim();
      if (!text) return;
      input.value = '';
      sendMessage(text);
    });
  }

  /* ======================================================================
     7. REPORT MESSAGE POPUP
     ====================================================================== */
  function setupReport() {
    var modal = $('report-modal');

    $('chat-messages-box').addEventListener('click', function (event) {
      var button = event.target.closest('.report-trigger-btn');
      if (!button) return;
      var index = Number(button.getAttribute('data-message-index'));
      var msg = conversationData[activeId].messages[index];
      if (!msg || msg.flagged) return;

      reportTarget = { id: activeId, index: index };
      $('report-modal-msg-preview').textContent = '"' + msg.text + '"';
      $('report-reason-input').value = '';
      openModal(modal);
      $('report-reason-input').focus();
    });

    function close() { closeModal(modal); reportTarget = null; }
    $('modal-close-btn').addEventListener('click', close);
    $('modal-cancel-btn').addEventListener('click', close);
    modal.addEventListener('click', function (event) { if (event.target === modal) close(); });

    $('submit-report-btn').addEventListener('click', function () {
      if (!reportTarget) return;
      var reason = $('report-reason-input').value.trim() || 'No reason given';
      var msg = conversationData[reportTarget.id].messages[reportTarget.index];
      msg.flagged = reason;
      var shownId = reportTarget.id;
      close();
      if (shownId === activeId) renderConversation(false);
      showToast('Message reported successfully');
    });
  }

  /* ======================================================================
     8. NEW CHAT POPUP
     ====================================================================== */
  function setupNewChat() {
    var modal = $('new-chat-modal');
    var form = $('new-chat-form');

    function close() { closeModal(modal); form.reset(); }

    $('new-chat-btn').addEventListener('click', function () {
      openModal(modal);
      $('new-chat-input-name').focus();
    });
    $('new-chat-close-btn').addEventListener('click', close);
    $('new-chat-cancel-btn').addEventListener('click', close);
    modal.addEventListener('click', function (event) { if (event.target === modal) close(); });

    form.addEventListener('submit', function (event) {
      event.preventDefault();
      var name = $('new-chat-input-name').value.trim();
      var intro = $('new-chat-input-intro').value.trim();
      if (!name) return;

      var id = 'new-' + Date.now();
      conversationData[id] = { name: name, messages: intro ? [{ from: 'me', text: intro }] : [] };

      var pill = el('div', 'contact-pill');
      pill.setAttribute('data-contact-id', id);
      pill.appendChild(el('div', 'avatar avatar-sm', letterFor(name)));
      pill.appendChild(el('span', 'contact-name', name));
      var list = $('contacts-list-container');
      list.insertBefore(pill, list.firstChild);

      close();
      openConversation(id);
      if (intro) showReply(id);
      showToast('New conversation started');
    });
  }

  /* ======================================================================
     9. TOAST
     ====================================================================== */
  var toastTimer = null;
  function showToast(message) {
    var toast = $('toast-notification');
    $('toast-message').textContent = message;
    toast.classList.add('is-visible');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toast.classList.remove('is-visible'); }, 2600);
  }

  /* ======================================================================
     10. START
     ====================================================================== */
  document.addEventListener('DOMContentLoaded', function () {
    fillAvatars();

    $('contacts-list-container').addEventListener('click', function (event) {
      var pill = event.target.closest('.contact-pill');
      if (pill) openConversation(pill.getAttribute('data-contact-id'));
    });

    document.addEventListener('keydown', function (event) {
      if (event.key !== 'Escape') return;
      document.querySelectorAll('.modal-overlay.is-open').forEach(closeModal);
    });

    setupSending();
    setupReport();
    setupNewChat();
    openConversation(activeId);
  });
})();
