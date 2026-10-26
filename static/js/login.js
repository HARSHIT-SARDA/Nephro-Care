// Optional login-page enhancements. The Flask backend performs authentication.
document.addEventListener("DOMContentLoaded", () => {
  const password = document.getElementById("password");
  const togglePassword = document.getElementById("togglePassword");
  const form = document.querySelector("form");

  if (togglePassword && password) {
    togglePassword.addEventListener("click", () => {
      const showing = password.type === "password";
      password.type = showing ? "text" : "password";
      togglePassword.classList.toggle("bi-eye-fill", !showing);
      togglePassword.classList.toggle("bi-eye-slash-fill", showing);
    });
  }

  if (form) {
    form.addEventListener("submit", (event) => {
      const email = form.querySelector("input[type='email']");
      if (email && !/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email.value.trim())) {
        event.preventDefault();
        alert("Please enter a valid email address.");
      }
    });
  }
});
