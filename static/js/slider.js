let slideIndex = 0;

function showSlides() {
    let i;
    let dots = document.getElementsByClassName("slide-indicator");
    let counter = document.getElementsByClassName("counter");
    let slides = document.getElementsByClassName("slide");

    for (i = 0; i < slides.length; i++) {
        slides[i].style.display = "none";
    }

    if (slideIndex >= slides.length) slideIndex = 0;
    if (slideIndex < 0) slideIndex = slides.length - 1;

    for (i = 0; i < dots.length; i++) {
        dots[i].className = dots[i].className.replace(" active-slide", ""); 
    }

    slides[slideIndex].style.display = "block";
    counter[slideIndex].innerHTML = `<span style="color: var(--primary-color); font-weight: bold;">${slideIndex + 1}</span> / ${slides.length}`;
    dots[slideIndex].className += " active-slide";

}

// document.addEventListener("keydown", function (event) {
//     if (event.key === "ArrowRight") {
//         slideIndex++;
//         showSlides();
//     } else if (event.key === "ArrowLeft") {
//         slideIndex--;
//         showSlides();
//     }
// });


document.getElementById("slide-prev").addEventListener("click", () => {
    slideIndex--;
    showSlides();
});

document.getElementById("slide-next").addEventListener("click", () => {
    slideIndex++;
    showSlides();
});

function startAutoPlay() {
    autoPlay = setInterval(() => {
        slideIndex++;
        showSlides(true);
    }, 5000);
}

function stopAutoPlay() {
    clearInterval(autoPlay);
}

 // SWIPE SUPPORT for Mobile
 let touchStartX = 0;
 let touchEndX = 0;
 let slideshow = document.querySelector(".slideshow-container");

 slideshow.addEventListener("touchstart", function (event) {
     touchStartX = event.touches[0].clientX;
 });

 slideshow.addEventListener("touchend", function (event) {
     touchEndX = event.changedTouches[0].clientX;
     handleSwipe();
 });

 function handleSwipe() {
     let swipeDistance = touchStartX - touchEndX;
     if (swipeDistance > 50) { 
         slideIndex++;
         showSlides();
     } else if (swipeDistance < -50) {
         slideIndex--;
         showSlides();
     }
 }

// Pause slideshow on mouse over
slideshow.addEventListener("mouseover", stopAutoPlay);
slideshow.addEventListener("mouseout", startAutoPlay);

showSlides();
startAutoPlay();



