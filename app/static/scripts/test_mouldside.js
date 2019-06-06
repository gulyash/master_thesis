const tcGraphLayout = {
    height: 300,
    margin: {
        r: 0,
        t: 10,
    },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    yaxis: {range: [minTemp, maxTemp]}
};
const heatmapLayout = {
    hovermode: 'closest',
    margin: {
        r: 0,
        t: 0,
        b: 30,
    },
    height: 300,
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
};

$(document).ready($ => {
    let tcGraph = document.getElementById('tc-graph');
    Plotly.newPlot(tcGraph, [], tcGraphLayout, {responsive: true, displayModeBar: false});
    let heatMapElement = document.getElementById('heatmap');
    Plotly.newPlot(heatMapElement, [], heatmapLayout, {responsive: true, displayModeBar: false});
    heatMapElement.on('plotly_click', (data) => {
        heatmapClick(data)
    });
    setInterval(updateByInterval, 200);
});

function heatmapClick(data) {
    for (let i = 0; i < data.points.length; i++) {
        if (data.points[i].data.type === "scatter") {
            let selectedTcText = data.points[i].text;
            let selectedTcNum = selectedTcText.match(/\d+/g)[0];
            $('#selected-tc').text(selectedTcNum);
            break;
        }
    }
}

function updateByInterval() {
    $.getJSON('/heatmap-data', {mold_side: heatMapInfo.moldSide}, (response) => {
        let graphTitle = heatMapInfo.graphTitle;
        if (response.error) {
            $('#graph-title').text(graphTitle + ' Error: ' + response.error)
        } else {
            $('#graph-title').text(graphTitle);
        }
        let plotData = response.data;
        heatmapUpdate(plotData);
        // enable or disable manual testing button
        manualTestingButtonUpdate(plotData);
        // switch tc graph to currently tested TC
        selectedTcUpdate(plotData);
    });
    $.getJSON('/session-info', {mold_side: heatMapInfo.moldSide}, (response) => {
        if (response.ordering.length > 0) {
            $('#ordering').text("Expected order: " + response.ordering);
        } else {
            $('#ordering').text("All thermocouples on this side are tested.");
        }
        // update modal status
        modalWindowUpdate(response);
        // update toolbar buttons order
        toolBarButtonsUpdate(response);
    });
    $.getJSON('/tc-data', {tc: $('#selected-tc').text()}, (response) => {
        tcGraphUpdate(response)
    });
}

function heatmapUpdate(plotData) {
    function getTcColors(plotData) {
        let colors = [];
        for (let i = 0; i < plotData.label.length; i++) {
            let label = plotData.label[i];
            let status = plotData.status[i];
            if (status === 'Disconnected') {
                colors.push('black')
            } else if (status === 'OK') {
                if (plotData.test.current === label) {
                    colors.push('yellow')
                } else if (plotData.test.successful.includes(label)) {
                    colors.push('lightgreen')
                } else if (plotData.test.failed.includes(label)) {
                    colors.push('red')
                } else {
                    colors.push('white')
                }
            }
        }
        return colors
    }

    function getTextLabels(plotData) {
        let text_labels = [];
        for (let i = 0; i < plotData.label.length; i++) {
            let label = plotData.label[i];
            let temperature = plotData.temperature[i];
            if (temperature) {
                let temperatureString = '';
                if (Number.isInteger(temperature)) {
                    temperatureString = temperature + '.0'
                } else {
                    temperatureString = temperature.toString()
                }
                text_labels.push('TC ' + label + '<br>' + temperatureString)
            } else {
                text_labels.push('TC ' + label)
            }
        }
        return text_labels
    }

    let heatmap = {
        x: plotData.x,
        y: plotData.y,
        z: plotData.temperature,
        type: 'heatmap',
        hoverinfo: 'none',
        zsmooth: 'best',
        zauto: false,
        zmin: minTemp,
        zmax: maxTemp,
    };

    let mold_side_scatter = {
        x: plotData.x,
        y: plotData.y,
        mode: 'markers+text',
        text: getTextLabels(plotData),
        textposition: 'bottom center',
        marker: {
            symbol: 'circle',
            opacity: 0.9,
            color: getTcColors(plotData),
            size: 16,
            line: {
                width: 1
            },
        },
        hoverinfo: 'x+y+text',
        textfont: {color: '#e8e5e9'},
        type: 'scatter',
    };
    // heat map first, then a scatter plot on top of it
    let data = [
        heatmap,
        mold_side_scatter,
    ];
    Plotly.react('heatmap', data, heatmapLayout);
}

