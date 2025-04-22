// document.addEventListener("DOMContentLoaded", () => {
//     const categoryItems = document.querySelectorAll(".category-item");

//     categoryItems.forEach(item => {
//         const submenu = item.querySelector(".subcategory-menu");
//         if (!submenu) return;

//         item.addEventListener("mouseenter", () => {
//             const rect = item.getBoundingClientRect();
//             submenu.style.top = `${rect.bottom}px`; // Set top position below the parent
//             submenu.style.left = `${rect.left}px`; // Align to parent left
//         });
//     });
// });
