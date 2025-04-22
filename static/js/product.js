document.addEventListener("DOMContentLoaded", () => {
    let thumbnails = document.querySelectorAll(".product-page-thumbnail img");
    let mainImage = document.querySelector(".product-page-image img");

    if (thumbnails.length > 0) {
        thumbnails[0].parentElement.classList.toggle('active-thumnail');
    }

    thumbnails.forEach((img) => {
        img.addEventListener("mouseover", () => {
            mainImage.src = img.src;
            thumbnails.forEach((thumb) => {
                thumb.parentElement.classList.remove('active-thumnail')
            });
            img.parentElement.classList.toggle('active-thumnail');
        });
    });



    // Scroll thumbnails
    const scrollContainer = document.querySelector(".product-page-thumbnails-container");
    const scrollLeft = document.querySelector(".product-page-thumbnail-scroll-left");
    const scrollRight = document.querySelector(".product-page-thumbnail-scroll-right");

    scrollLeft?.addEventListener("click", () => scrollContainer.scrollBy({ left: -300, behavior: "smooth" }));
    scrollRight?.addEventListener("click", () => scrollContainer.scrollBy({ left: 300, behavior: "smooth" }));

    document.addEventListener("keydown", event => {
        if (event.key === "ArrowLeft") scrollContainer.scrollBy({ left: -300, behavior: "smooth" });
        if (event.key === "ArrowRight") scrollContainer.scrollBy({ left: 300, behavior: "smooth" });
    });

    // Quantity selection
    let qty = 1;
    const stockQuantity = parseInt(document.querySelector('.stock-quantity').textContent.match(/\d+/)?.[0] || "0", 10);
    const productQuantity = document.querySelector('.quantity');
    const minusQuantity = document.querySelector('.quantity-minus');
    const plusQuantity = document.querySelector('.quantity-plus');

    const updateQuantity = () => {
        productQuantity.textContent = qty;
        minusQuantity.disabled = qty <= 1;
        plusQuantity.disabled = qty >= stockQuantity;

        minusQuantity.title = minusQuantity.disabled ? "You must have at least 1 item" : "";
        plusQuantity.title = plusQuantity.disabled ? `We have only ${stockQuantity} items in stock` : "";
    };

    plusQuantity?.addEventListener("click", () => {
        if (qty < stockQuantity) {
            qty++;
            updateQuantity();
        }
    });

    minusQuantity?.addEventListener("click", () => {
        if (qty > 1) {
            qty--;
            updateQuantity();
        }
    });

    updateQuantity();

});
