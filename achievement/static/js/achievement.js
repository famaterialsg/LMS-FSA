const data1 = {
    labels: labels,  // `labels` should be passed in from the template
    datasets: [{
        data: data,  // `data` should be passed in from the template
        backgroundColor: color,
        borderColor: color,
        hoverOffset: 6
    }]
};
const config1 = {
    type: 'pie',
    data: data1,
    options: {
        responsive: true,
        plugins: {
            title: {
                display: true,
                text: chart_name  // `chart_name` should be passed in from the template
            },
            legend: {
                position: 'right'
            },
            datalabels: {
                formatter: (value, context) => value > 0 ? value : '',
                color: '#fff',
                font: {
                    size: 14,
                },
            }
        }
    },
    plugins: [ChartDataLabels]
};

document.addEventListener("DOMContentLoaded", function() {
    const pieChart1 = new Chart(
        document.getElementById('myChart'),
        config1
    );
});

// JavaScript to toggle visibility of the full text
const toggleLinks = document.querySelectorAll('.toggle-text');
toggleLinks.forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        const fullText = this.previousElementSibling; // The full-text span
        const truncatedText = fullText.previousElementSibling; // The truncated span
        if (fullText.style.display === 'none') {
            fullText.style.display = 'inline'; // Show the full text
            truncatedText.style.display = 'none'; // Hide the truncated text
            this.textContent = 'Show Less'; // Change the link text
        } else {
            fullText.style.display = 'none'; // Hide the full text
            truncatedText.style.display = 'inline'; // Show the truncated text
            this.textContent = 'Show More'; // Change the link text
        }
    });
});


