// static/js/torque-power-curves.js

function renderTorqueCurve() {
    try {
        const torqueCurveData = window.torqueCurveData;
        if (!torqueCurveData || !Array.isArray(torqueCurveData) || torqueCurveData.length === 0) {
            console.log("No torque curve data available");
            return;
        }
        
        const container = document.getElementById('powerCurveGraph');
        if (!container) {
            console.error("Power curve container not found");
            return;
        }
        
        // Hide the fallback message
        const fallback = document.getElementById('powerGraphFallback');
        if (fallback) {
            fallback.style.display = 'none';
        }
        
        const width = container.clientWidth || 800;
        const height = container.clientHeight || 400;
        
        // Create SVG element
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', '100%');
        svg.setAttribute('height', '100%');
        svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
        
        // Add axes
        const margin = { top: 20, right: 30, bottom: 40, left: 50 };
        const innerWidth = width - margin.left - margin.right;
        const innerHeight = height - margin.top - margin.bottom;
        
        // Get min/max values for axes
        const rpmValues = torqueCurveData.map(d => d[0]);
        const torqueValues = torqueCurveData.map(d => d[1]);
        const minRPM = Math.min(...rpmValues);
        const maxRPM = Math.max(...rpmValues);
        const maxTorque = Math.max(...torqueValues);
        
        // Create scales
        const xScale = (rpm) => margin.left + (rpm - minRPM) / (maxRPM - minRPM) * innerWidth;
        const yScale = (torque) => margin.top + innerHeight - (torque / maxTorque) * innerHeight;
        
        // Draw axes
        const xAxis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        xAxis.setAttribute('x1', margin.left);
        xAxis.setAttribute('y1', margin.top + innerHeight);
        xAxis.setAttribute('x2', margin.left + innerWidth);
        xAxis.setAttribute('y2', margin.top + innerHeight);
        xAxis.setAttribute('stroke', 'rgba(255, 255, 255, 0.5)');
        xAxis.setAttribute('stroke-width', '1');
        svg.appendChild(xAxis);
        
        const yAxis = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        yAxis.setAttribute('x1', margin.left);
        yAxis.setAttribute('y1', margin.top);
        yAxis.setAttribute('x2', margin.left);
        yAxis.setAttribute('y2', margin.top + innerHeight);
        yAxis.setAttribute('stroke', 'rgba(255, 255, 255, 0.5)');
        yAxis.setAttribute('stroke-width', '1');
        svg.appendChild(yAxis);
        
        // Draw torque curve
        let path = `M${xScale(torqueCurveData[0][0])},${yScale(torqueCurveData[0][1])}`;
        for (let i = 1; i < torqueCurveData.length; i++) {
            path += ` L${xScale(torqueCurveData[i][0])},${yScale(torqueCurveData[i][1])}`;
        }
        
        const torquePath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        torquePath.setAttribute('d', path);
        torquePath.setAttribute('stroke', '#ff3333');
        torquePath.setAttribute('stroke-width', '2');
        torquePath.setAttribute('fill', 'none');
        svg.appendChild(torquePath);
        
        // Add labels and ticks for axes
        // RPM axis ticks
        for (let rpm = minRPM; rpm <= maxRPM; rpm += 1000) {
            // Tick mark
            const tick = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            tick.setAttribute('x1', xScale(rpm));
            tick.setAttribute('y1', margin.top + innerHeight);
            tick.setAttribute('x2', xScale(rpm));
            tick.setAttribute('y2', margin.top + innerHeight + 5);
            tick.setAttribute('stroke', 'rgba(255, 255, 255, 0.5)');
            svg.appendChild(tick);
            
            // Label
            const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            label.setAttribute('x', xScale(rpm));
            label.setAttribute('y', margin.top + innerHeight + 20);
            label.setAttribute('text-anchor', 'middle');
            label.setAttribute('fill', 'rgba(255, 255, 255, 0.7)');
            label.textContent = rpm;
            svg.appendChild(label);
        }
        
        // Add axis labels
        const xLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        xLabel.setAttribute('x', margin.left + innerWidth / 2);
        xLabel.setAttribute('y', height - 5);
        xLabel.setAttribute('text-anchor', 'middle');
        xLabel.setAttribute('fill', 'rgba(255, 255, 255, 0.8)');
        xLabel.textContent = 'RPM';
        svg.appendChild(xLabel);
        
        const yLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        yLabel.setAttribute('x', 15);
        yLabel.setAttribute('y', margin.top + innerHeight / 2);
        yLabel.setAttribute('text-anchor', 'middle');
        yLabel.setAttribute('fill', 'rgba(255, 255, 255, 0.8)');
        yLabel.setAttribute('transform', `rotate(-90, 15, ${margin.top + innerHeight / 2})`);
        yLabel.textContent = 'Torque';
        svg.appendChild(yLabel);
        
        // Append to container
        container.innerHTML = '';
        container.appendChild(svg);
        console.log('Torque curve rendered successfully');
    } catch (error) {
        console.error("Error rendering torque curve:", error);
        const container = document.getElementById('powerCurveGraph');
        if (container) {
            container.innerHTML = `<div class="alert alert-danger">Error rendering torque curve: ${error.message}</div>`;
        }
    }
}