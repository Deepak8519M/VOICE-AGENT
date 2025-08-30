const sidebarItems = document.querySelectorAll(".settings-sidebar li");
const cards = document.querySelectorAll(".settings-card");
const apiForm = document.getElementById("apiForm");
const settingsForm = document.querySelector(".settings-main");
const notification = document.getElementById("notification");
const cancelBtn = document.querySelector(".cancel-btn");
const saveBtn = document.querySelector(".settings-footer .save-btn");
const resetBtn = document.querySelector(".reset-btn");
const enableCustomKeys = document.getElementById("enableCustomKeys");
const apiInputs = document.querySelectorAll(
  "#apiForm input[type='password'], #apiForm input[type='text']"
);
const sliders = document.querySelectorAll(".slider");
const previewVoiceBtn = document.getElementById("previewVoice");
const accentColorSelect = document.querySelector("select[name='accentColor']");
const themeSelect = document.querySelector("select[name='theme']");

// Color definitions
const colorSchemes = {
  orange: {
    primary: "#ff8d04",
    gradientStart: "#ffd700",
    gradientEnd: "#ff8d04",
  },
  blue: {
    primary: "#1e88e5",
    gradientStart: "#4fc3f7",
    gradientEnd: "#1e88e5",
  },
  green: {
    primary: "#43a047",
    gradientStart: "#a5d6a7",
    gradientEnd: "#43a047",
  },
};

// Apply theme and accent color
function applyTheme(theme, accentColor) {
  document.documentElement.setAttribute("data-theme", theme);
  const scheme = colorSchemes[accentColor];
  document.documentElement.style.setProperty("--accent-color", scheme.primary);
  document.documentElement.style.setProperty(
    "--accent-gradient-start",
    scheme.gradientStart
  );
  document.documentElement.style.setProperty(
    "--accent-gradient-end",
    scheme.gradientEnd
  );
}

document.addEventListener("DOMContentLoaded", () => {
  const menuToggle = document.querySelector(".menu-toggle");
  const sidebarUl = document.querySelector(".settings-sidebar ul");
  const expandButtons = document.querySelectorAll(".expand-btn");
  const sidebarItems = document.querySelectorAll(
    ".settings-sidebar li[data-section]"
  );

  // Toggle sidebar on mobile
  menuToggle.addEventListener("click", () => {
    sidebarUl.classList.toggle("active");
    menuToggle.textContent = sidebarUl.classList.contains("active") ? "✖" : "☰";
  });

  // Accordion functionality
  expandButtons.forEach((button) => {
    button.addEventListener("click", (e) => {
      const subMenu = e.target.nextElementSibling;
      const isExpanded = e.target.getAttribute("aria-expanded") === "true";
      e.target.setAttribute("aria-expanded", !isExpanded);
      e.target.textContent = isExpanded ? "▶" : "▼";
      subMenu.classList.toggle("active");
      e.stopPropagation(); // Prevent triggering the parent li click
    });
  });

  // Sidebar navigation
  sidebarItems.forEach((item) => {
    item.addEventListener("click", (e) => {
      const section = item.getAttribute("data-section");
      document
        .querySelectorAll(".settings-card")
        .forEach((card) => card.classList.remove("active"));
      document.getElementById(section).classList.add("active");
      sidebarItems.forEach((li) => li.classList.remove("active"));
      item.classList.add("active");
      if (window.innerWidth <= 900) {
        sidebarUl.classList.remove("active");
        menuToggle.textContent = "☰";
      }
    });
  });

  // Initial active section
  const initialSection = document.querySelector(".settings-card.active");
  if (initialSection) {
    initialSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }
});

