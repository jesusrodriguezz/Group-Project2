// Function to update the graph using Plotly.js
function updateGraph() {
    fetch('/get_portfolio_value')
        .then(response => response.json())
        .then(data => {
            console.log(data.x);
            console.log(data.y);

            console.log('Received data:', data);
            var processedDates = data.x.map(date => date.slice(0, -4)); // Remove the last 4 characters (" GMT")
            var graphData = [{
                x: processedDates,
                y: data.y,
                type: 'line',
                marker: { color: 'blue' },
                line: { shape: 'spline' }
            }];

            var layout = {
                title: 'Investment Portfolio Performance -- Current Value: ' + data.y[data.y.length - 1],
                xaxis: {
                    title: 'Time (EST)',
                    tickangle: -45,
                    tickformat: '%H:%M:%S',
                },
                yaxis: {
                    title: 'Portfolio Value ($ USD)'
                }
            };

            console.log('Graph data:', graphData);
            console.log('Layout:', layout);

            Plotly.newPlot('graph-container', graphData, layout);
        });
}

// Call the updateGraph function initially
updateGraph();

// Call the updateGraph function periodically
setInterval(updateGraph, 1000); // Update every second
