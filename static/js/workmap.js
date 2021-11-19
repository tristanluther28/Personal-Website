
    var margin = {top: 0, left: 0, right: 0, bottom: 0},
    height = 400 - margin.top - margin.bottom,
    width = 800 - margin.left - margin.right;

    var svg = d3.select("#map")
        .append("svg")
        .attr("height", height + margin.top + margin.bottom)
        .attr("width", width + margin.left + margin.right)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var promise = [];
    promise.push("us_states.topojson")

    var projection = d3.geoMercator()
        .translate([ width / 2, height / 2])
        .scale(100);

    var path = d3.geoPath()
        .projection(projection);

    Promise.all(promise).then(function(data){
        console.log(data);
        var states = topojson.feature(data, data.objects.states).features;
        console.log(states);
    });