// Load saved settings from server on page load
async function loadSettings() {
  try {
    const response = await fetch("/get_settings");
    const settings = await response.json();
    if (!settings.error) {
      document.querySelector("select[name='voiceId']").value =
        settings.voiceId || "en-IN-alia";
      document.querySelector("input[name='playbackSpeed']").value =
        settings.playbackSpeed || 1.0;
      document.querySelector("select[name='conversationType']").value =
        settings.conversationType || "casual";
      document.querySelector("input[name='micSensitivity']").value =
        settings.micSensitivity || 50;
      document.querySelector("select[name='audioQuality']").value =
        settings.audioQuality || "medium";
      document.querySelector("input[name='autoSaveHistory']").checked =
        settings.autoSaveHistory !== false;
      document.querySelector("input[name='includeKnowledgeBase']").checked =
        settings.includeKnowledgeBase !== false;
      document.querySelector("input[name='enableSearch']").checked =
        settings.enableSearch !== false;
      document.querySelector("input[name='maxSearchResults']").value =
        settings.maxSearchResults || 3;
      document.querySelector("input[name='enableSound']").checked =
        settings.enableSound !== false;
      document.querySelector("input[name='notificationDuration']").value =
        settings.notificationDuration || 4;
      document.querySelector("select[name='theme']").value =
        settings.theme || "dark";
      document.querySelector("select[name='accentColor']").value =
        settings.accentColor || "orange";
      sliders.forEach((slider) => {
        const valueSpan = slider.nextElementSibling;
        valueSpan.textContent =
          slider.name === "micSensitivity"
            ? `${slider.value}%`
            : `${slider.value}x`;
      });
      applyTheme(settings.theme || "dark", settings.accentColor || "orange");
      localStorage.setItem("theme", settings.theme || "dark");
      localStorage.setItem("accentColor", settings.accentColor || "orange");
    } else {
      console.error("Failed to load settings:", settings.error);
      showNotification("Error loading settings.", true);
    }
  } catch (error) {
    console.error("Error fetching settings:", error);
    showNotification("Error loading settings.", true);
  }
}

// Load saved settings on page load
document.addEventListener("DOMContentLoaded", () => {
  loadSettings();
});

// Dynamic theme update
themeSelect.addEventListener("change", () => {
  const theme = themeSelect.value;
  const accentColor = accentColorSelect.value;
  applyTheme(theme, accentColor);
  localStorage.setItem("theme", theme);
});

// Dynamic accent color update
accentColorSelect.addEventListener("change", () => {
  const theme = themeSelect.value;
  const accentColor = accentColorSelect.value;
  applyTheme(theme, accentColor);
  localStorage.setItem("accentColor", accentColor);
});

// Sidebar navigation
sidebarItems.forEach((item) => {
  item.addEventListener("click", () => {
    sidebarItems.forEach((i) => i.classList.remove("active"));
    item.classList.add("active");
    cards.forEach((card) => card.classList.remove("active"));
    const sectionId = item.getAttribute("data-section");
    document.getElementById(sectionId).classList.add("active");
  });
});

// Toggle API inputs
enableCustomKeys.addEventListener("change", () => {
  const isEnabled = enableCustomKeys.checked;
  apiInputs.forEach((input) => {
    input.disabled = !isEnabled;
    input.classList.remove("error");
  });
});

// Update slider values
sliders.forEach((slider) => {
  const valueSpan = slider.nextElementSibling;
  slider.addEventListener("input", () => {
    valueSpan.textContent =
      slider.name === "micSensitivity"
        ? `${slider.value}%`
        : `${slider.value}x`;
  });
});

// Show notification
function showNotification(message, isError = false) {
  notification.textContent = message;
  notification.className = `notification ${isError ? "error" : ""}`;
  notification.style.display = "block";
  const duration =
    parseInt(
      document.querySelector("input[name='notificationDuration']").value
    ) * 1000 || 4000;
  setTimeout(() => {
    notification.style.display = "none";
  }, duration);
}

