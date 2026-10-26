// =====================================
// NephroCare Register Page
// =====================================

// Password fields
const password = document.getElementById("password");
const confirmPassword = document.getElementById("confirmPassword");

// Toggle buttons
const togglePassword = document.getElementById("togglePassword");
const toggleConfirmPassword = document.getElementById("toggleConfirmPassword");

// Register form
const registerForm = document.getElementById("registerForm");


// =====================================
// PASSWORD TOGGLE
// =====================================

if (togglePassword && password) {

    togglePassword.addEventListener("click", () => {

        if (password.type === "password") {

            password.type = "text";

            togglePassword.classList.replace(
                "bi-eye-fill",
                "bi-eye-slash-fill"
            );

        } else {

            password.type = "password";

            togglePassword.classList.replace(
                "bi-eye-slash-fill",
                "bi-eye-fill"
            );
        }

    });

}


// =====================================
// CONFIRM PASSWORD TOGGLE
// =====================================

if (toggleConfirmPassword && confirmPassword) {

    toggleConfirmPassword.addEventListener("click", () => {

        if (confirmPassword.type === "password") {

            confirmPassword.type = "text";

            toggleConfirmPassword.classList.replace(
                "bi-eye-fill",
                "bi-eye-slash-fill"
            );

        } else {

            confirmPassword.type = "password";

            toggleConfirmPassword.classList.replace(
                "bi-eye-slash-fill",
                "bi-eye-fill"
            );

        }

    });

}


// =====================================
// REGISTER VALIDATION
// =====================================

if (registerForm) {

    registerForm.addEventListener("submit", function (e) {

        const name = document.getElementById("name").value.trim();
        const email = document.getElementById("email").value.trim();
        const mobile = document.getElementById("mobile").value.trim();
        const pass = password.value.trim();
        const confirm = confirmPassword.value.trim();


        // Empty validation

        if (
            name === "" ||
            email === "" ||
            mobile === "" ||
            pass === "" ||
            confirm === ""
        ) {

            e.preventDefault();

            alert("Please fill all fields.");

            return;
        }


        // Email validation

        const emailPattern =
            /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (!emailPattern.test(email)) {

            e.preventDefault();

            alert("Please enter a valid email.");

            return;
        }


        // Mobile validation

        if (!/^[6-9]\d{9}$/.test(mobile)) {

            e.preventDefault();

            alert("Enter a valid 10-digit mobile number.");

            return;
        }


        // Password length

        if (pass.length < 8) {

            e.preventDefault();

            alert("Password must be at least 8 characters.");

            return;
        }


        // Confirm password

        if (pass !== confirm) {

            e.preventDefault();

            alert("Passwords do not match.");

            return;
        }


        // =====================================
        // IMPORTANT
        // =====================================
        // Do NOT use e.preventDefault() here.
        // Browser will submit the form to Flask.

    });

}