// DOM Elements
const uploadArea = document.getElementById("uploadArea")
const fileInput = document.getElementById("documents")
const fileList = document.getElementById("fileList")
const temperatureSlider = document.getElementById("temperature")
const tempValue = document.getElementById("temp-value")
const submitBtn = document.getElementById("submitBtn")
const loadingOverlay = document.getElementById("loadingOverlay")
const questionInput = document.getElementById("question")
const configForm = document.querySelector(".config-form")
const voiceBtn = document.getElementById("voiceBtn")
const voiceStatus = document.getElementById("voiceStatus")
const chatHistorySidebar = document.getElementById("chatHistorySidebar")
const chatHistoryContent = document.getElementById("chatHistoryContent")

// File handling
const selectedFiles = []

// Voice recognition
let recognition = null
let isListening = false

// Chat history
let chatHistory = JSON.parse(localStorage.getItem("chatHistory") || "[]")

// Initialize
document.addEventListener("DOMContentLoaded", () => {
  initializeFileUpload()
  initializeTemperatureSlider()
  initializeFormSubmission()
  initializeKeyboardShortcuts()
  initializeVoiceRecognition()
  loadChatHistory()

  // Auto-hide flash messages
  setTimeout(() => {
    const flashMessages = document.querySelectorAll(".flash-message")
    flashMessages.forEach((msg) => {
      msg.style.animation = "slideOut 0.3s ease forwards"
      setTimeout(() => msg.remove(), 300)
    })
  }, 5000)
})

// Voice Recognition Setup
function initializeVoiceRecognition() {
  if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    recognition = new SpeechRecognition()

    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = "en-US"

    recognition.onstart = () => {
      isListening = true
      voiceBtn.classList.add("listening")
      voiceStatus.classList.add("show")
      document.getElementById("voiceText").textContent = ""
    }

    recognition.onresult = (event) => {
      let interimTranscript = ""
      let finalTranscript = ""

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          finalTranscript += transcript
        } else {
          interimTranscript += transcript
        }
      }

      const voiceText = document.getElementById("voiceText")
      voiceText.textContent = finalTranscript + interimTranscript

      if (finalTranscript) {
        questionInput.value = finalTranscript
        stopVoiceInput()
      }
    }

    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error)
      let errorMessage = "Voice recognition error"

      switch (event.error) {
        case "no-speech":
          errorMessage = "No speech detected. Please try again."
          break
        case "audio-capture":
          errorMessage = "Microphone not accessible. Please check permissions."
          break
        case "not-allowed":
          errorMessage = "Microphone permission denied. Please enable microphone access."
          break
        case "network":
          errorMessage = "Network error. Please check your connection."
          break
        default:
          errorMessage = `Voice recognition error: ${event.error}`
      }

      showNotification(errorMessage, "error")
      stopVoiceInput()
    }

    recognition.onend = () => {
      stopVoiceInput()
    }
  } else {
    voiceBtn.style.display = "none"
    console.warn("Speech recognition not supported")
  }
}

async function checkMicrophonePermission() {
  try {
    const permission = await navigator.permissions.query({ name: "microphone" })
    if (permission.state === "denied") {
      showNotification(
        "Microphone access is required for voice input. Please enable it in your browser settings.",
        "warning",
        8000,
      )
      return false
    }
    return true
  } catch (error) {
    console.warn("Could not check microphone permission:", error)
    return true // Assume it's available if we can't check
  }
}

async function toggleVoiceInput() {
  if (!recognition) {
    showNotification("Voice recognition not supported in this browser", "error")
    return
  }

  if (isListening) {
    stopVoiceInput()
  } else {
    const hasPermission = await checkMicrophonePermission()
    if (hasPermission) {
      startVoiceInput()
    }
  }
}

function startVoiceInput() {
  if (recognition && !isListening) {
    recognition.start()
  }
}

function stopVoiceInput() {
  if (recognition && isListening) {
    recognition.stop()
    isListening = false
    voiceBtn.classList.remove("listening")
    voiceStatus.classList.remove("show")
  }
}

// Chat History Functions
function toggleChatHistory() {
  chatHistorySidebar.classList.toggle("show")
  document.querySelector(".main-content").classList.toggle("sidebar-open")
}

