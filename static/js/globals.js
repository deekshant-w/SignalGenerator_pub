// plotlyShapes.js
const SHAPES_DIV_ID = "drawBoxDiv";

// Screen Loader
var loader = {
    show: function(){
        document.getElementById('waitingScreen').style.visibility = 'visible';
    },
    hide: function(){
        document.getElementById('waitingScreen').style.visibility = 'hidden';
    }
}