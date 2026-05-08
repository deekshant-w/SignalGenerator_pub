let SHAPES_NANOPORE_VERTICAL_LINE_STYLE = {
  color: 'red',
  width: 0,
  dash: 'dash'
};
let PLOTLY_PORE_SHAPE_ID = 'poreShape';
let PLOTLY_PORE_SHAPE_INFINITY = 100;

// Horizontal padding at which the pore top is drawn
let PLOTLY_PORE_SHAPE_Y = 0;

// Maximum width a component can have to pass through the nanopore
var widthInNanoporeForThingsToPass = -1;
var poreDetailHolder = {};
let PORE_SHAPE_STYLE = {
  line: {
      color: 'rgba(0, 0, 0, 0.8)',
      width: 1,
  },
  fillcolor: 'rgba(0, 0, 0, 0.2)'
};

// Bool that tells whether the pore details are valid or not
var poreDetailsValid = true;

// UNUSED
function updateVerticalLines(nanoporeRadius){
  // Update the vertical lines and the nanopore rectangle to reflect the new nanopore radius.
  // Delete existing vertical lines 
  let shapes = document.getElementById(SHAPES_DIV_ID).layout.shapes || [];
  shapes = shapes.filter(shape => shape.id !== 'leftVerticalLine' && shape.id !== 'rightVerticalLine');
  // Add new vertical lines
  shapes.push({
      type: 'rect',
      xref: 'x',
      yref: 'paper',
      x0: -nanoporeRadius,
      y0: 0,
      x1: -nanoporeRadius,
      y1: 1,
      line: SHAPES_NANOPORE_VERTICAL_LINE_STYLE,
      id: 'leftVerticalLine'
  });
  shapes.push({
      type: 'rect',
      xref: 'x',
      yref: 'paper',
      x0: nanoporeRadius,
      y0: 0,
      x1: nanoporeRadius,
      y1: 1,
      line: SHAPES_NANOPORE_VERTICAL_LINE_STYLE,
      id: 'rightVerticalLine'
  });

  // Delete existing nanopore rectangle
  shapes = shapes.filter(shape => shape.id !== 'nanoporeRectangle');

  // Update the layout
  Plotly.relayout(SHAPES_DIV_ID, {
      shapes: shapes,
      'xaxis.range': [-nanoporeRadius-SHAPES_HORIONTAL_PADDING, nanoporeRadius+SHAPES_HORIONTAL_PADDING]
  });
}

function deletePoreFromPlot_AndReturnRemainingShapes(){
  let shapes = document.getElementById(SHAPES_DIV_ID).layout.shapes || [];
  shapes = shapes.filter(shape => shape.id !== PLOTLY_PORE_SHAPE_ID);
  return shapes;
}

function plotPore_simple(poreRadius,height=0.3){
  let shapes = deletePoreFromPlot_AndReturnRemainingShapes();
  // Left and right rectangles for 2D nanopore
  shapes.push({
    type: 'rect',
    x0: -PLOTLY_PORE_SHAPE_INFINITY,
    y0: PLOTLY_PORE_SHAPE_Y,
    x1: -poreRadius,
    y1: PLOTLY_PORE_SHAPE_Y-height,
    line: PORE_SHAPE_STYLE.line,
    fillcolor: PORE_SHAPE_STYLE.fillcolor,
    id: PLOTLY_PORE_SHAPE_ID
  });
  shapes.push({
    type: 'rect',
    x0: poreRadius,
    y0: PLOTLY_PORE_SHAPE_Y,
    x1: PLOTLY_PORE_SHAPE_INFINITY,
    y1: PLOTLY_PORE_SHAPE_Y-height,
    line: PORE_SHAPE_STYLE.line,
    fillcolor: PORE_SHAPE_STYLE.fillcolor,
    id: PLOTLY_PORE_SHAPE_ID
  });
  console.log(shapes);
  // Update the layout
  Plotly.relayout(SHAPES_DIV_ID, {
    shapes: shapes,
    'xaxis.range': [-poreRadius-SHAPES_HORIONTAL_PADDING, poreRadius+SHAPES_HORIONTAL_PADDING]
  });
  return true;
}

