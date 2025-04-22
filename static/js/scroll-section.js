document.addEventListener("DOMContentLoaded", () => {
    const containers = document.querySelectorAll(".scrolling-container");
    const leftBtns = document.querySelectorAll(".scroll-left-btn");
    const rightBtns = document.querySelectorAll(".scroll-right-btn");

    if (containers.length === 0 || leftBtns.length === 0 || rightBtns.length === 0) return;

    containers.forEach((container, index) => {
        const leftBtn = leftBtns[index];
        const rightBtn = rightBtns[index];

        if (!leftBtn || !rightBtn) return;

        // Track active container on hover
        container.addEventListener("mouseenter", () => {
            activeContainer = container;
        });

        container.addEventListener("mouseleave", () => {
            activeContainer = null;
        });

        // Check scroll position and toggle buttons
        const updateButtonVisibility = () => {
            const { scrollLeft, scrollWidth, clientWidth } = container;
            leftBtn.classList.toggle("hidden", scrollLeft === 0);
            rightBtn.classList.toggle("hidden", scrollLeft >= scrollWidth - clientWidth - 1);
        };

        // Scroll left
        leftBtn.addEventListener("click", () => {
            container.scrollBy({ left: -300, behavior: "smooth" });
        });

        // Scroll right
        rightBtn.addEventListener("click", () => {
            container.scrollBy({ left: 300, behavior: "smooth" });
        });

        // Update on scroll
        container.addEventListener("scroll", updateButtonVisibility);

        // Initial check
        updateButtonVisibility();
    });

    // Global keyboard arrow key scrolling for the active container
    document.addEventListener("keydown", (event) => {
        if (!activeContainer) return; // Only scroll if a container is hovered

        if (event.key === "ArrowLeft") {
            activeContainer.scrollBy({ left: -300, behavior: "smooth" });
        } else if (event.key === "ArrowRight") {
            activeContainer.scrollBy({ left: 300, behavior: "smooth" });
        }
    });
});
