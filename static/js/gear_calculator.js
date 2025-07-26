document.addEventListener('DOMContentLoaded', function() {
    // Check if we have calculation data
    const gearCalculationData = {
        gearRatios: {{ calculation.gear_ratios|safe|default:"{}" }},
        finalDrive: {{ calculation.final_drive|default:"0" }},
        maxRPM: {{ calculation.max_rpm|default:"8000" }},
        minRPM: {{ calculation.min_rpm|default:"1000" }},
        tireDiameter: {{ calculation.tire_diameter_inches|default:"26.0" }}
    };
    
    // Only try to render if we have valid data
    if (gearCalculationData.finalDrive > 0 && Object.keys(gearCalculationData.gearRatios).length > 0) {
        renderGearGraph(gearCalculationData);
    }
});

function renderGearGraph(data) {
    try {
        const container = document.getElementById('gearGraph');
        if (!container) return;
        
        const width = container.clientWidth || 800;
        const height = container.clientHeight || 300;
        
        // Create SVG element
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', '100%');
        svg.setAttribute('height', '100%');
        svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
        
        // Add axes
        const xAxis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        xAxis.setAttribute('x1', '50');
        xAxis.setAttribute('y1', height - 30);
        xAxis.setAttribute('x2', width - 30);
        xAxis.setAttribute('y2', height - 30);
        xAxis.setAttribute('stroke', 'rgba(255, 255, 255, 0.2)');
        svg.appendChild(xAxis);
        
        const yAxis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        yAxis.setAttribute('x1', '50');
        yAxis.setAttribute('y1', '30');
        yAxis.setAttribute('x2', '50');
        yAxis.setAttribute('y2', height - 30);
        yAxis.setAttribute('stroke', 'rgba(255, 255, 255, 0.2)');
        svg.appendChild(yAxis);
        
        // Add axis labels
        const xLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        xLabel.setAttribute('x', width / 2);
        xLabel.setAttribute('y', height - 5);
        xLabel.setAttribute('text-anchor', 'middle');
        xLabel.setAttribute('fill', 'rgba(255, 255, 255, 0.7)');
        xLabel.textContent = 'Speed (mph)';
        svg.appendChild(xLabel);
        
        const yLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        yLabel.setAttribute('x', 15);
        yLabel.setAttribute('y', height / 2);
        yLabel.setAttribute('text-anchor', 'middle');
        yLabel.setAttribute('fill', 'rgba(255, 255, 255, 0.7)');
        yLabel.setAttribute('transform', `rotate(-90, 15, ${height/2})`);
        yLabel.textContent = 'RPM';
        svg.appendChild(yLabel);
        
        // Constants for calculations
        const maxSpeed = 300; // mph
        
        // Function to convert speed and RPM to x,y coordinates
        function toCoords(speed, rpm) {
            const x = 50 + ((width - 80) * speed / maxSpeed);
            const y = (height - 30) - ((height - 60) * (rpm - data.minRPM) / (data.maxRPM - data.minRPM));
            return { x, y };
        }
        
        // Draw gear lines
        const gear_keys = Object.keys(data.gearRatios);
        const colors = ['#FF3333', '#FFFF33', '#33FF33', '#33FFFF', '#3333FF', '#FF33FF'];
        
        gear_keys.forEach((gear, index) => {
            const ratio = data.gearRatios[gear];
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            
            // Calculate the gear line
            let pathData = '';
            
            for (let rpm = data.minRPM; rpm <= data.maxRPM; rpm += 100) {
                // Calculate speed at this RPM and gear
                const speed = (rpm * Math.PI * data.tireDiameter) / (ratio * data.finalDrive * 1056);
                
                const point = toCoords(speed, rpm);
                
                if (pathData === '') {
                    pathData = `M${point.x},${point.y}`;
                } else {
                    pathData += ` L${point.x},${point.y}`;
                }
            }
            
            path.setAttribute('d', pathData);
            path.setAttribute('stroke', colors[index % colors.length]);
            path.setAttribute('stroke-width', '2');
            path.setAttribute('fill', 'none');
            svg.appendChild(path);
            
            // Add gear label at the top of the line
            const endPoint = toCoords((data.maxRPM * Math.PI * data.tireDiameter) / (ratio * data.finalDrive * 1056), data.maxRPM);
            
            const gearLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            gearLabel.setAttribute('x', endPoint.x);
            gearLabel.setAttribute('y', endPoint.y - 10);
            gearLabel.setAttribute('text-anchor', 'middle');
            gearLabel.setAttribute('fill', colors[index % colors.length]);
            gearLabel.textContent = gear;
            svg.appendChild(gearLabel);
        });
        
        // Add tickmarks for RPM
        for (let rpm = data.minRPM; rpm <= data.maxRPM; rpm += 1000) {
            const y = (height - 30) - ((height - 60) * (rpm - data.minRPM) / (data.maxRPM - data.minRPM));
            
            const tick = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            tick.setAttribute('x1', '45');
            tick.setAttribute('y1', y);
            tick.setAttribute('x2', '50');
            tick.setAttribute('y2', y);
            tick.setAttribute('stroke', 'rgba(255, 255, 255, 0.5)');
            svg.appendChild(tick);
            
            const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            label.setAttribute('x', '40');
            label.setAttribute('y', y + 5);
            label.setAttribute('text-anchor', 'end');
            label.setAttribute('fill', 'rgba(255, 255, 255, 0.7)');
            label.setAttribute('font-size', '10');
            label.textContent = rpm.toString();
            svg.appendChild(label);
        }
        
        // Add tickmarks for speed
        for (let speed = 0; speed <= maxSpeed; speed += 50) {
            const x = 50 + ((width - 80) * speed / maxSpeed);
            
            const tick = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            tick.setAttribute('x1', x);
            tick.setAttribute('y1', height - 30);
            tick.setAttribute('x2', x);
            tick.setAttribute('y2', height - 25);
            tick.setAttribute('stroke', 'rgba(255, 255, 255, 0.5)');
            svg.appendChild(tick);
            
            const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            label.setAttribute('x', x);
            label.setAttribute('y', height - 15);
            label.setAttribute('text-anchor', 'middle');
            label.setAttribute('fill', 'rgba(255, 255, 255, 0.7)');
            label.setAttribute('font-size', '10');
            label.textContent = speed.toString();
            svg.appendChild(label);
        }
        
        // Clear any fallback message
        container.innerHTML = '';
        
        // Append to container
        container.appendChild(svg);
        console.log('Gear graph rendered successfully');
    } catch (error) {
        console.error("Error rendering gear graph:", error);
        const container = document.getElementById('gearGraph');
        if (container) {
            container.innerHTML = `<div class="alert alert-danger">Error rendering graph: ${error.message}</div>`;
        }
    }
}