function plotPore_conical(data){
  let shapes = deletePoreFromPlot_AndReturnRemainingShapes();
  let r1 = data['nanoporeRadius1_conical'];
  let r2 = data['nanoporeRadius2_conical'];
  let length = data['nanoporeLength_conical'];
  // Conical pore shape
  shapes.push({
    type: 'path',
    path: `M ${-PLOTLY_PORE_SHAPE_INFINITY} ${PLOTLY_PORE_SHAPE_Y} H ${-r2} L ${-r1} ${PLOTLY_PORE_SHAPE_Y-length} H ${-PLOTLY_PORE_SHAPE_INFINITY} Z`, 
    line: PORE_SHAPE_STYLE.line,
    fillcolor: PORE_SHAPE_STYLE.fillcolor,
    id: PLOTLY_PORE_SHAPE_ID
  });
  shapes.push({
    type: 'path',
    path: `M ${PLOTLY_PORE_SHAPE_INFINITY} ${PLOTLY_PORE_SHAPE_Y} H ${r2} L ${r1} ${PLOTLY_PORE_SHAPE_Y-length} H ${PLOTLY_PORE_SHAPE_INFINITY} Z`,
    line: PORE_SHAPE_STYLE.line,
    fillcolor: PORE_SHAPE_STYLE.fillcolor,
    id: PLOTLY_PORE_SHAPE_ID
  });
  console.log(shapes);
  // Update the layout
  let maxRadius = Math.max(r1,r2);
  Plotly.relayout(SHAPES_DIV_ID, {
    shapes: shapes,
    'xaxis.range': [-maxRadius-SHAPES_HORIONTAL_PADDING, maxRadius+SHAPES_HORIONTAL_PADDING]
  });
  return true;
}

function plotPore_hyperbolic(data){
  let shapes = deletePoreFromPlot_AndReturnRemainingShapes();
  let rIn = data['nanoporeRadiusIn_hyperbolic'];
  let rOut = data['nanoporeRadiusOut_hyperbolic'];
  let length = data['nanoporeLength_hyperbolic'];
  let cX = 2*rIn - rOut; // x coordinate of center of hyperbola
  let cY = length/2; // y coordinate of center of hyperbola
  // Hyperbolic pore shape
  shapes.push({
    type: 'path',
    path: `M ${-PLOTLY_PORE_SHAPE_INFINITY} ${PLOTLY_PORE_SHAPE_Y} 
    H ${-rOut} 
    Q ${-cX} ${-cY}, ${-rOut} ${-length} 
    H ${-PLOTLY_PORE_SHAPE_INFINITY} 
    Z`,
    line: PORE_SHAPE_STYLE.line,
    fillcolor: PORE_SHAPE_STYLE.fillcolor,
    id: PLOTLY_PORE_SHAPE_ID
  });
  shapes.push({
    type: 'path',
    path: `M ${PLOTLY_PORE_SHAPE_INFINITY} ${PLOTLY_PORE_SHAPE_Y}
    H ${rOut}
    Q ${cX} ${-cY}, ${rOut} ${-length}
    H ${PLOTLY_PORE_SHAPE_INFINITY}
    Z`,
    line: PORE_SHAPE_STYLE.line,
    fillcolor: PORE_SHAPE_STYLE.fillcolor,
    id: PLOTLY_PORE_SHAPE_ID
  });

  console.log(shapes);
  // Update the layout
  let maxRadius = Math.max(rIn,rOut);
  Plotly.relayout(SHAPES_DIV_ID, {
    shapes: shapes,
    'xaxis.range': [-maxRadius-SHAPES_HORIONTAL_PADDING, maxRadius+SHAPES_HORIONTAL_PADDING]
  });
  return true;
}

function getSelectedPoreType(){
  return document.getElementById("poreTypeSelector").value;
}

function getPoreDetails(){
  let data = document.getElementById("poreDetailsContainer");
  data = new FormData(data);
  return data;
}

function clearPoreInputFields(){
  let fieldsHolderDiv = Array.from(document.getElementById("poreDetailsContainer").children);
  for(let children of fieldsHolderDiv){
    if(children.hasAttribute("data-pore-resolution-DONOT-DELETE")){
      continue;
    }
    children.remove();
  }
}

function addPoreInputFields(divId){
  /**
   * Add pore input fields to the poreDetailsContainer div from the hidden divs along with event listeners and container id.
   * @param {string} divId - id of the div containing the pore details to be added
   * @returns {boolean} : status - Whether addition was successful
   */
  let fieldsHolderDiv = document.getElementById("poreDetailsContainer");
  let hiddenFields = document.getElementById(divId);
  if (!hiddenFields) {
    return false;
  }
  hiddenFields = hiddenFields.children;
  for(let i=hiddenFields.length-1;i>=0;i--){
    let children = hiddenFields[i].cloneNode(true);
    children.querySelector("input").addEventListener('change',poreDetailChange)
    fieldsHolderDiv.prepend(children);
  }
  return true;
}