function loadChatHistory() {
  if (chatHistory.length === 0) {
    chatHistoryContent.innerHTML = `
      <div class="empty-history">
        <i class="fas fa-comments"></i>
        <p>No chat history yet</p>
      </div>
    `
    return
  }

  chatHistoryContent.innerHTML = ""
  chatHistory.forEach((item, index) => {
    const historyItem = document.createElement("div")
    historyItem.className = "history-item"
    historyItem.onclick = () => loadHistoryItem(item)

    historyItem.innerHTML = `
      <div class="history-question">${item.question.substring(0, 100)}${item.question.length > 100 ? "..." : ""}</div>
      <div class="history-answer">${item.answer.substring(0, 150)}${item.answer.length > 150 ? "..." : ""}</div>
      <div class="history-timestamp">${new Date(item.timestamp).toLocaleString()}</div>
    `

    chatHistoryContent.appendChild(historyItem)
  })
}

function saveToHistory() {
  const question = questionInput.value.trim()
  const answer = document.querySelector(".answer-content p")?.textContent

  if (question && answer) {
    const historyItem = {
      question,
      answer,
      timestamp: new Date().toISOString(),
      model: document.getElementById("model").value,
      temperature: document.getElementById("temperature").value,
    }

    chatHistory.unshift(historyItem)

    // Keep only last 50 items
    if (chatHistory.length > 50) {
      chatHistory = chatHistory.slice(0, 50)
    }

    localStorage.setItem("chatHistory", JSON.stringify(chatHistory))
    loadChatHistory()
    showNotification("Saved to chat history!", "success")
  }
}

function loadHistoryItem(item) {
  questionInput.value = item.question
  document.getElementById("model").value = item.model
  document.getElementById("temperature").value = item.temperature
  document.getElementById("temp-value").textContent = item.temperature

  // Update temperature slider visual
  const percentage = ((item.temperature - 0) / (1 - 0)) * 100
  temperatureSlider.style.background = `linear-gradient(to right, #8b5cf6 0%, #764ba2 ${percentage}%, var(--border-color) ${percentage}%, var(--border-color) 100%)`

  toggleChatHistory()
  showNotification("Loaded from history!", "info")
}

function clearChatHistory() {
  if (confirm("Are you sure you want to clear all chat history?")) {
    chatHistory = []
    localStorage.removeItem("chatHistory")
    loadChatHistory()
    showNotification("Chat history cleared!", "info")
  }
}

// File Upload Functionality
function initializeFileUpload() {
  // Drag and drop
  uploadArea.addEventListener("dragover", handleDragOver)
  uploadArea.addEventListener("dragleave", handleDragLeave)
  uploadArea.addEventListener("drop", handleDrop)

  // File input change
  fileInput.addEventListener("change", handleFileSelect)

  // Click to upload
  uploadArea.addEventListener("click", () => fileInput.click())
}

function handleDragOver(e) {
  e.preventDefault()
  uploadArea.classList.add("dragover")
}

function handleDragLeave(e) {
  e.preventDefault()
  uploadArea.classList.remove("dragover")
}

function handleDrop(e) {
  e.preventDefault()
  uploadArea.classList.remove("dragover")

  const files = Array.from(e.dataTransfer.files)
  handleFiles(files)
}

function handleFileSelect(e) {
  const files = Array.from(e.target.files)
  handleFiles(files)
}

function handleFiles(files) {
  const allowedTypes = [".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls", ".txt"]

  files.forEach((file) => {
    const fileExt = "." + file.name.split(".").pop().toLowerCase()

    if (allowedTypes.includes(fileExt)) {
      if (!selectedFiles.find((f) => f.name === file.name && f.size === file.size)) {
        selectedFiles.push(file)
      }
    } else {
      showNotification(`File type ${fileExt} is not supported`, "error")
    }
  })

  updateFileList()
  updateFileInput()
}

function updateFileList() {
  fileList.innerHTML = ""

  selectedFiles.forEach((file, index) => {
    const fileItem = document.createElement("div")
    fileItem.className = "file-item"

    const fileIcon = getFileIcon(file.name)
    const fileSize = formatFileSize(file.size)

    fileItem.innerHTML = `
      <div class="file-info">
        <i class="fas ${fileIcon} file-icon"></i>
        <div>
          <div class="file-name">${file.name}</div>
          <div class="file-size">${fileSize}</div>
        </div>
      </div>
      <div class="file-actions">
        <button type="button" class="preview-btn" onclick="previewFile(${index})" title="Preview">
          <i class="fas fa-eye"></i>
        </button>
        <button type="button" class="remove-file" onclick="removeFile(${index})" title="Remove">
          <i class="fas fa-times"></i>
        </button>
      </div>
    `

    fileList.appendChild(fileItem)
  })
}

