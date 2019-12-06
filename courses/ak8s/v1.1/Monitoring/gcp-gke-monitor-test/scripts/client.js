
var JSONData = null;
var cpuLoadRunning = false;
var customMetricCreated = false;
var userCount = 0;
var debugMode = false;
// Set the CPU Load Generator document elements to objects
var btnStartCPU   = null;
var btnStopCPU    = null;
var lblCPUStatus  = null;	// Maps to the JSON CpuLoadRunning flag

// Set the Custom Metric document elements to objects
var btnStartMonitoring    = null;
var btnIncreaseUserCount  = null;
var btnDecreaseUserCount  = null;
var lblCustomMetricStatus = null;	// Maps to the JSON CustomMetricCreated flag
var lblCurrentUserCount   = null;		// Maps to the JSON UserCount value

// Set the Log Test document elements to objects
var btnEnableDebugLogging  = null;
var btnDisableDebugLogging = null;
var lblDebugLoggingStatus  = null;

// const dataFilePath = './scripts/data.json'	// Used by a commented-out function

var loaded = function() {

	console.log("Loaded");
	// --------------------------------------------------------------------------------------
	// SECTION: Initialization
	// This code sets configuration values and retrieves the server state from a JSON file.
	// --------------------------------------------------------------------------------------
	//

	// Retrieves the server-side data.json file via HTTP and parses its current values into variables.
	loadJSON(function(JSONData) {
		console.log(JSONData);
		cpuLoadRunning      = JSONData.CpuLoadRunning;
		customMetricCreated = JSONData.customMetricCreated;
		userCount           = JSONData.UserCount;
		debugMode           = JSONData.debugMode;
		SetVars();
		DataIsLoaded();

	});
	console.log(debugMode);


}

function SetVars()
{
		// Set the CPU Load Generator document elements to objects
	btnStartCPU   = document.getElementById('btnStartCPU');
	btnStopCPU    = document.getElementById('btnStopCPU');
	lblCPUStatus  = document.getElementById('lblCPUStatus');	// Maps to the JSON CpuLoadRunning flag
	
	// Set the Custom Metric document elements to objects
	btnStartMonitoring    = document.getElementById('btnStartMonitoring');
	btnIncreaseUserCount  = document.getElementById('btnIncreaseUserCount');
	btnDecreaseUserCount  = document.getElementById('btnDecreaseUserCount');
	lblCustomMetricStatus = document.getElementById('lblCustomMetricStatus');	// Maps to the JSON CustomMetricCreated flag
	lblCurrentUserCount   = document.getElementById('lblCurrentUserCount');		// Maps to the JSON UserCount value

	// Set the Log Test document elements to objects
	btnEnableDebugLogging  = document.getElementById('btnEnableDebugLogging');
	btnDisableDebugLogging = document.getElementById('btnDisableDebugLogging');
	lblDebugLoggingStatus  = document.getElementById('lblDebugLoggingStatus');	// Maps to the JSON DebugMode flag
}


function DataIsLoaded()
{
		// --------------------------------------------------------------------------------------
	// SECTION: Staging
	// This code sets the document controls and status text based on the variables set above.
	// --------------------------------------------------------------------------------------
	//
	// CPU Load Generator Section
	//
	if (cpuLoadRunning) {
		// CPU Load Generator is running, so disable the START button and set the status to "Running"
		btnStartCPU.disabled   = true;
		btnStopCPU.disabled    = false;
		lblCPUStatus.innerHTML = "STATUS: CPU Load Generator RUNNING";
	}
	else {
		// CPU isn't running yet, so disable the stop button and set the status to "Not Running"
		btnStartCPU.disabled   = false;
		btnStopCPU.disabled    = true;
		lblCPUStatus.innerHTML = "STATUS: CPU Load Generator NOT running";
	}

	//
	// Custom Metric Section
	//
	if (customMetricCreated) {
		// The Stackdriver custom metric descriptor has been created, we can now increase/decrease user count and report its status
		btnStartMonitoring.disabled     = true;
		btnIncreaseUserCount.disabled   = false;
		btnDecreaseUserCount.disabled   = false;
		lblCustomMetricStatus.innerHTML = "STATUS: Exporting custom metrics once per MINUTE";
		lblCurrentUserCount.innerHTML   = "Current User Count = " + userCount;
	}
	else {
		// The Stackdriver custom metric descriptor has NOT been created, disable the increase/decrease user count buttons and report its inactive status
		btnStartMonitoring.disabled     = false;
		btnIncreaseUserCount.disabled   = true;
		btnDecreaseUserCount.disabled   = true;
		lblCustomMetricStatus.innerHTML = "STATUS: Inactive. You must click Start Monitoring";
		lblCurrentUserCount.innerHTML   = "Current User Count = " + userCount;
	}
	
	//
	// Log Test Section
	//
	if (debugMode) {
		// The Debug Logging mode is active, disable the Enable button and report status
		btnEnableDebugLogging.disabled  = true;
		btnDisableDebugLogging.disabled = false;
		lblDebugLoggingStatus.innerHTML = "STATUS: Debug-level Logging is ENABLED";
	}
	else {
		// The Debug Logging mode is NOT active, disable the Disable button and report status
		btnEnableDebugLogging.disabled  = false;
		btnDisableDebugLogging.disabled = true;
		lblDebugLoggingStatus.innerHTML = "STATUS: Debug-level Logging is disabled";
	}	
}

function loadJSON(callback) {   
  // var xobj = new XMLHttpRequest();
  // xobj.overrideMimeType("application/json");
  // xobj.open('GET', dataFilePath, true);
  // xobj.onreadystatechange = function () {
  //   if (xobj.readyState == 4 && xobj.status == "200") {
  //     callback(JSON.parse(xobj.responseText));
  //   }
  // };
  // xobj.send(null);

  let dataCookie = getCookie('data');
  deleteCookie('data');

  if (dataCookie) {
    const data = callback(parseObjectFromCookie(dataCookie));
    // work with data. `data` is equal to `visitCard` from the server

  } else {
    // handle data not found
  }
}

const getCookie = (name) => {
  const value = "; " + document.cookie;
  const parts = value.split("; " + name + "=");
  if (parts.length === 2) return parts.pop().split(";").shift();
};

const deleteCookie = (name) => {
  document.cookie = name + '=; max-age=0;';
};

const parseObjectFromCookie = (cookie) => {
  const decodedCookie = decodeURIComponent(cookie);
  return JSON.parse(decodedCookie);
};