function manualTestingButtonUpdate(plotData) {
    if (Object.keys(plotData).length === 0) {
        $('#btn-test').prop('disabled', true);
    } else {
        let selectedTc = parseInt($('#selected-tc').text());
        // search plotData for selected thermocouple
        for (let i = 0; i < plotData.label.length; i++) {
            let tcLabel = plotData.label[i];
            if (tcLabel === selectedTc) {
                if (plotData.status[i] === 'Disconnected' ||
                    plotData.test.current === tcLabel ||
                    plotData.test.successful.includes(tcLabel) ||
                    plotData.test.failed.includes(tcLabel)
                ) {
                    $('#btn-test').prop('disabled', true);
                } else {
                    $('#btn-test').prop('disabled', false);
                }
                break;
            }
        }
    }
}

function modalWindowUpdate(response) {
    let modal = $('#testResultModal');
    let test = response.completed;
    if (test) {
        let ordering = response.ordering;
        if (test.label === ordering[0]) {
            modal.find('.modal-title').text('Test result: ' + test.result + '!');
            let html_str = test.text_label + '<br/>X: ' + test.x + '<br/>Y: ' + test.y;
            $('#modal-text').html(html_str);
        } else {
            modal.find('.modal-title').text('Possible wiring issue:');
            let html_str = test.text_label + ' (X: ' + test.x + ', Y: ' + test.y + ')<br>was heated instead of TC ' + ordering[0] + '.';
            $('#modal-text').html(html_str);
        }
        modal.modal('show');
    } else {
        modal.modal('hide');
    }
}

function toolBarButtonsUpdate(response) {
    $('.test-button').removeClass('test-button-left  test-button-active test-button-right');
    if (response.current_mode === 'horizontal_first') {
        $('#horz').addClass('test-button-active');
        $('#vert').addClass('test-button-right');
        $('#btn-test').addClass('test-button-left');
    } else if (response.current_mode === 'vertical_first') {
        $('#vert').addClass('test-button-active');
        $('#horz').addClass('test-button-right');
        $('#btn-test').addClass('test-button-left');
    } else if (response.current_mode === 'manual') {
        $('#horz').addClass('test-button-left');
        $('#vert').addClass('test-button-right');
        $('#btn-test').addClass('test-button-active');
    }
}

function selectedTcUpdate(plotData) {
    if (plotData.test.current) {
        $('#selected-tc').text(plotData.test.current)
    }
}

function tcGraphUpdate(response) {
    let scatter = {
        x: response.time,
        y: response.temperature,
        name: response.name,
        mode: 'lines',
    };
    Plotly.react('tc-graph', [scatter], tcGraphLayout);
}

// modal options
$("#btn-fail").click(function () {
    let data = JSON.stringify({
        result: 'fail',
    });
    $.post("/autotest-confirmation", data);
});
$("#btn-ok").click(function () {
    let data = JSON.stringify({
        result: 'success',
    });
    $.post("/autotest-confirmation", data);
});

// manual test
$("#btn-test").click(function () {
    $.post("/mantest", {tc: $('#selected-tc').text()}, function (data) {
        console.log(data);
        $("#btn-test").trigger("blur");
        this.blur();
    });
});
// switching test direction
$(".test-direction-button").click(function () {
    $.post("/test-direction", {direction: this.id});
    this.blur();
});