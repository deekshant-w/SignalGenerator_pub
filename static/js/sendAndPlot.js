const ServerURL = window.location.href;
const ROUTING_PARAM = '-_-at-_';
const postHeaders = {
  'Accept': 'application/json',
  'Content-Type': 'application/json',
}
var ORIGINAL_PLOT_HOLDER = {
  'x':[],
  'y':[]
}
var ATTENUATED_PLOT_HOLDER = {
  'x':[],
  'y':[]
}
let PLOTLY_REMAKE_ICON = {
  name: 'Remake',
  icon: Plotly.Icons.undo,
  click: function(gd) {
    Plotly.Plots.resize(gd);
    showToast("Plot remade successfully.");
  }
}
let PLOTLY_DOWNLOAD_CSV_ICON = {
  name: 'Download CSV',
  icon: Plotly.Icons.disk,
  click: function(gd) {
    let x1 = ORIGINAL_PLOT_HOLDER['x'];
    let y1 = ORIGINAL_PLOT_HOLDER['y'];
    let x2 = ATTENUATED_PLOT_HOLDER['x'];
    let y2 = ATTENUATED_PLOT_HOLDER['y'];
    let csvContent = "data:text/csv;charset=utf-8,";
    csvContent += "Distance from center to pore (nm), Gb/Go, Attenuated Signal X, Attenuated Signal Y\n";
    for(let i=0; i<Math.max(ORIGINAL_PLOT_HOLDER['x'].length, ATTENUATED_PLOT_HOLDER['x'].length); i++){
      // csvContent += `${x[i]}, ${y[i]}\n`;
      [r1,r2,r3,r4] = [
        (x1[i] !== undefined) ? x1[i] : "",
        (y1[i] !== undefined) ? y1[i] : "",
        (x2[i] !== undefined) ? x2[i] : "",
        (y2[i] !== undefined) ? y2[i] : ""
      ]
      csvContent += `${r1}, ${r2}, ${r3}, ${r4}\n`
    }
    let encodedUri = encodeURI(csvContent);
    let link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "signal_data.csv");
    document.body.appendChild(link);
    link.click();
  }
}
const PLOTTING_DIV_ID = "plottingDiv";
const PLOTTING_DIV = document.getElementById(PLOTTING_DIV_ID);
const PLOTLY_LAYOUT = {
    title: "Generated Signal",
    margin: {
        l: 60,
        r: 30,
        b: 70,
        t: 40
    },
    xaxis: {
        title: "Distance from center to pore (nm)",
    },
    yaxis: {
        title: "G<span style='font-size:0.6rem'>b</span>/G<span style='font-size:0.6rem'>o</span>",
    },
    showlegend: false,
}
const PLOTLY_CONFIG = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d'],
    modeBarButtonsToAdd: [PLOTLY_DOWNLOAD_CSV_ICON, PLOTLY_REMAKE_ICON],
}

var PLOTLY_LAYOUT_DARK_MODE = {
    title: 'Sample Data Visualization',
    plot_bgcolor: '#ff000000', // Set background color to dark grey
    paper_bgcolor: '#ff000000', // Set paper background color to a darker grey
    font: {
      color: '#ddd' // Set text color to light grey
    },
    xaxis: {
      title: 'X-axis Label',
      titlefont: {
        //color: '#ddd' // Set axis title color to light grey
      },
      gridcolor: '#444' // Set grid lines color to a lighter grey
    },
    yaxis: {
      title: 'Y-axis Label',
      titlefont: {
        //color: '#ddd' // Set axis title color to light grey
      },
      gridcolor: '#444' // Set grid lines color to a lighter grey
    }
  };