function _poreDetailChangeLogic_numParser(val){
  if(!val){
    return [false, "Invalid Value"];
  }
  val = parseFloat(val);
  if(isNaN(val)){
    return [false, "Not a number!"];
  }
  if (val<=0){
    return [false, "Value is <= 0"];
  }
  return [true, val];
}

function validatePoreData(selectedPoreType,data){
  /**
   * Validate pore details
   * @param {FormData} data - Data retrieved from details form
   * @param {string} selectedPoreType - Select value from poreTypeSelector(id) 
   * @returns {boolean} : status - Whether validation was successful
   * @returns {object} : validatedData dictionary with only the correct and validated data
   * @returns {float} : minWidth - widthInNanoporeForThingsToPass
   */
  let status,cleanValue;
  let validatedData = {};

  let resolution = data.get("signalResolution");
  [status, resolution] = _poreDetailChangeLogic_numParser(resolution);
  if(status===false){
    showToast("Error: Resolution: "+resolution,"warning");
  }
  validatedData['signalResolution'] = resolution;

  if (selectedPoreType=="2dPore"){
    [status,cleanValue] = _poreDetailChangeLogic_numParser(data.get("nanoporeRadius_2D"));
    if(status===false){
      showToast("Error: Nanopore Radius: "+cleanValue,"warning");
      return [false,validatedData,-1];
    }
    validatedData['nanoporeRadius_2D'] = cleanValue;

    return [true,validatedData,validatedData['nanoporeRadius_2D']];
  } 
  else if (selectedPoreType=="CylindricalPore"){
    [status,cleanValue] = _poreDetailChangeLogic_numParser(data.get("nanoporeRadius_cylindrical"));
    if(status===false){
      showToast("Error: Nanopore Radius: "+cleanValue,"warning");
      return [false,validatedData,-1];
    }
    validatedData['nanoporeRadius_cylindrical'] = cleanValue;

    [status,cleanValue] = _poreDetailChangeLogic_numParser(data.get("nanoporeLength_cylindrical"));
    if(status===false){
      showToast("Error: Nanopore Length: "+cleanValue,"warning");
      return [false,validatedData,-1];
    }
    validatedData['nanoporeLength_cylindrical'] = cleanValue;

    return [true,validatedData,validatedData['nanoporeRadius_cylindrical']];
  }
  else if (selectedPoreType=="ConicalPore"){
    [status,cleanValue] = _poreDetailChangeLogic_numParser(data.get("nanoporeRadius1_conical"));
    if(status===false){
      showToast("Error: Nanopore Radius 1: "+cleanValue,"warning");
      return [false,validatedData,-1];
    }
    validatedData['nanoporeRadius1_conical'] = cleanValue;
    [status,cleanValue] = _poreDetailChangeLogic_numParser(data.get("nanoporeRadius2_conical"));
    if(status===false){
      showToast("Error: Nanopore Radius 2: "+cleanValue,"warning");
      return [false,validatedData,-1];
    }
    validatedData['nanoporeRadius2_conical'] = cleanValue;
    [status,cleanValue] = _poreDetailChangeLogic_numParser(data.get("nanoporeLength_conical"));
    if(status===false){
      showToast("Error: Nanopore Length: "+cleanValue,"warning");
      return [false,validatedData,-1];
    }
    validatedData['nanoporeLength_conical'] = cleanValue;
    // Custom logic for conical pore
    if (validatedData['nanoporeRadius1_conical'] === validatedData['nanoporeRadius2_conical']){
      showToast("Error: Nanopore Radius 1 and 2 cannot be the same for a conical pore.","warning");
      return [false,validatedData,-1];
    }
    let minWidth = Math.min(validatedData['nanoporeRadius1_conical'],validatedData['nanoporeRadius2_conical']);
    return [true,validatedData,minWidth];
  }
  else if (selectedPoreType=="HyperbolicPore"){
    [status,cleanValue] = _poreDetailChangeLogic_numParser(data.get("nanoporeRadiusIn_hyperbolic"));
    if(status===false){
      showToast("Error: Nanopore In-Radius: "+cleanValue,"warning");
      return [false,validatedData,-1];
    }
    validatedData['nanoporeRadiusIn_hyperbolic'] = cleanValue;
    [status,cleanValue] = _poreDetailChangeLogic_numParser(data.get("nanoporeRadiusOut_hyperbolic"));
    if(status===false){
      showToast("Error: Nanopore Out-Radius: "+cleanValue,"warning");
      return [false,validatedData,-1];
    }
    validatedData['nanoporeRadiusOut_hyperbolic'] = cleanValue;
    [status,cleanValue] = _poreDetailChangeLogic_numParser(data.get("nanoporeLength_hyperbolic"));
    if(status===false){
      showToast("Error: Nanopore Length: "+cleanValue,"warning");
      return [false,validatedData,-1];
    }
    validatedData['nanoporeLength_hyperbolic'] = cleanValue;
    // Custom logic for hyperbolic pore
    if (validatedData['nanoporeRadiusIn_hyperbolic'] >= validatedData['nanoporeRadiusOut_hyperbolic']){
      showToast("Error: Nanopore Out-Radius must be greater than In-Radius for a hyperbolic pore.","warning");
      return [false,validatedData,-1];
    }
    let minWidth = Math.min(validatedData['nanoporeRadiusIn_hyperbolic'],validatedData['nanoporeRadiusOut_hyperbolic']);
    return [true,validatedData,minWidth];
  }
  else {
    showToast("Error: Invalid pore type!!!","warning");
    return [false,validatedData,-1];
  }
  alert("Unreachable code! validatedData");
  throw new Error("Unreachable code! validatedData"); 
}

