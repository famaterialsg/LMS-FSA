
// Gán giá trị cho các biến từ Django
var courseCode = JSON.parse(document.getElementById("course-code").textContent);
var courseNames = JSON.parse(document.getElementById("course-names").textContent);
var enrollCounts = JSON.parse(document.getElementById("enroll-data").textContent);
var passCounts = JSON.parse(document.getElementById("pass-data").textContent);

// Kiểm tra giá trị của các biến
var ctx = document.getElementById('courseChart').getContext('2d');
var courseChart = new Chart(ctx, {
type: 'bar',
data: {
    labels: courseCode,
    datasets: [
        {
            label: 'Enrolls',
            data: enrollCounts,
            backgroundColor: 'rgba(54, 162, 235, 0.7)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 1
        },
        {
            label: 'Passes',
            data: passCounts,
            backgroundColor: 'rgba(75, 192, 192, 0.7)',
            borderColor: 'rgba(75, 192, 192, 1)',
            borderWidth: 1
        }
    ]
},
    options: {
        responsive: true,
        plugins: {
            title: {
                display: true,
                text: 'Comparison of Enrollment and Pass Counts Across Courses', // Tiêu đề biểu đồ
                position: 'bottom',
                font: {
                    size: 16,
                    weight: 'bold'
                },
                padding: {
                    top: 10,
                    bottom: 20
                }
            },
            tooltip: {
                callbacks: {
                    // Tùy chỉnh nội dung tooltip
                    title: function (context) {
                        const index = context[0].dataIndex; // Lấy index của điểm được hover
                        return courseNames[index]; // Trả về tên khóa học thay vì code_course
                    }
                }
            }
        },
        scales: {
            x: {
                ticks: {
                    autoSkip: false, // Không bỏ qua nhãn nào
                    maxRotation: 90, // Góc xoay tối đa
                    minRotation: 0  // Góc xoay tối thiểu
                }
            },
            y: {
                beginAtZero: true
            }
        }
    }
});

//// Pie chart highest pass percent
var highestCourseName = JSON.parse(document.getElementById("hightestCourseName").textContent);
var passCount = JSON.parse(document.getElementById("pass-count-highest").textContent);
var InprogressCount = JSON.parse(document.getElementById("in_progress-count-highest").textContent);

// Tính toán tổng số học viên
var totalStudentHighest = passCount + InprogressCount;

// Tính tỷ lệ phần trăm cho Pass và In Progress
var passPercentage = (passCount / totalStudentHighest) * 100;
var inProgressPercentage = (InprogressCount / totalStudentHighest) * 100;

// Chart.js Pie Chart
var pie_highest = document.getElementById('passRateChart').getContext('2d');
new Chart(pie_highest, {
    type: 'pie',
    data: {
        labels: ['Pass', 'In Progress'], // Nhãn cho từng phần trong biểu đồ
        datasets: [{
            data: [passCount, InprogressCount], // Dữ liệu Pass và In Progress
            backgroundColor: ['#4caf50', '#FF8C00'], // Màu sắc cho Pass và In Progress
            hoverOffset: 4
        }]
    },
    options: {
        responsive: true,
        plugins: {
            title: {
                display: true,
                text: 'Highest Pass Rate Distribution for ' + highestCourseName, // Tiêu đề biểu đồ, chứa tên khóa học
                position: 'bottom', // Vị trí tiêu đề
                font: {
                    size: 16,
                    weight: 'bold'
                },
                padding: {
                    top: 10,
                    bottom: 20
                }
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        // Hiển thị số học viên và tỷ lệ phần trăm
                        var percentage = (context.raw / totalStudentHighest) * 100;
                        console.log(percentage)
                        console.log(context.raw)
                        console.log(totalStudentHighest)
                        return `${context.label}: ${context.raw} students (${percentage.toFixed(2)}%)`;
                    }
                }
            },
            datalabels: {
                display: true,
                color: '#fff', // Màu chữ hiển thị trên biểu đồ
                formatter: function(value, context) {
                    var percentage = (value / totalStudentHighest) * 100;
                    return `${percentage.toFixed(2)}%`; // Hiển thị tỷ lệ phần trăm
                },
                font: {
                    weight: 'bold'
                }
            }
        }
    }
});

//// Pie chart lowest pass percent
var lowestCourseName = JSON.parse(document.getElementById("lowestCourseName").textContent);
var passCount = JSON.parse(document.getElementById("pass-count_lowest").textContent);
var InprogressCount = JSON.parse(document.getElementById("in_progress-count-lowest").textContent);

// Tính toán tổng số học viên
var totalStudentsLowest = passCount + InprogressCount;

// Tính tỷ lệ phần trăm cho Pass và In Progress
var passPercentage = (passCount / totalStudentsLowest) * 100;
var inProgressPercentage = (InprogressCount / totalStudentsLowest) * 100;

// Chart.js Pie Chart
var pie_lowest = document.getElementById('passRateChart1').getContext('2d');
new Chart(pie_lowest, {
    type: 'pie',
    data: {
        labels: ['Pass', 'In Progress'], // Nhãn cho từng phần trong biểu đồ
        datasets: [{
            data: [passCount, InprogressCount], // Dữ liệu Pass và In Progress
            backgroundColor: ['#4caf50', '#FF8C00'], // Màu sắc cho Pass và In Progress
            hoverOffset: 4
        }]
    },
    options: {
        responsive: true,
        plugins: {
            title: {
                display: true,
                text: 'Lowest Pass Rate Distribution for ' + lowestCourseName, // Tiêu đề biểu đồ, chứa tên khóa học
                position: 'bottom', // Vị trí tiêu đề
                font: {
                    size: 16,
                    weight: 'bold'
                },
                padding: {
                    top: 10,
                    bottom: 20
                }
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        // Hiển thị số học viên và tỷ lệ phần trăm
                        var percentage = (context.raw / totalStudentsLowest) * 100;
                        return `${context.label}: ${context.raw} students (${percentage.toFixed(2)}%)`;
                    }
                }
            },
            datalabels: {
                display: true,
                color: '#fff', // Màu chữ hiển thị trên biểu đồ
                formatter: function(value, context) {
                    var percentage = (value / totalStudentsLowest) * 100;
                    return `${percentage.toFixed(2)}%`; // Hiển thị tỷ lệ phần trăm
                },
                font: {
                    weight: 'bold'
                }
            }
        }
    }
});

