/**
 * AI Resume Analyzer & ATS Optimizer - Frontend Controller
 * Handles drag-and-drop file uploads, preset job descriptions,
 * API communication, and dynamic metric visualizations.
 */

let selectedFile = null;
let activeTab = 'upload';
let cachedPresets = null;

// Initialize dropzone and presets on page load
document.addEventListener('DOMContentLoaded', () => {
  setupDropzone();
  fetchPresets();

  // Word count listeners
  const jdInput = document.getElementById('jd-text-input');
  jdInput.addEventListener('input', updateJdWordCount);
});

/**
 * Setup drag and drop events for the PDF upload area
 */
function setupDropzone() {
  const dropzone = document.getElementById('dropzone');

  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add('dragover');
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('dragover');
    }, false);
  });

  dropzone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0) {
      processSelectedFile(files[0]);
    }
  }, false);
}

/**
 * Handles file selected via system file dialog
 */
function handleFileSelected(event) {
  const file = event.target.files[0];
  if (file) {
    processSelectedFile(file);
  }
}

function processSelectedFile(file) {
  const validExts = ['.pdf', '.txt'];
  const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();

  if (!validExts.includes(ext)) {
    alert('Please select a valid PDF (.pdf) or Plain Text (.txt) file.');
    return;
  }

  selectedFile = file;
  document.getElementById('file-name-display').textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
  document.getElementById('selected-file-badge').style.display = 'flex';
  document.getElementById('resume-status-hint').textContent = 'File attached ready for ATS audit';
}

function clearSelectedFile(event) {
  if (event) event.stopPropagation();
  selectedFile = null;
  document.getElementById('file-input').value = '';
  document.getElementById('selected-file-badge').style.display = 'none';
  document.getElementById('resume-status-hint').textContent = 'No file selected';
}

/**
 * Switch tabs between PDF Upload and Direct Text Input
 */
function switchResumeTab(tab) {
  activeTab = tab;
  const btnUpload = document.getElementById('tab-upload');
  const btnText = document.getElementById('tab-text');
  const viewUpload = document.getElementById('view-upload');
  const viewText = document.getElementById('view-text');

  if (tab === 'upload') {
    btnUpload.classList.add('active');
    btnText.classList.remove('active');
    viewUpload.classList.add('active');
    viewText.classList.remove('active');
  } else {
    btnText.classList.add('active');
    btnUpload.classList.remove('active');
    viewText.classList.add('active');
    viewUpload.classList.remove('active');
  }
}

/**
 * Fetches preset job descriptions from backend
 */
async function fetchPresets() {
  try {
    const res = await fetch('/api/presets');
    if (res.ok) {
      cachedPresets = await res.json();
    }
  } catch (err) {
    console.warn('Using offline preset fallbacks:', err);
  }
}

/**
 * Loads a selected job preset into the JD textarea
 */
function loadJobPreset(presetKey) {
  if (cachedPresets && cachedPresets[presetKey]) {
    document.getElementById('jd-text-input').value = cachedPresets[presetKey].description;
  } else {
    // Standard offline fallback
    if (presetKey === 'aiml_intern') {
      document.getElementById('jd-text-input').value = `Job Title: AI/ML Engineering Intern
Requirements:
- Strong programming proficiency in Python and Object-Oriented Programming (OOP).
- Experience with Machine Learning & Deep Learning: PyTorch, Scikit-Learn, TensorFlow.
- Computer Vision (OpenCV) or Natural Language Processing (NLP).
- Libraries: Pandas, NumPy, Matplotlib.
- Building REST APIs using FastAPI or Flask.
- Foundational Data Structures, Algorithms, Docker, and Git.`;
    }
  }
  updateJdWordCount();
}

function clearJobDescription() {
  document.getElementById('jd-text-input').value = '';
  updateJdWordCount();
}

function updateJdWordCount() {
  const text = document.getElementById('jd-text-input').value.trim();
  const count = text ? text.split(/\s+/).length : 0;
  document.getElementById('jd-word-count').textContent = `${count} words`;
}

/**
 * Loads a realistic sample student resume for 1-click live demo
 */
async function loadSampleResume() {
  try {
    const res = await fetch('/api/sample-resume');
    if (res.ok) {
      const data = await res.json();
      switchResumeTab('text');
      document.getElementById('resume-text-input').value = data.text;
      document.getElementById('resume-status-hint').textContent = 'Sample student resume loaded';
    }
  } catch (err) {
    console.warn('Fallback loading sample resume:', err);
  }
}

/**
 * Main Analysis Trigger
 */
async function runAnalysis() {
  const jdText = document.getElementById('jd-text-input').value.trim();
  const resumeText = document.getElementById('resume-text-input').value.trim();

  if (!jdText || jdText.length < 30) {
    alert('Please paste or select a target Job Description (at least 30 characters).');
    return;
  }

  const formData = new FormData();
  formData.append('job_description', jdText);

  if (activeTab === 'upload') {
    if (!selectedFile) {
      alert('Please select or drag-and-drop a resume PDF file, or switch to the Direct Text tab.');
      return;
    }
    formData.append('resume_file', selectedFile);
  } else {
    if (!resumeText || resumeText.length < 30) {
      alert('Please paste your resume text (at least 30 characters) or click "Load Sample Student Resume".');
      return;
    }
    formData.append('resume_text', resumeText);
  }

  // Set loading state
  const btn = document.getElementById('analyze-btn');
  const spinner = document.getElementById('btn-spinner');
  btn.disabled = true;
  spinner.style.display = 'block';

  try {
    const response = await fetch('/api/analyze', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Analysis failed' }));
      throw new Error(errorData.detail || 'Failed to analyze resume');
    }

    const data = await response.json();
    renderResults(data);
  } catch (error) {
    alert(`Error during analysis: ${error.message}`);
  } finally {
    btn.disabled = false;
    spinner.style.display = 'none';
  }
}