// API form submission with validation
apiForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const settings = {
    enableCustomKeys: enableCustomKeys.checked,
    aai_api_key: document
      .querySelector("#apiForm input[name='aai_api_key']")
      .value.trim(),
    gemini_api_key: document
      .querySelector("#apiForm input[name='gemini_api_key']")
      .value.trim(),
    murf_api_key: document
      .querySelector("#apiForm input[name='murf_api_key']")
      .value.trim(),
    tavily_api_key: document
      .querySelector("#apiForm input[name='tavily_api_key']")
      .value.trim(),
    zapier_webhook_url: document
      .querySelector("#apiForm input[name='zapier_webhook_url']")
      .value.trim(),
    override_env: enableCustomKeys.checked ? "true" : "false",
  };

  if (settings.enableCustomKeys) {
    let hasError = false;
    const requiredFields = [
      "aai_api_key",
      "gemini_api_key",
      "murf_api_key",
      "tavily_api_key",
    ];
    requiredFields.forEach((field) => {
      if (!settings[field]) {
        document
          .querySelector(`#apiForm input[name='${field}']`)
          .classList.add("error");
        hasError = true;
      } else {
        document
          .querySelector(`#apiForm input[name='${field}']`)
          .classList.remove("error");
      }
    });
    if (hasError) {
      showNotification("Please fill all required API keys.", true);
      return;
    }
  }

  try {
    const response = await fetch("/set_keys", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings),
    });
    const result = await response.json();
    if (result.error) {
      showNotification(`${result.error} Falling back to .env keys.`, true);
    } else {
      showNotification("API keys saved successfully!");
    }
    setTimeout(() => (window.location.href = "/"), 2000);
  } catch (error) {
    console.error("Error saving API keys:", error);
    showNotification("Error saving API keys. Falling back to .env keys.", true);
    setTimeout(() => (window.location.href = "/"), 2000);
  }
});

// General settings submission
saveBtn.addEventListener("click", async () => {
  const settings = {
    voiceId: document.querySelector("select[name='voiceId']").value,
    playbackSpeed: parseFloat(
      document.querySelector("input[name='playbackSpeed']").value
    ),
    conversationType: document.querySelector("select[name='conversationType']")
      .value,
    micSensitivity: parseInt(
      document.querySelector("input[name='micSensitivity']").value
    ),
    audioQuality: document.querySelector("select[name='audioQuality']").value,
    autoSaveHistory: document.querySelector("input[name='autoSaveHistory']")
      .checked,
    includeKnowledgeBase: document.querySelector(
      "input[name='includeKnowledgeBase']"
    ).checked,
    enableSearch: document.querySelector("input[name='enableSearch']").checked,
    maxSearchResults: parseInt(
      document.querySelector("input[name='maxSearchResults']").value
    ),
    enableSound: document.querySelector("input[name='enableSound']").checked,
    notificationDuration: parseInt(
      document.querySelector("input[name='notificationDuration']").value
    ),
    theme: document.querySelector("select[name='theme']").value,
    accentColor: document.querySelector("select[name='accentColor']").value,
  };

  try {
    const response = await fetch("/set_settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings),
    });
    const result = await response.json();
    if (result.error) {
      console.error("Error saving settings:", result.error);
      showNotification(`Error saving settings: ${result.error}`, true);
    } else {
      showNotification("Settings saved successfully!");
      localStorage.setItem("theme", settings.theme);
      localStorage.setItem("accentColor", settings.accentColor);
      applyTheme(settings.theme, settings.accentColor);
    }
    setTimeout(() => (window.location.href = "/app"), 2000);
  } catch (error) {
    console.error("Error saving settings:", error);
    showNotification("Error saving settings.", true);
    setTimeout(() => (window.location.href = "/app"), 2000);
  }
});

// Cancel button
cancelBtn.addEventListener("click", () => {
  window.location.href = "/app";
});