function validateComponentsWithNanoporeRadius(nanoporeRadius){
  let validationErrors = [];
  let validation = true;
  for(let i=0; i<_ComponentList.length; i++){
    let component = _ComponentList[i];
    let componentShapeName = component['shape'].toLowerCase();
    let formData = component['data'];
    switch(componentShapeName){
      case "cylinder":
        if(formData.cylinderRadius >= nanoporeRadius){
          validation = false;
          validationErrors.push(`Cylinder ${i+1} radius should be less than nanopore radius.`);
        }
        break;
      case "cone":
        if(formData.coneRadius1 >= nanoporeRadius || formData.coneRadius2 >= nanoporeRadius){
          validation = false;
          validationErrors.push(`Cone ${i+1} radius should be less than nanopore radius.`);
        }
        if(formData.coneRadius1 === formData.coneRadius2){
          validation = false;
          validationErrors.push(`Cone ${i+1} Radius 1 and Radius 2 cannot be the same.`);
        }
        let coneMinLengthValue = calculateConeMinLength(formData.coneRadius1, formData.coneRadius2, nanoporeRadius);
        if(formData.coneLength < coneMinLengthValue && validation == true){
          validation = false;
          validationErrors.push(`For closed form solution, cone length should be greater than ${coneMinLengthValue} given the input radii.`)
        }
        break;
      case "sphere":
        if(formData.sphereRadius >= nanoporeRadius){
          validation = false;
          validationErrors.push(`Sphere ${i+1} radius should be less than nanopore radius.`);
        }
        break;
      case "wedge":
        if(formData.wedgeRadius1 >= nanoporeRadius || formData.wedgeRadius2 >= nanoporeRadius){
          validation = false;
          validationErrors.push(`Wedge ${i+1} radius should be less than nanopore radius.`);
        }
        break;
      case "ellipsoid":
        if(formData.ellipsoidAxisA > nanoporeRadius){
          validation = false;
          validationErrors.push(`Ellipsoid ${i+1} axis should be less than nanopore radius.`);
        }
        break;
      default:
        validation = false;
        validationErrors.push(`Invalid component shape.`);
    }
  }
  return [validation, validationErrors];
}

  
function validateBeforeSend(){
  // Check if pore details are valid
  if(!poreDetailsValid){
    showToast("Please enter valid nanopore details.", "danger");
    return false;
  }

  // Check if nanopore radius is available and greater than 0
  let nanoporeRadius = widthInNanoporeForThingsToPass;
  if(nanoporeRadius <= 0){
    showToast("Please enter a valid nanopore radius.", "danger");
    return false;
  }

  // Check if Signal Resolution is available and greater than 0
  let signalResolution = document.getElementById("signalResolution").value;
  if(signalResolution === "" || parseFloat(signalResolution) <= 0){
    showToast("Please enter a valid signal resolution.", "danger");
    return false;
  }

  // Check if _ComponentList is not empty
  if(_ComponentList.length === 0){
    showToast("Please add components to the list.", "danger");
    return false;
  }

  // Check if all the components are valid
  for(let i=0; i<_ComponentList.length; i++){
    let component = _ComponentList[i];
    let componentShapeName = component['shape'].toLowerCase();
    let formData = component['data'];
    let [validation, validationErrors] = validateComponentBeforeAddingToList(componentShapeName, formData);
    if(!validation){
      showToast(validationErrors.join("\n"), "danger");
      return false;
    }
  }

  // Check component dimensions with nanopore radius
  let [validation, validationErrors] = validateComponentsWithNanoporeRadius(nanoporeRadius);
  let validationError = validationErrors.join("\n");
  if(!validation){
    showToast(validationError, "danger");
    return false;
  }

  return true;
}

async function sendMolecule(){
  if(!validateBeforeSend()){
    return;
  }
  let data = {}
  data['components'] = _ComponentList;
  data[ROUTING_PARAM] = "generate";
  console.log(poreDetailHolder);
  data['poreDetails'] = poreDetailHolder;
  console.log(data);
  loader.show();
  try{
    let url = ServerURL;
    // send fetch request with _ComponentList
    let response = await fetch(url, {
      method: "POST",
      headers: postHeaders,
      body: JSON.stringify(data)
    });
    console.log('response', response);
    if(!response.ok){
      let error = await response.json();
      let errorMessage;
      switch(response.status){
        case 500:
          errorMessage = "Unable to plot: "+(error.error || "Internal Server Error.");
          throw new Error(errorMessage);
        case 400:
          errorMessage = "Unable to Plot: "+(error.error || "Bad Request.");
          throw new Error(errorMessage);
        default:
          console.log(`${response.status}: ${error.error}`);
          throw new Error("Unable to send molecule.");
      }
    }
    console.log('response', response);
    // console.log(await response.text());
    let recievedData = await response.json();
    console.log(recievedData);
    plot(recievedData.x, recievedData.y);
    ORIGINAL_PLOT_HOLDER['x'] = recievedData.x;
    ORIGINAL_PLOT_HOLDER['y'] = recievedData.y;
    showToast("Signal generated successfully");
    document.getElementById("noiseBox").classList.remove("visually-hidden");
    document.getElementById("signalPlottingRow").scrollIntoView(
      {behavior: "smooth", block: "start", inline: "nearest"}
    );
  } catch(e){
    console.error(e);
    showToast(e, "danger");
  } finally{
    loader.hide();
  }
}

async function ping(){
  loader.show(); 
  let data = {}
  data[ROUTING_PARAM] = "ping";
  try{
    let url = ServerURL;
    // send fetch request with _ComponentList
    let response = await fetch(url, {
      method: "POST",
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data)
    });
    console.log('response', response);
    let recievedData = await response.json();
    console.log(recievedData);
  } catch(e){
    console.error(e);
    showToast("Unable to connect to the server.", "danger");
  } finally{
    loader.hide();
  }
}
ping();

function plot(x,y){
  // remove the visualy hidden class
  document.getElementById("signalPlottingRow").classList.remove("visually-hidden");
  // remove the existing plot
  Plotly.purge(PLOTTING_DIV);
  // plot the new data
  Plotly.newPlot(
    PLOTTING_DIV, 
    [{
      x: x, 
      y: y, 
      type: 'scatter', 
      mode: 'lines+markers',
      // mode: 'markers',
      marker: {
        color: 'black',
        size: 1
      },
      line: {
        color: 'rgba(255,0,0,0.5)',  // Line color
        width: 1,       // Line width
        dash: 'solid'   // Can be 'solid', 'dash', 'dot', etc.
      },
      hoverinfo: 'x+y'
    }], 
    PLOTLY_LAYOUT,
    PLOTLY_CONFIG
  );
  // Reset the axis (Cant be addded to PLOTLY_LAYOUT as it changes on zoom)
  Plotly.relayout(PLOTTING_DIV,{
    'xaxis.autorange': true,  // Enable autoscaling for x-axis
    'yaxis.autorange': true   // Enable autoscaling for y-axis
  });
}