/**
 * Renders all analysis data into the visual dashboard
 */
function renderResults(data) {
  const resultsSection = document.getElementById('results-section');
  resultsSection.style.display = 'flex';

  // Scroll smoothly to results
  resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

  // 1. Overall Score & Dial
  const overallScore = Math.round(data.overall_score);
  document.getElementById('overall-score-display').textContent = overallScore;

  const scoreCircle = document.getElementById('score-circle');
  let colorVar = 'var(--accent-emerald)';
  if (overallScore < 60) colorVar = 'var(--accent-red)';
  else if (overallScore < 75) colorVar = 'var(--accent-amber)';

  const deg = (overallScore / 100) * 360;
  scoreCircle.style.background = `conic-gradient(${colorVar} ${deg}deg, rgba(255,255,255,0.05) ${deg}deg)`;
  scoreCircle.style.boxShadow = `0 0 25px ${colorVar}`;

  // Verdict
  document.getElementById('verdict-display').textContent = data.verdict;
  let verdictDesc = 'Candidate demonstrates strong alignment with technical requirements.';
  if (overallScore < 60) verdictDesc = 'Significant skill gaps or structural formatting issues detected. Follow checklist below to optimize.';
  else if (overallScore < 75) verdictDesc = 'Solid foundation. Adding target keywords and quantifying impact will boost your ATS ranking.';
  document.getElementById('verdict-description').textContent = verdictDesc;

  // 2. Candidate Quick Stats
  document.getElementById('meta-email').textContent = data.contacts.email || 'Not detected ⚠️';
  document.getElementById('meta-phone').textContent = data.contacts.phone || 'Not detected ⚠️';
  document.getElementById('meta-words').textContent = `${data.word_count} words`;
  document.getElementById('meta-verbs').textContent = `${data.impact_details.action_verb_count} distinct power verbs`;

  // 3. 5-Pillar Breakdown Bars
  const comp = data.component_scores;
  setBar('pillar-skills', comp.skill_match);
  setBar('pillar-semantic', comp.semantic_similarity);
  setBar('pillar-sections', comp.section_completeness);
  setBar('pillar-impact', comp.impact_and_metrics);
  setBar('pillar-format', comp.formatting_and_length);

  // 4. Skills Matrix
  const matchedContainer = document.getElementById('matched-skills-container');
  const missingContainer = document.getElementById('missing-skills-container');

  matchedContainer.innerHTML = '';
  missingContainer.innerHTML = '';

  const matchedList = data.skills.matched || [];
  const missingList = data.skills.missing || [];

  document.getElementById('matched-skills-count').textContent = matchedList.length;
  document.getElementById('missing-skills-count').textContent = missingList.length;

  if (matchedList.length === 0) {
    matchedContainer.innerHTML = '<span class="text-hint">No direct target skills matched yet.</span>';
  } else {
    matchedList.forEach(skill => {
      const tag = document.createElement('span');
      tag.className = 'tag-badge tag-matched';
      tag.innerHTML = `✓ ${skill}`;
      matchedContainer.appendChild(tag);
    });
  }

  if (missingList.length === 0) {
    missingContainer.innerHTML = '<span class="text-hint" style="color: var(--accent-emerald);">All target skills from the job description are present!</span>';
  } else {
    missingList.forEach(skill => {
      const tag = document.createElement('span');
      tag.className = 'tag-badge tag-missing';
      tag.innerHTML = `+ ${skill}`;
      missingContainer.appendChild(tag);
    });
  }

  // 5. Recommendations Checklist
  const recsContainer = document.getElementById('recommendations-container');
  recsContainer.innerHTML = '';

  const recs = data.recommendations || [];
  if (recs.length === 0) {
    recsContainer.innerHTML = '<p class="text-hint">No critical issues detected. Your resume conforms excellently to ATS screening standards.</p>';
  } else {
    recs.forEach(rec => {
      const item = document.createElement('div');
      let pClass = 'rec-low';
      let bClass = 'badge-low';
      if (rec.priority === 'HIGH') {
        pClass = 'rec-high';
        bClass = 'badge-high';
      } else if (rec.priority === 'MEDIUM') {
        pClass = 'rec-medium';
        bClass = 'badge-med';
      }

      item.className = `rec-item ${pClass}`;
      item.innerHTML = `
        <div class="rec-header-row">
          <span class="rec-category">${rec.category}</span>
          <span class="rec-priority-badge ${bClass}">${rec.priority} PRIORITY</span>
        </div>
        <div class="rec-text">${rec.message}</div>
      `;
      recsContainer.appendChild(item);
    });
  }
}

function setBar(idPrefix, val) {
  const rounded = Math.round(val);
  const bar = document.getElementById(`${idPrefix}-bar`);
  const label = document.getElementById(`${idPrefix}-val`);
  if (bar && label) {
    label.textContent = `${rounded}%`;
    bar.style.width = `${Math.min(100, Math.max(0, rounded))}%`;
  }
}