function drawPoreShape(selectedPoreType,data){
  /**
   * Draw pore
   * @param {string} selectedPoreType - Select value from poreTypeSelector(id) 
   * @param {dict} data - Validated data assume everything is OK and all vars available.
   * @returns {boolean} : status - Whether drawing was successful
   */
  if (selectedPoreType=="2dPore"){
    return plotPore_simple(data['nanoporeRadius_2D']);
  } 
  else if (selectedPoreType=="CylindricalPore"){
    return plotPore_simple(data['nanoporeRadius_cylindrical'],data['nanoporeLength_cylindrical']);
  }
  else if (selectedPoreType=="ConicalPore"){
    return plotPore_conical(data);
  }
  else if (selectedPoreType=="HyperbolicPore"){
    return plotPore_hyperbolic(data);
  }
  else {
    showToast("Error: Invalid pore type! drawPoreShape","warning");
    return false
  }
}

function poreDetailChangeLogic(selectedPoreType){
  /**
   * Logic to be executed when pore details are changed
   */
  console.log("Pore detail change logic triggered for ",selectedPoreType);
  // Get Inputs
  let data = getPoreDetails()
  // Validate Pore details (raise errors inside the function)
  let status, minWidth;
  [status,data,minWidth] = validatePoreData(selectedPoreType,data);
  if(status===false){
    poreDetailsValid = false;
    Plotly.relayout(SHAPES_DIV_ID, {shapes: deletePoreFromPlot_AndReturnRemainingShapes()});
    return;
  }
  poreDetailsValid = true;
  console.log("Validated pore data: ",data);
  // If everything is OK, draw the pore shape
  // Make changes to shapes plot
  if (drawPoreShape(selectedPoreType,data)===false){
    return
  }
  // Set min width
  widthInNanoporeForThingsToPass = minWidth;
  poreDetailHolder = data;
  poreDetailHolder['selectedPoreType'] = selectedPoreType;
  console.log(widthInNanoporeForThingsToPass);
}

function poreDetailChange(){
  /**
   * Event listener for pore detail change
   * It is applied to all pore detail input fields dynamically inside addPoreInputFields function.
   */
  console.log("Pore detail change event triggered");
  // Get selected pore type
  let selectedPoreType = getSelectedPoreType(); 
  poreDetailChangeLogic(selectedPoreType);
}

function poreChangeLogic(){
  /**
   * Logic to be executed when pore type is changed
   */
  let selectedPoreType = getSelectedPoreType();
  // Clear Pore detail fields
  clearPoreInputFields();
  // Add new fields
  if (!addPoreInputFields(selectedPoreType+"Details")){
    alert("Invalid pore type!");
    return;
  }
  poreDetailChangeLogic(selectedPoreType);

  // Update the vertical lines| If minShapeSize is 0, raise an error
  // if (minShapeSize <= 0){
  //   alert("minShapeSize is not set."+`minShapeSize: ${minShapeSize}`+`selectedPoreType: ${selectedPoreType}`);
  //   return;
  // }
  // updateVerticalLines(minShapeSize);
}
// On Page Load
poreChangeLogic();
// On pore type change, trigger the pore logic
document.getElementById("poreTypeSelector").addEventListener("change", poreChangeLogic);