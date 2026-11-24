// Render model text as text nodes; model output is never inserted as HTML.
window.MathJax = {tex: {inlineMath: [['\\(', '\\)'], ['$', '$']], displayMath: [['\\[', '\\]'], ['$$', '$$']]}, startup: {typeset: false}};
let latestAnswer = '';
let mathAvailable = false;
function plainMath(value) {
  return value.replace(/\\(?:text|mathrm)\{([^{}]*)\}/g, '$1')
    .replace(/\{,\}/g, ',').replace(/\\times/g, '×').replace(/\\cdot/g, '·')
    .replace(/\\%/g, '%').replace(/\\\s/g, ' ').replace(/\\([{}])/g, '$1');
}
function appendTextWithBold(container, value) {
  const pieces = value.split(/(\*\*[^*\n]+\*\*)/g);
  for (const part of pieces) {
    if (part.startsWith('**') && part.endsWith('**') && part.length > 4) {
      const strong = document.createElement('strong'); strong.textContent = part.slice(2, -2); container.appendChild(strong);
    } else container.appendChild(document.createTextNode(part));
  }
}
window.renderAnswer = function (text) {
  latestAnswer = String(text || '');
  const container = document.getElementById('answer');
  container.replaceChildren();
  // Keep math expressions intact when applying bold formatting to surrounding text.
  const parts = latestAnswer.split(/(\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\)|\$\$[\s\S]*?\$\$|\$(?!\s)[^$\n]+\$)/g);
  for (const part of parts) {
    const isMath = part.startsWith('\\(') || part.startsWith('\\[') || part.startsWith('$');
    if (isMath) {
      const span = document.createElement('span');
      if (mathAvailable) span.textContent = part;
      else {
        let inside = part.startsWith('$$') ? part.slice(2,-2) : part.startsWith('\\') ? part.slice(2,-2) : part.slice(1,-1);
        span.textContent = plainMath(inside);
      }
      container.appendChild(span);
    } else appendTextWithBold(container, part);
  }
  if (mathAvailable && window.MathJax.typesetPromise) window.MathJax.typesetPromise([container]).catch(() => { mathAvailable = false; window.renderAnswer(latestAnswer); });
};
window.mathRendererReady = function () {
  if (!window.MathJax || !window.MathJax.startup) return;
  window.MathJax.startup.promise.then(() => { mathAvailable = true; if (latestAnswer) window.renderAnswer(latestAnswer); }).catch(window.mathRendererUnavailable);
};
window.mathRendererUnavailable = function () { mathAvailable = false; if (latestAnswer) window.renderAnswer(latestAnswer); };
