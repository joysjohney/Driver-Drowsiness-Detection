/**
 * Chart.js Configuration for Drowsiness Timeline
 */

let drowsinessChart;
const maxDataPoints = 60; // 60 seconds of data

/**
 * Initialize the drowsiness chart
 */
function initializeChart() {
    const ctx = document.getElementById('drowsiness-chart').getContext('2d');
    
    drowsinessChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [], // will be filled by updateChartFromTimeline
            datasets: [{
                label: 'Drowsiness Score',
                data: [],
                borderColor: '#00f5a0',
                backgroundColor: 'rgba(0, 245, 160, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 6,
                pointHoverBackgroundColor: '#00f5a0',
                pointHoverBorderColor: '#fff',
                pointHoverBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 300
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: true,
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#00f5a0',
                    borderColor: '#00f5a0',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return 'Score: ' + context.parsed.y + '%';
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#718096',
                        maxTicksLimit: 10,
                        callback: function(value, index, values) {
                            // Show only every ~10 seconds
                            if (index % 10 === 0) return this.getLabelForValue(value);
                            return '';
                        }
                    }
                },
                y: {
                    display: true,
                    min: 0,
                    max: 100,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#718096',
                        font: {
                            size: 11
                        },
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        },
        plugins: [{
            // Custom plugin to draw threshold line – changed to 60
            id: 'thresholdLine',
            afterDatasetsDraw: function(chart) {
                const ctx = chart.ctx;
                const yAxis = chart.scales.y;
                const xAxis = chart.scales.x;
                const thresholdValue = 60;    // <-- changed from 70 to 60
                const y = yAxis.getPixelForValue(thresholdValue);
                
                ctx.save();
                ctx.strokeStyle = '#ff4757';
                ctx.lineWidth = 2;
                ctx.setLineDash([5, 5]);
                ctx.beginPath();
                ctx.moveTo(xAxis.left, y);
                ctx.lineTo(xAxis.right, y);
                ctx.stroke();
                
                // Draw label
                ctx.fillStyle = '#ff4757';
                ctx.font = '12px Inter';
                ctx.fillText('Alert Threshold', xAxis.right - 110, y - 5);
                ctx.restore();
            }
        }]
    });
}

/**
 * Update chart with data from the backend timeline
 * @param {Array} timelineData - Array of {age, score} objects (age in seconds, negative)
 */
function updateChartFromTimeline(timelineData) {
    if (!drowsinessChart) return;

    // Convert ages to labels (e.g., "-60s", "-50s", ...)
    const labels = timelineData.map(item => Math.round(item.age) + 's');
    const scores = timelineData.map(item => item.score);

    // Update line color based on the most recent score
    const lastScore = scores.length > 0 ? scores[scores.length - 1] : 0;
    if (lastScore >= 70) {
        drowsinessChart.data.datasets[0].borderColor = '#ff4757';
        drowsinessChart.data.datasets[0].backgroundColor = 'rgba(255, 71, 87, 0.1)';
    } else if (lastScore >= 30) {
        drowsinessChart.data.datasets[0].borderColor = '#ffd700';
        drowsinessChart.data.datasets[0].backgroundColor = 'rgba(255, 215, 0, 0.1)';
    } else {
        drowsinessChart.data.datasets[0].borderColor = '#00f5a0';
        drowsinessChart.data.datasets[0].backgroundColor = 'rgba(0, 245, 160, 0.1)';
    }

    drowsinessChart.data.labels = labels;
    drowsinessChart.data.datasets[0].data = scores;
    drowsinessChart.update('none');
}

/**
 * Reset chart to empty
 */
function resetChart() {
    if (!drowsinessChart) return;
    drowsinessChart.data.labels = [];
    drowsinessChart.data.datasets[0].data = [];
    drowsinessChart.update();
}