const ctx = document.getElementById('categoryChart');
new Chart(ctx, {
  type: 'bar',
  data: {
    labels: ['Fantasy', 'Science Fiction'],
    datasets: [{
      label: 'Books per Category',
      data: [5, 3],
      backgroundColor: ['#3498db', '#9b59b6']
    }]
  }
});