function removeFile(index) {
  selectedFiles.splice(index, 1)
  updateFileList()
  updateFileInput()
}

function updateFileInput() {
  // Create a new DataTransfer object to update the file input
  const dt = new DataTransfer()
  selectedFiles.forEach((file) => dt.items.add(file))
  fileInput.files = dt.files
}

function getFileIcon(filename) {
  const ext = filename.split(".").pop().toLowerCase()
  const iconMap = {
    pdf: "fa-file-pdf",
    doc: "fa-file-word",
    docx: "fa-file-word",
    ppt: "fa-file-powerpoint",
    pptx: "fa-file-powerpoint",
    xls: "fa-file-excel",
    xlsx: "fa-file-excel",
    txt: "fa-file-alt",
  }
  return iconMap[ext] || "fa-file"
}

function formatFileSize(bytes) {
  if (bytes === 0) return "0 Bytes"
  const k = 1024
  const sizes = ["Bytes", "KB", "MB", "GB"]
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
}

// Temperature Slider
function initializeTemperatureSlider() {
  temperatureSlider.addEventListener("input", function () {
    tempValue.textContent = this.value

    // Update slider color based on value
    const percentage = ((this.value - this.min) / (this.max - this.min)) * 100
    this.style.background = `linear-gradient(to right, #8b5cf6 0%, #764ba2 ${percentage}%, var(--border-color) ${percentage}%, var(--border-color) 100%)`
  })

  // Initialize slider color
  const initialPercentage =
    ((temperatureSlider.value - temperatureSlider.min) / (temperatureSlider.max - temperatureSlider.min)) * 100
  temperatureSlider.style.background = `linear-gradient(to right, #8b5cf6 0%, #764ba2 ${initialPercentage}%, var(--border-color) ${initialPercentage}%, var(--border-color) 100%)`
}

// Form Submission
function initializeFormSubmission() {
  configForm.addEventListener("submit", (e) => {
    const question = questionInput.value.trim()
    const hasFiles = selectedFiles.length > 0
    const hasUrls = document.getElementById("document_links").value.trim()

    if (!question) {
      e.preventDefault()
      showNotification("Please enter a question", "error")
      questionInput.focus()
      return
    }

    if (!hasFiles && !hasUrls) {
      // Allow submission without documents (will use Pinecone)
      const confirmed = confirm("No documents provided. The system will search the general knowledge base. Continue?")
      if (!confirmed) {
        e.preventDefault()
        return
      }
    }

    // Show progress
    progressManager.show()
    showLoadingWithProgress()

    // Disable submit button
    submitBtn.disabled = true
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>Processing...</span>'

    // Simulate progress steps
    setTimeout(() => progressManager.nextStep(), 500)
    setTimeout(() => progressManager.nextStep(), 1500)
    setTimeout(() => progressManager.nextStep(), 3000)
    setTimeout(() => progressManager.nextStep(), 5000)
  })
}

// Keyboard Shortcuts
function initializeKeyboardShortcuts() {
  document.addEventListener("keydown", (e) => {
    // Ctrl/Cmd + Enter to submit
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      if (document.activeElement === questionInput) {
        configForm.dispatchEvent(new Event("submit"))
      }
    }

    // Ctrl/Cmd + D for dark mode
    if ((e.ctrlKey || e.metaKey) && e.key === "d") {
      e.preventDefault()
      toggleTheme()
    }

    // Ctrl/Cmd + H for chat history
    if ((e.ctrlKey || e.metaKey) && e.key === "h") {
      e.preventDefault()
      toggleChatHistory()
    }

    // Ctrl/Cmd + Space for voice input
    if ((e.ctrlKey || e.metaKey) && e.key === " ") {
      e.preventDefault()
      toggleVoiceInput()
    }

    // Escape to clear question or close modals
    if (e.key === "Escape") {
      if (document.activeElement === questionInput) {
        questionInput.value = ""
      }
      closeFilePreview()
      hideLoading()
      stopVoiceInput()
      if (chatHistorySidebar.classList.contains("show")) {
        toggleChatHistory()
      }
    }
  })
}

// Utility Functions
function showLoading() {
  loadingOverlay.classList.add("show")
}

function hideLoading() {
  loadingOverlay.classList.remove("show")
}

