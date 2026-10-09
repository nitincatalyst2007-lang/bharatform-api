chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "AUTOFILL") {
    const data = request.profile;

    // Detect Name fields
    const nameInputs = document.querySelectorAll('input[name*="name" i], input[id*="name" i], input[placeholder*="name" i]');
    nameInputs.forEach(input => {
      input.value = data.name;
      input.dispatchEvent(new Event('input', { bubbles: true }));
    });

    // Detect DOB fields
    const dobInputs = document.querySelectorAll('input[name*="dob" i], input[id*="dob" i], input[name*="date" i]');
    dobInputs.forEach(input => {
      input.value = data.dob;
      input.dispatchEvent(new Event('input', { bubbles: true }));
    });

    sendResponse({ status: "success" });
  }
});