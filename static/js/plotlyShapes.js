let INITIAL_NANOPORE_RADIUS = 1.5;
let SHAPES_HORIONTAL_PADDING = 1;
let SHAPES_RUNNING_Y_INITIAL = 1;
var SHAPES_RUNNING_Y = SHAPES_RUNNING_Y_INITIAL;
let SKIP_PLOTLY_UPDATE = false;
let SHAPES_LINE_STYLE = {
    color: 'rgb(0, 0, 255)',
    width: 1
};
let SHAPES_FILL_COLOR = (function* () {
    while (true) {
        yield 'rgba(0, 0, 255, 0.5)'; // Blue
        yield 'rgba(255, 0, 0, 0.3)'; // Red
    }
})();
let SHAPES_LAYOUT = {
    dragmode: 'pan',
    margin: {
        l: 0,
        r: 0,
        b: 0,
        t: 0
    },
    xaxis: {
        range: [-INITIAL_NANOPORE_RADIUS-SHAPES_HORIONTAL_PADDING, INITIAL_NANOPORE_RADIUS+SHAPES_HORIONTAL_PADDING],
        showgrid: false,
        zeroline: false,
    },
    yaxis: {
        range: [-INITIAL_NANOPORE_RADIUS, 2*INITIAL_NANOPORE_RADIUS],
        scaleanchor: 'x', // Lock the aspect ratio relative to the x-axis
        scaleratio: 1,    // Ensure that the units are equal
        showgrid: false,
        zeroline: false,
    },
    // Aspect ratio testing
    // shapes: [{type: 'circle',x0: -1,y0: -1,x1: 1,y1: 1,}],
    aspectratio: {x: 1, y: 1},
    hovermode: false,
    showlegend: false
};
let SHAPES_CONFIG = {
    scrollZoom: false,  // Disables scrolling to zoom
    doubleClick: false, // Disables double click to zoom
    displaylogo: false, // Hides the plotly logo
    modeBarButtonsToRemove: [
        'pan2d', 'zoom2d', 'lasso2d', 'drawclosedpath', 'autoScale2d', 'hoverClosestCartesian', 'hoverCompareCartesian', 'toggleSpikelines'
    ],
    modeBarButtonsToAdd: [{
        name: 'Remake',
        icon: Plotly.Icons.undo,
        click: function(gd) {
            // Remake the shapes
            showToast("Remaking shapes... Please wait as this may take some time.", "info");
            // No matter what SKIP_PLOTLY_UPDATE is, it will be updated
            remakeShapesPlotly(false);
            showToast("Shapes remade successfully!", "success");
        }
    }],
    displayModeBar: true
};

Plotly.newPlot(SHAPES_DIV_ID, [], SHAPES_LAYOUT, SHAPES_CONFIG);

function projectionCylinder(r,h,y){
    // Plotted Upwards
    // -----
    // |   |
    // *--- <- y
    let shape = {
        type: 'rect',
        x0: -r,
        y0: y,
        x1: r,
        y1: y+h,
        line: SHAPES_LINE_STYLE,
        fillcolor: SHAPES_FILL_COLOR.next().value,
    };
    return [shape];
}

function projectionSphere(r,y){
    let shape = {
        type: 'circle',
        x0: -r,
        y0: y,
        x1: r,
        y1: y+(2*r),
        line: SHAPES_LINE_STYLE,
        fillcolor: SHAPES_FILL_COLOR.next().value,
    };
    return [shape];
}

function projectionEllipsoid(a,b,y){
    let shape = {
        type: 'circle',
        x0: -a,
        y0: y,
        x1: a,
        y1: y+(b*2),
        line: SHAPES_LINE_STYLE,
        fillcolor: SHAPES_FILL_COLOR.next().value,
    };
    return [shape];
}

function projectionCone(r1,r2,h,y){
    // as a trapezoid
    let shape = {
        type: 'path',
        path: `M ${-r1} ${y} H ${r1} L ${r2} ${y+h} H ${-r2} Z`,
        line: SHAPES_LINE_STYLE,
        fillcolor: SHAPES_FILL_COLOR.next().value,
    };
    return [shape];
}