function showNotification(message, type = "info", duration = 5000) {
  const notification = document.createElement("div")
  notification.className = `flash-message flash-${type}`

  const icons = {
    info: "info-circle",
    error: "exclamation-triangle",
    success: "check-circle",
    warning: "exclamation-circle",
  }

  notification.innerHTML = `
    <i class="fas fa-${icons[type] || icons.info}"></i>
    <span>${message}</span>
    <button class="close-flash" onclick="this.parentElement.remove()">
      <i class="fas fa-times"></i>
    </button>
  `

  let container = document.querySelector(".flash-messages")
  if (!container) {
    container = document.createElement("div")
    container.className = "flash-messages"
    document.body.appendChild(container)
  }

  container.appendChild(notification)

  // Auto-remove
  setTimeout(() => {
    if (notification.parentElement) {
      notification.style.animation = "slideOut 0.3s ease forwards"
      setTimeout(() => notification.remove(), 300)
    }
  }, duration)
}

// Answer Actions
function copyAnswer() {
  const answerText = document.querySelector(".answer-content p").textContent
  navigator.clipboard
    .writeText(answerText)
    .then(() => {
      showNotification("Answer copied to clipboard!", "success")
    })
    .catch(() => {
      showNotification("Failed to copy answer", "error")
    })
}

function shareAnswer() {
  const answerText = document.querySelector(".answer-content p").textContent
  const question = document.getElementById("question").value

  if (navigator.share) {
    navigator.share({
      title: "AI Document Analysis Result",
      text: `Question: ${question}\n\nAnswer: ${answerText}`,
    })
  } else {
    // Fallback: copy to clipboard
    const shareText = `Question: ${question}\n\nAnswer: ${answerText}`
    navigator.clipboard.writeText(shareText).then(() => {
      showNotification("Answer and question copied to clipboard!", "success")
    })
  }
}

// Sources Toggle
function toggleSources() {
  const sourcesContent = document.getElementById("sourcesContent")
  const toggleBtn = document.querySelector(".toggle-btn i")

  if (sourcesContent.classList.contains("show")) {
    sourcesContent.classList.remove("show")
    toggleBtn.className = "fas fa-chevron-down"
  } else {
    sourcesContent.classList.add("show")
    toggleBtn.className = "fas fa-chevron-up"
  }
}

