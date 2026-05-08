const attenuatedSignalLayout = JSON.parse(JSON.stringify(PLOTLY_LAYOUT))
attenuatedSignalLayout.title = "Attenuated Signal";
attenuatedSignalLayout.xaxis.title = "Time";
attenuatedSignalLayout.yaxis.title = "Current";
attenuatedSignalLayout.showlegend = true;
attenuatedSignalLayout.legend = {
  x: 1,
  y: 0.01,
  xanchor: 'right',
  yanchor: 'bottom',
  margin: 0,
}

// Attenuate signal over the server
async function attenuate(){
  let x,y,sigma,transition_time,sampling_rate,cutoff_frequency,filter_poles;
  try{
    x = ORIGINAL_PLOT_HOLDER['x'];
    y = ORIGINAL_PLOT_HOLDER['y'];
    if (x.length==0 || y.length==0){
      console.log(x);
      console.log(y);
      throw new Error("Signal unavailable to attenuate.")
    }
  } catch(e){
    console.error(e);
    console.log("PLOTTING_DIV data ",PLOTTING_DIV.data)
    showToast("No data to attenuate", "danger");
    return;
  }
  try{
    sigma = document.getElementById("sigma").value;
    sigma = parseFloat(sigma)
    if (isNaN(sigma)){
      throw "Invalid Sigma value";
    }

    transition_time = document.getElementById("transition_time").value;
    transition_time = parseFloat(transition_time);
    // Convert transition time to seconds
    transition_time /= 1000000;
    if (isNaN(transition_time) || transition_time<=0){
      throw "Transition Time is invalid";
    }

    sampling_rate = document.getElementById("sampling_rate").value;
    sampling_rate = parseFloat(sampling_rate)
    if (isNaN(sampling_rate) || sampling_rate<=0){
      throw "Sampling Rate is invalid";
    }

    cutoff_frequency = document.getElementById("cutoff_frequency").value;
    cutoff_frequency = parseFloat(cutoff_frequency);
    if (isNaN(cutoff_frequency) || cutoff_frequency<=0){
      throw "Cutoff Frequency is invalid";
    }

    filter_poles = document.getElementById("filter_poles").value;
    filter_poles = parseFloat(filter_poles)
    if (isNaN(filter_poles)){
      throw "Poles value is invalid";
    } else if (filter_poles<=0){
      throw "Poles value shouled be greater than or equal to 1."
    } else if (filter_poles>=10){
      let polesConfirmation = confirm("This might lead to unstable results. Are you sure you want to continue?");
      if (!polesConfirmation) {
        throw "Confirmation was denied."
      }
    }


  } catch(e){
    console.error(e);
    showToast(e,"danger");
    return
  }
  loader.show();
  try{
    let data = {};
    data[ROUTING_PARAM] = "attenuate";
    data['sigma'] = sigma;
    data['transition_time'] = transition_time;
    data['sampling_rate'] = sampling_rate;
    data['cutoff_frequency'] = cutoff_frequency;
    data['filter_poles'] = filter_poles;
    data['y'] = y;
    data['x_max'] = x.at(-1)
    console.log(data)
    let url = ServerURL;
    let response = await fetch(url, {
      method: "POST",
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data)
    });
    console.log(response);
    let recievedData = await response.json();
    if(response.status!=200){
      throw new Error(recievedData.error);
    }
    console.log(recievedData);
    ///////////////////
    Plotly.purge(PLOTTING_DIV);
    Plotly.newPlot(
      PLOTTING_DIV, 
      [
        {
          x: recievedData.x_new, 
          y: recievedData.y, 
          type: 'scatter', 
          mode: 'lines+markers',
          // mode: 'markers',
          marker: {
            color: 'rgba(0, 76, 255, 0.9)',
            size: 1
          },
          line: {
            color: 'rgba(0, 204, 255, 0.9)',  // Line color
            width: 1,       // Line width
            dash: 'solid'   // Can be 'solid', 'dash', 'dot', etc.
          },
          hoverinfo: 'x+y',
          name: 'Attenuated'
        },
        {
          x: recievedData.x_old, 
          y: y, // ORIGINAL_PLOT_HOLDER['y']
          type: 'scatter', 
          mode: 'lines+markers',
          // mode: 'markers',
          marker: {
            color: 'rgba(255, 0, 0, 0.8)',
            size: 1
          },
          line: {
            color: 'rgba(255,0,0,0.2)',  // Line color
            width: 1,       // Line width
            dash: 'solid'   // Can be 'solid', 'dash', 'dot', etc.
          },
          hoverinfo: 'x+y',
          name: 'Original'
        }
      ], 
      attenuatedSignalLayout,
      PLOTLY_CONFIG
    );
    // Reset the axis (Cant be addded to PLOTLY_LAYOUT as it changes on zoom)
    Plotly.relayout(PLOTTING_DIV,{
      'xaxis.autorange': true,  // Enable autoscaling for x-axis
      'yaxis.autorange': true   // Enable autoscaling for y-axis
    });
  
    ///////////////////
    showToast("Signal attenuated successfully");
    // Store the attenuated data
    ATTENUATED_PLOT_HOLDER['x'] = recievedData.x_new;
    ATTENUATED_PLOT_HOLDER['y'] = recievedData.y;
  } catch(e){
    console.error(e);
    showToast(e, "danger");
  } finally{
    loader.hide();
  }
}

// Generate a random number from a normal distribution 
function polarBoxMuller(mean = 0, stdDev = 1) {
  let u, v, s;
  do {
      u = 2 * Math.random() - 1; // Uniform [-1, 1]
      v = 2 * Math.random() - 1; // Uniform [-1, 1]
      s = u * u + v * v;
  } while (s >= 1 || s === 0); // Reject if s is not in (0, 1)

  const factor = Math.sqrt(-2.0 * Math.log(s) / s);
  return mean + stdDev * u * factor; // Return one normally distributed value
}

// Attenuate signal on client side
async function _attenuate(){
  let x,y,sigma;
  try{
    x = ORIGINAL_PLOT_HOLDER['x'];
    y = ORIGINAL_PLOT_HOLDER['y'];
    if (x.length==0 || y.length==0){
      console.log(x);
      console.log(y);
      throw new Error("Signal unavailable to attenuate.")
    }
  } catch(e){
    console.error(e);
    console.log("PLOTTING_DIV data ",PLOTTING_DIV.data)
    showToast("No data to attenuate", "danger");
    return;
  }
  try{
    sigma = document.getElementById("sigma").value;
    sigma = parseFloat(sigma)
    // if sigma is not a number, show an error
    if (isNaN(sigma)){
      showToast("Invalid sigma value", "danger");
    }
  } catch(e){
    console.error(e);
    console.log(sigma);
    showToast("Invalid sigma value", "danger");
  }
  loader.show();
  let attenuatedY = []
  try{
    for (let i=0; i<y.length; i++){
      attenuatedY.push(y[i] + polarBoxMuller(0, sigma));
    }
    Plotly.purge(PLOTTING_DIV)
    plot(x,y);
    Plotly.addTraces(PLOTTING_DIV,{
      x:x,
      y:attenuatedY,
      type: 'scatter', 
      mode: 'markers',
      marker: {
        color: 'red',
        size: 1
      },
      showlegend: true,
      hoverinfo: 'x+y'
    });
    showToast("Signal attenuated successfully");
  } catch(e){
    console.error(e);
    showToast(e, "danger");
  } finally{
    loader.hide();
  }
}