// Reset to defaults
resetBtn.addEventListener("click", async () => {
  try {
    const response = await fetch("/reset_settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reset: true }),
    });
    const result = await response.json();
    if (result.error) {
      console.error("Error resetting settings:", result.error);
      showNotification(`Error resetting settings: ${result.error}`, true);
    } else {
      showNotification("Settings reset to defaults!");
      // Explicitly set form values to defaults
      document.querySelector("select[name='voiceId']").value = "en-IN-alia";
      document.querySelector("input[name='playbackSpeed']").value = "1.0";
      document.querySelector("select[name='conversationType']").value =
        "casual";
      document.querySelector("input[name='micSensitivity']").value = "50";
      document.querySelector("select[name='audioQuality']").value = "medium";
      document.querySelector("input[name='autoSaveHistory']").checked = true;
      document.querySelector(
        "input[name='includeKnowledgeBase']"
      ).checked = true;
      document.querySelector("input[name='enableSearch']").checked = true;
      document.querySelector("input[name='maxSearchResults']").value = "3";
      document.querySelector("input[name='enableSound']").checked = true;
      document.querySelector("input[name='notificationDuration']").value = "4";
      document.querySelector("select[name='theme']").value = "dark";
      document.querySelector("select[name='accentColor']").value = "orange";
      // Update API inputs
      enableCustomKeys.checked = false;
      apiInputs.forEach((input) => {
        input.value = "";
        input.disabled = true;
        input.classList.remove("error");
      });
      // Update slider displays
      sliders.forEach((slider) => {
        const valueSpan = slider.nextElementSibling;
        valueSpan.textContent =
          slider.name === "micSensitivity"
            ? `${slider.value}%`
            : `${slider.value}x`;
      });
      // Apply theme
      applyTheme("dark", "orange");
      localStorage.setItem("theme", "dark");
      localStorage.setItem("accentColor", "orange");
      // Reload settings to ensure sync
      await loadSettings();
    }
  } catch (error) {
    console.error("Error resetting settings:", error);
    showNotification("Error resetting settings.", true);
  }
});

// Clear chat history
document.getElementById("clearHistory").addEventListener("click", async () => {
  try {
    const response = await fetch("/clear_chat_history", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ clear: true }),
    });
    const result = await response.json();
    if (result.error) {
      console.error("Error clearing chat history:", result.error);
      showNotification(`Error clearing chat history: ${result.error}`, true);
    } else {
      showNotification("Chat history cleared successfully!");
    }
  } catch (error) {
    console.error("Error clearing chat history:", error);
    showNotification("Error clearing chat history.", true);
  }
});

// Clear knowledge base
document
  .getElementById("clearKnowledgeBase")
  .addEventListener("click", async () => {
    try {
      const response = await fetch("/clear_knowledge_base", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ clear: true }),
      });
      const result = await response.json();
      if (result.error) {
        console.error("Error clearing knowledge base:", result.error);
        showNotification(
          `Error clearing knowledge base: ${result.error}`,
          true
        );
      } else {
        showNotification("Knowledge base cleared successfully!");
      }
    } catch (error) {
      console.error("Error clearing knowledge base:", error);
      showNotification("Error clearing knowledge base.", true);
    }
  });

// Preview voice
previewVoiceBtn.addEventListener("click", async () => {
  const voiceId = document.querySelector("select[name='voiceId']").value;
  const sampleText = "Hello! This is a sample of my voice.";
  try {
    const response = await fetch("/ws?chat_id=1", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ command: `speak:${sampleText}`, voiceId }),
    });
    const result = await response.json();
    if (result.error) {
      console.error("Error previewing voice:", result.error);
      showNotification(`Error previewing voice: ${result.error}`, true);
    } else {
      showNotification("Voice preview playing!");
    }
  } catch (error) {
    console.error("Error previewing voice:", error);
    showNotification("Error previewing voice.", true);
  }
});

// Navigation buttons
document.querySelectorAll(".nav-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    const target = btn.getAttribute("data-nav");
    if (target === "home") {
      window.location.href = "/";
    } else if (target === "voice-agent") {
      window.location.href = "/app";
    }
  });
});
