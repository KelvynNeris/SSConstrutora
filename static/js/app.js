document.addEventListener("DOMContentLoaded", () => {
    document.body.classList.add("is-ready");

    const revealItems = document.querySelectorAll(
        ".resource-card, .request-block, .form-heading, .auth-form, .pending-content"
    );

    revealItems.forEach((item, index) => {
        item.classList.add("reveal-item");
        item.style.setProperty("--reveal-delay", `${Math.min(index * 90, 450)}ms`);
    });

    if ("IntersectionObserver" in window) {
        const observer = new IntersectionObserver((entries, currentObserver) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("is-visible");
                    currentObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.12 });

        revealItems.forEach((item) => observer.observe(item));
    } else {
        revealItems.forEach((item) => item.classList.add("is-visible"));
    }

    document.querySelectorAll("form").forEach((form) => {
        form.addEventListener("submit", () => {
            const submitButton = form.querySelector("button[type='submit']");
            if (!submitButton || !form.checkValidity()) return;

            submitButton.classList.add("is-submitting");
            submitButton.setAttribute("aria-disabled", "true");
            submitButton.innerHTML = "Enviando <span aria-hidden='true'>...</span>";
        });
    });

    const formatPhone = (value) => {
        const digits = value.replace(/\D/g, "").slice(0, 11);
        if (digits.length <= 2) return digits;
        if (digits.length <= 7) return `(${digits.slice(0, 2)}) ${digits.slice(2)}`;
        return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`;
    };

    document.querySelectorAll("input[type='tel']").forEach((phoneInput) => {
        phoneInput.setAttribute("inputmode", "numeric");
        phoneInput.setAttribute("maxlength", "15");
        phoneInput.addEventListener("input", () => {
            phoneInput.value = formatPhone(phoneInput.value);
        });
        phoneInput.form.addEventListener("submit", () => {
            phoneInput.value = phoneInput.value.replace(/\D/g, "");
        });
    });

    const modal = document.querySelector("#request-modal");
    const modalForm = document.querySelector("#request-update-form");

    if (modal && modalForm) {
        const closeModal = () => {
            modal.classList.remove("is-open");
            modal.setAttribute("aria-hidden", "true");
        };

        document.querySelectorAll(".approve-button").forEach((button) => {
            button.addEventListener("click", () => {
                document.querySelector("#modal-title").textContent = `Pedido de ${button.dataset.requester}`;
                document.querySelector("#modal-material").textContent = button.dataset.material;
                document.querySelector("#modal-quantity").textContent = button.dataset.quantity;
                document.querySelector("#modal-work").textContent = button.dataset.work;
                document.querySelector("#modal-requester").textContent = button.dataset.requester;
                document.querySelector("#modal-date").textContent = button.dataset.date;
                modalForm.action = `/requisicao/${button.dataset.requestId}/atualizar`;
                modal.classList.add("is-open");
                modal.setAttribute("aria-hidden", "false");
                document.querySelector("#modal-status").focus();
            });
        });

        document.querySelector(".modal-close").addEventListener("click", closeModal);
        document.querySelector(".modal-cancel").addEventListener("click", closeModal);
        modal.addEventListener("click", (event) => {
            if (event.target === modal) closeModal();
        });
        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape" && modal.classList.contains("is-open")) closeModal();
        });
    }
});