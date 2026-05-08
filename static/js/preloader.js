function getListAndNewImages() {
    var bases = [import_listCard, import_newCard];
    var shapes = ["sphere", "ellipsoid", "cylinder", "cone", "wedge"];
    var images = [];
    for (var i = 0; i < bases.length; i++) {
        for (var j = 0; j < shapes.length; j++) {
            images.push(bases[i] + shapes[j] + ".png");
        }
    }
    return images;
}
 
window.addEventListener('load', function () {
    // Array of image URLs that you expect to load dynamically
    var imagesToPreload = getListAndNewImages();
    imagesToPreload.forEach(function (imageUrl) {
        var img = new Image();
        img.src = imageUrl;  // This starts the downloading of the image
        img.onload = function () {
            // console.log('Preloaded:', imageUrl);  // Log for debugging
        };
    });
});