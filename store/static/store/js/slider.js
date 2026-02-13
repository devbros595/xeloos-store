const slides = document.getElementById("slides");
const images = new Array(
  "img-slide/slide1.jpg",
  "img-slide/slide2.jpg",
  "img-slide/slide3.jpg",
  "img-slide/slide4.jpg",
  "img-slide/slide5.png"
);
const len = images.length;
let i = 0;
function slider() {
  if (i > len - 1) {
    i = 0;
  }
  slides.src = images[i];
  i++;
  setTimeout( 'slider()', 10000);
}
