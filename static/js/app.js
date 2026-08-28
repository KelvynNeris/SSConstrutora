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

    if (document.body.dataset.approvalPoll === "true") {
        const checkApproval = async () => {
            try {
                const response = await fetch("/api/cadastro/status", { headers: { Accept: "application/json" } });
                if (response.ok && (await response.json()).aprovado) {
                    window.location.href = "/login";
                }
            } catch (error) {
            }
        };
        checkApproval();
        window.setInterval(checkApproval, 5000);
    }

    const refreshInterval = Number(document.body.dataset.autoRefresh);
    if (refreshInterval > 0) {
        window.setInterval(() => window.location.reload(), refreshInterval);
    }

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

    const workModal = document.querySelector("#work-modal");
    if (workModal) {
        const closeWorkModal = () => {
            workModal.classList.remove("is-open");
            workModal.setAttribute("aria-hidden", "true");
        };

        document.querySelectorAll("[data-open-work-modal]").forEach((button) => {
            button.addEventListener("click", () => {
                workModal.classList.add("is-open");
                workModal.setAttribute("aria-hidden", "false");
                document.querySelector("#work-name").focus();
            });
        });
        document.querySelectorAll("[data-close-work-modal]").forEach((button) => {
            button.addEventListener("click", closeWorkModal);
        });
        workModal.addEventListener("click", (event) => {
            if (event.target === workModal) closeWorkModal();
        });
        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape" && workModal.classList.contains("is-open")) closeWorkModal();
        });
    }

    const logoutModal = document.querySelector("#logout-modal");
    if (logoutModal) {
        const closeLogoutModal = () => {
            logoutModal.classList.remove("is-open");
            logoutModal.setAttribute("aria-hidden", "true");
        };

        document.querySelectorAll("[data-open-logout-modal]").forEach((button) => {
            button.addEventListener("click", (event) => {
                event.preventDefault();
                logoutModal.classList.add("is-open");
                logoutModal.setAttribute("aria-hidden", "false");
            });
        });

        document.querySelectorAll("[data-close-logout-modal]").forEach((button) => {
            button.addEventListener("click", closeLogoutModal);
        });

        logoutModal.addEventListener("click", (event) => {
            if (event.target === logoutModal) closeLogoutModal();
        });

        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape" && logoutModal.classList.contains("is-open")) closeLogoutModal();
        });
    }
});