function projectionWedge(r1,r2,h,theta,y){
    // as 2 rectangles
    if (theta < 0 || theta > 2*Math.PI){
        alert("Theta must be between 0 and 2*pi");
        return;
    }
    // 2 rectangles | left and right to represent width 2 adjoint regions of the wedge
    // Full width of the wedge is r1+r2
    let w = (r1+r2);
    let right = ((Math.tanh((theta - Math.PI)/2) + 1)/2)*w;
    // If during calculation r is greater than w, then set r to w
    if (right > w){
        right = w;
    }
    // If during calculation r is less than 0, then set r to 0
    else if (right < 0){
        right = 0;
    }
    fillcolor = SHAPES_FILL_COLOR.next().value
    let left = w - right;
    let leftShape = {
        type: 'rect',
        x0: -w/2,
        y0: y,
        x1: (-w/2)+left,
        y1: y+h,
        line: SHAPES_LINE_STYLE,
        fillcolor: fillcolor,
    };
    fillcolor = fillcolor.replace(/[^,]+(?=\))/, 0.8);
    let rightShape = {
        type: 'rect',
        x0: (-w/2)+left,
        y0: y,
        x1: w/2,
        y1: y+h,
        line: SHAPES_LINE_STYLE,
        fillcolor: fillcolor,
    };
    return [leftShape, rightShape];
}

function generateShapesForPlotly(index=-1){
    // Generate plotly shapes dictionary for the component at index
    let component = _ComponentList[index];
    let shapes = [];
    if (component.shape === 'cylinder'){
        shapes = projectionCylinder(component.data.cylinderRadius, component.data.cylinderLength, SHAPES_RUNNING_Y);
    } else if (component.shape === 'sphere'){
        shapes = projectionSphere(component.data.sphereRadius, SHAPES_RUNNING_Y);
    } else if (component.shape === 'ellipsoid'){
        shapes = projectionEllipsoid(component.data.ellipsoidAxisA, component.data.ellipsoidAxisB, SHAPES_RUNNING_Y);
    } else if (component.shape === 'cone'){
        shapes = projectionCone(component.data.coneRadius1, component.data.coneRadius2, component.data.coneLength, SHAPES_RUNNING_Y);
    } else if (component.shape === 'wedge'){
        shapes = projectionWedge(component.data.wedgeRadius1, component.data.wedgeRadius2, component.data.wedgeLength, component.data.wedgeAngle, SHAPES_RUNNING_Y);
    } else {
        showToast("Invalid shape while displaying shapes!", "error");
        return;
    }
    console.log("Shapes for index: ", index);
    console.log(shapes);
    return shapes;
}

function updateShapePlotly(shapes, update=true){
    // Update the plotly shapes
    let fig = document.getElementById(SHAPES_DIV_ID);
    if (update){
        fig.layout.shapes = fig.layout.shapes.concat(shapes);
    } else {
        fig.layout.shapes = shapes;
    }
    // Update the layout
    Plotly.relayout(SHAPES_DIV_ID, fig.layout);
}

function update_SHAPES_RUNNING_Y(shape, data){
    if (shape === 'cylinder'){
        SHAPES_RUNNING_Y += data.cylinderLength;
    } else if (shape === 'sphere'){
        SHAPES_RUNNING_Y += 2*data.sphereRadius;
    } else if (shape === 'ellipsoid'){
        SHAPES_RUNNING_Y += 2*data.ellipsoidAxisB;
    } else if (shape === 'cone'){
        SHAPES_RUNNING_Y += data.coneLength;
    } else if (shape === 'wedge'){
        SHAPES_RUNNING_Y += data.wedgeLength;
    } else {
        showToast("Invalid shape while displaying shapes!", "error");
        return;
    }
}

function addShapePlotly(index=-1){
    // Add the shape at index to the plotly shapes 
    let shapes = generateShapesForPlotly(index);
    updateShapePlotly(shapes);
    let component = _ComponentList[index];
    update_SHAPES_RUNNING_Y(component.shape, component.data);
}
// Dynamically Load poreLogic.js
let _poreLogicScript = document.createElement('script');
_poreLogicScript.src = poreLogicFile;
document.head.appendChild(_poreLogicScript);

function remakeShapesPlotly(skip=SKIP_PLOTLY_UPDATE){
    // If plotly is lagging, add a skip parameter to skip the update
    // Normal remake requests will be controled by SKIP_PLOTLY_UPDATE
    // Force remake plot using the button on plotly will always remake the shapes
    if(skip){
        return;
    }
    // Remake the plotly shapes
    SHAPES_RUNNING_Y = SHAPES_RUNNING_Y_INITIAL;
    let shapes = [];
    for(let i=0; i<_ComponentList.length; i++){
        shapes = shapes.concat(generateShapesForPlotly(i));
        update_SHAPES_RUNNING_Y(_ComponentList[i].shape, _ComponentList[i].data);
    }
    updateShapePlotly(shapes, update=false);
    // Update pore logic
    poreDetailChange();
}