// Example Questions
function setQuestion(question) {
  questionInput.value = question.replace(/"/g, "")
  questionInput.focus()

  // Smooth scroll to question input
  questionInput.scrollIntoView({ behavior: "smooth", block: "center" })

  // Add a subtle highlight effect
  questionInput.style.boxShadow = "0 0 0 3px rgba(139, 92, 246, 0.3)"
  setTimeout(() => {
    questionInput.style.boxShadow = ""
  }, 2000)
}

// Auto-resize textarea
questionInput.addEventListener("input", function () {
  this.style.height = "auto"
  this.style.height = Math.max(120, this.scrollHeight) + "px"
})

// Theme Management
function toggleTheme() {
  const body = document.body
  const themeToggle = document.querySelector(".theme-toggle i")

  if (body.classList.contains("dark-theme")) {
    body.classList.remove("dark-theme")
    themeToggle.className = "fas fa-moon"
    localStorage.setItem("theme", "light")
    showNotification("Switched to light mode", "info", 2000)
  } else {
    body.classList.add("dark-theme")
    themeToggle.className = "fas fa-sun"
    localStorage.setItem("theme", "dark")
    showNotification("Switched to dark mode", "info", 2000)
  }
}

// Load saved theme
document.addEventListener("DOMContentLoaded", () => {
  const savedTheme = localStorage.getItem("theme")
  const themeToggle = document.querySelector(".theme-toggle i")

  if (savedTheme === "dark") {
    document.body.classList.add("dark-theme")
    themeToggle.className = "fas fa-sun"
  }
})

// Enhanced Progress Management
class ProgressManager {
  constructor() {
    this.container = document.getElementById("progressContainer")
    this.fill = document.getElementById("progressFill")
    this.text = document.getElementById("progressText")
    this.steps = [
      "Initializing...",
      "Processing documents...",
      "Building vector index...",
      "Querying AI model...",
      "Generating response...",
      "Complete!",
    ]
    this.currentStep = 0
  }

  show() {
    this.container.classList.add("show")
    this.reset()
  }

  hide() {
    this.container.classList.remove("show")
  }

  reset() {
    this.currentStep = 0
    this.fill.style.width = "0%"
    this.text.textContent = this.steps[0]
  }

  nextStep() {
    if (this.currentStep < this.steps.length - 1) {
      this.currentStep++
      const progress = (this.currentStep / (this.steps.length - 1)) * 100
      this.fill.style.width = `${progress}%`
      this.text.textContent = this.steps[this.currentStep]
    }
  }

  setProgress(percentage, message) {
    this.fill.style.width = `${percentage}%`
    if (message) this.text.textContent = message
  }
}

const progressManager = new ProgressManager()

// File Preview Functionality
function previewFile(index) {
  const file = selectedFiles[index]
  const modal = document.getElementById("filePreviewModal")
  const content = document.getElementById("filePreviewContent")

  content.innerHTML = '<div class="loading-spinner"></div><p>Loading preview...</p>'
  modal.classList.add("show")

  const reader = new FileReader()

  reader.onload = (e) => {
    const fileType = file.type
    let previewHTML = ""

    if (fileType.includes("text")) {
      previewHTML = `
        <div class="text-preview">
          <h4>${file.name}</h4>
          <pre>${e.target.result.substring(0, 2000)}${e.target.result.length > 2000 ? "..." : ""}</pre>
        </div>
      `
    } else if (fileType.includes("image")) {
      previewHTML = `
        <div class="image-preview">
          <h4>${file.name}</h4>
          <img src="${e.target.result}" alt="Preview" style="max-width: 100%; height: auto;">
        </div>
      `
    } else {
      previewHTML = `
        <div class="file-info-preview">
          <h4>${file.name}</h4>
          <div class="file-details">
            <p><strong>Size:</strong> ${formatFileSize(file.size)}</p>
            <p><strong>Type:</strong> ${file.type || "Unknown"}</p>
            <p><strong>Last Modified:</strong> ${new Date(file.lastModified).toLocaleString()}</p>
          </div>
          <div class="preview-note">
            <i class="fas fa-info-circle"></i>
            <p>Preview not available for this file type. The file will be processed when you submit your question.</p>
          </div>
        </div>
      `
    }

    content.innerHTML = previewHTML
  }

  reader.onerror = () => {
    content.innerHTML = `
      <div class="preview-error">
        <i class="fas fa-exclamation-triangle"></i>
        <h4>Preview Error</h4>
        <p>Could not load preview for ${file.name}</p>
      </div>
    `
  }

  if (file.type.includes("text")) {
    reader.readAsText(file)
  } else if (file.type.includes("image")) {
    reader.readAsDataURL(file)
  } else {
    reader.onload()
  }
}

function closeFilePreview() {
  document.getElementById("filePreviewModal").classList.remove("show")
}

// Enhanced Loading with Progress
function showLoadingWithProgress() {
  const overlay = document.getElementById("loadingOverlay")
  const progressFill = document.getElementById("loadingProgressFill")
  const percentage = document.getElementById("loadingPercentage")
  const status = document.getElementById("loadingStatus")

  overlay.classList.add("show")

  let progress = 0
  const interval = setInterval(() => {
    progress += Math.random() * 15
    if (progress > 90) progress = 90

    progressFill.style.width = `${progress}%`
    percentage.textContent = `${Math.round(progress)}%`

    if (progress > 20) status.textContent = "Processing documents..."
    if (progress > 50) status.textContent = "Analyzing content..."
    if (progress > 80) status.textContent = "Generating response..."
  }, 200)

  // Clear interval when form actually submits
  setTimeout(() => {
    clearInterval(interval)
    progressFill.style.width = "100%"
    percentage.textContent = "100%"
    status.textContent = "Complete!"
  }, 8000)
}

// Performance monitoring
let startTime
window.addEventListener("beforeunload", () => {
  if (startTime) {
    const duration = Date.now() - startTime
    console.log(`Page interaction duration: ${duration}ms`)
  }
})

// Track form submission time
configForm.addEventListener("submit", () => {
  startTime = Date.now()
})

// Hide loading on page load (in case of back navigation)
window.addEventListener("load", () => {
  hideLoading()
  progressManager.hide()

  // Re-enable submit button
  submitBtn.disabled = false
  submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i><span>Analyze</span>'
})

// Add CSS animation for slideOut
const style = document.createElement("style")
style.textContent = `
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`
document.head.appendChild(style)
