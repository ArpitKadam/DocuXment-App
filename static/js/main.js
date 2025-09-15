document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const uploadArea = document.getElementById("uploadArea")
  const fileInput = document.getElementById("fileInput")
  const temperatureSlider = document.getElementById("temperature")
  const tempValue = document.getElementById("tempValue")
  const submitBtn = document.querySelector(".submit-btn")
  const loadingOverlay = document.getElementById("loadingOverlay")
  const mainForm = document.querySelector(".main-form")

  // File Upload Drag & Drop
  if (uploadArea && fileInput) {
    ;["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
      uploadArea.addEventListener(eventName, preventDefaults, false)
      document.body.addEventListener(eventName, preventDefaults, false)
    })
    ;["dragenter", "dragover"].forEach((eventName) => {
      uploadArea.addEventListener(eventName, highlight, false)
    })
    ;["dragleave", "drop"].forEach((eventName) => {
      uploadArea.addEventListener(eventName, unhighlight, false)
    })

    uploadArea.addEventListener("drop", handleDrop, false)
    uploadArea.addEventListener("click", () => fileInput.click())
    fileInput.addEventListener("change", handleFiles)
  }

  // Temperature Slider
  if (temperatureSlider && tempValue) {
    temperatureSlider.addEventListener("input", function () {
      tempValue.textContent = this.value
    })
  }

  // Form Submission
  if (mainForm && submitBtn && loadingOverlay) {
    mainForm.addEventListener("submit", (e) => {
      const question = document.getElementById("question").value.trim()
      const files = fileInput ? fileInput.files : []
      const urls = document.getElementById("document_links").value.trim()

      if (!question) {
        e.preventDefault()
        alert("Please enter a question.")
        return
      }

      if (files.length === 0 && !urls) {
        const confirmSubmit = confirm(
          "No documents provided. The system will use the default knowledge base. Continue?",
        )
        if (!confirmSubmit) {
          e.preventDefault()
          return
        }
      }

      showLoading()
    })
  }

  // Auto-hide flash messages
  const flashMessages = document.querySelectorAll(".flash-message")
  flashMessages.forEach((message) => {
    setTimeout(() => {
      message.style.animation = "slideOut 0.3s ease forwards"
      setTimeout(() => message.remove(), 300)
    }, 5000)
  })

  // Utility Functions
  function preventDefaults(e) {
    e.preventDefault()
    e.stopPropagation()
  }

  function highlight(e) {
    uploadArea.classList.add("dragover")
  }

  function unhighlight(e) {
    uploadArea.classList.remove("dragover")
  }

  function handleDrop(e) {
    const dt = e.dataTransfer
    const files = dt.files
    if (fileInput) {
      fileInput.files = files
      handleFiles()
    }
  }

  function handleFiles() {
    const files = fileInput.files
    if (files.length > 0) {
      updateUploadText(files)
    }
  }

  function updateUploadText(files) {
    const uploadText = uploadArea.querySelector(".upload-text")
    const fileNames = Array.from(files)
      .map((file) => file.name)
      .join(", ")
    uploadText.innerHTML = `<strong>${files.length} file(s) selected:</strong><br>${fileNames}`
  }

  function showLoading() {
    loadingOverlay.style.display = "flex"
    if (submitBtn) {
      submitBtn.disabled = true
      submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...'
    }
  }

  // Auto-resize textareas
  const textareas = document.querySelectorAll("textarea")
  textareas.forEach((textarea) => {
    textarea.addEventListener("input", function () {
      this.style.height = "auto"
      this.style.height = this.scrollHeight + "px"
    })
  })

  // Keyboard shortcuts
  document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      const questionInput = document.getElementById("question")
      if (questionInput === document.activeElement && mainForm) {
        mainForm.dispatchEvent(new Event("submit"))
      }
    }
  })
})

// Add slideOut animation
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
