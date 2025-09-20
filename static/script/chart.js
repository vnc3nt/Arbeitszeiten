const viewoption = {
    "week": 1,
    "month": 4.5,
    "year": 55
}

const COLUMN_PER_VALUE = 3
//TODO left/right arrows for scrolling left and right on desktop like pictures on amazon product
google.charts.load('current', { 'packages': ['corechart'] });
google.charts.setOnLoadCallback(drawChart);


window.onload = function(e) {
    document.querySelectorAll("input[name='view-options']").forEach(radiobutton => {
        radiobutton.addEventListener("change", e => drawChart());
    });
};


function generateTooltip(date, category, value) {
    let name = category.name
    let unit = category.unit;
    let color = category.color;

    return `<div class="tooltipName">${name}</div> <div class="tooltipDate">${date}</div> <div class="tooltipData"><div class="tooltipValue">${value}</div>${unit}</div>`

}

async function drawChart() {
    try {
        let userData = await fetch('/api/data')
            .then(response => response.json())
            .catch((error) => {
                console.error('Error:', error);
            });
        let databaseData = [['Datum']];
        let firstDate = undefined;
        let currentDate = stringToDate(userData.data[0].date);
        let categoryStyles = {}; // Objekt zur Speicherung von Farben und Stilen je nach Kategorie

        // Sammeln aller Kategorien und deren Farben
        let response = await fetch('/api/categories');
        let categories = await response.json();
        categories.sort((a, b) => a.id - b.id); // Sortieren der Kategorien nach ID


        categories.forEach(category => {
            databaseData[0].push(category.name, { type: 'string', role: 'style' }, { type: 'string', role: 'tooltip', 'p': { html: true } }); // Hinzufügen der Kategorienamen als Überschriften
            categoryStyles[category.name] = { color: category.color }; // Speichern der Farben für jede Kategorie
        });




        // Datenpunkte zu den entsprechenden Datumseinträgen hinzufügen
        let dataByDate = {}; // Objekt zur Sammlung der Daten pro Datum
        userData.data.forEach(element => {

            let date = element.date;
            if (!dataByDate[date]) {
                dataByDate[date] = [date]; // Erste Spalte im Datenarray ist das Datum
                categories.forEach(category => {
                    dataByDate[date].push(
                        0,
                        'point { fill-color: #ffffff; stroke-color: #000000; stroke-width: 1 }',
                        "hoho"
                    ); // Initialisieren aller Kategorienwerte mit 0
                });
            }

            // Werte für jede Kategorie zum entsprechenden Datum hinzufügen
            categories.forEach(category => {
                dataByDate[date][COLUMN_PER_VALUE * categories.indexOf(category) + 1] += element[category.name] ?? 0;
            });
        });
        // Datenzeilen aus dem dataByDate Objekt in das databaseData Array einfügen
        Object.values(dataByDate).forEach(row => {
            databaseData.push(row);
        });


        // Finden des ersten gültigen Datums in den Daten
        firstDate = databaseData[1][0];

        console.log(databaseData);
        console.log(dataByDate);
        // let nextDay = databaseData[1]?.slice(0, 1)[0] ?? firstDate;
        let nextDay = undefined;
        for (let i = 1; i < databaseData.length; i++) {
            let row = databaseData[i];
            nextDay = nextDay ?? row[0];
            console.log(row[0] !== nextDay && daysTillToday(nextDay) > 0);
            while (row[0] !== nextDay && daysTillToday(nextDay) > 0) {
                let t = [nextDay]
                
                for (let j = 0; j < row.length - 1; j += COLUMN_PER_VALUE) {
                    t.push(0, "point { fill-color: " + lightenColor(categories[j / COLUMN_PER_VALUE].color, +40) + "; }", "abcd")  // interpoliert
                }
                databaseData.splice(i, 0, t);
                i++;
                nextDay = dateToString(addDays(stringToDate(nextDay), 1));
            }

            // individual dot color in chart
            for (let j = 0; j < row.length - 1; j += COLUMN_PER_VALUE) {
                if (row[j + 1] === 0) {
                    row[j + 2] = "point { fill-color: " + lightenColor(categories[j / COLUMN_PER_VALUE].color, +40) + "; }";
                }
            }
            nextDay = dateToString(addDays(stringToDate(nextDay), 1));
        }
        console.table(databaseData);
        // Aufruf der Funktion, um Nullen mit interpolierten Werten zu ersetzen
        ersetzeNullenMitInterpoliertenWerten(databaseData);

        // Create tooltips
        for (let i = 1; i < databaseData.length; i++) {
            let row = databaseData[i];
            for (let j = 0; j < row.length - 1; j += COLUMN_PER_VALUE) {
                row[j + 3] = generateTooltip(row[0], categories[j / COLUMN_PER_VALUE], row[j + 1]);
            }
        }

        let data = google.visualization.arrayToDataTable(databaseData);

        // Höchsten Wert für die Y-Achse berechnen
        let maxValue = Math.max(...Object.values(userData.maxValue));
        document.querySelector(".max").textContent = Math.round((maxValue + 5) / 5) * 5;
        let selectedValue = document.querySelector("input[type=radio][name='view-options']:checked").value;


        let options = {
            curveType: 'function',
            legend: 'none',
            width: Math.max(window.innerWidth / 7 * daysTillToday(firstDate) / viewoption[selectedValue], window.innerWidth * 0.95),
            height: window.innerHeight - convertRemToPixels(16),
            colors: categories.map(style => style.color),
            lineWidth: 3,
            pointSize: 5 / viewoption[selectedValue],
            backgroundColor: { fill: 'transparent' },
            chartArea: { 'width': '99%', 'height': '90%' },
            hAxis: { viewWindow: { min: .25, max: daysTillToday(firstDate) - 0.25 } },
            vAxis: { viewWindow: { min: 0, max: maxValue + 10 } },
            tooltip: { isHtml: true } /*, trigger: "selection" entfernt da so besser auf mobile*/
        };

        let chart = new google.visualization.LineChart(document.getElementById('curve_chart'));

        chart.draw(data, options);

        let container = document.querySelector('.scrollwindow');
        container.scrollLeft = options.width + 500;
    } catch (error) {
        console.error('Fehler beim Zeichnen des Charts:', error);
        showAddFirstInfoModal();
    }
}

function convertRemToPixels(rem) {
    return rem * parseFloat(getComputedStyle(document.documentElement).fontSize);
}

function dateToString(date) {
    let tag = String(date.getDate()).padStart(2, '0');
    let monat = String(date.getMonth() + 1).padStart(2, '0'); // Monate von 0-11
    let jahr = date.getFullYear();
    return `${tag}-${monat}-${jahr}`;
}

function stringToDate(datumString) {
    let teile = datumString.split("-");
    return new Date(teile[2], teile[1] - 1, teile[0]);
}

function addDays(date, days) {
    var result = new Date(date);
    result.setDate(result.getDate() + days);
    return result;
}

function ersetzeNullenMitInterpoliertenWerten(databaseData) {
    console.log("db", databaseData);
    let columnCount = databaseData[0].length; // Anzahl der Spalten dynamisch festlegen
    let categoryCount = (columnCount - 1) / COLUMN_PER_VALUE;

    // remove end of graph (no interpolation) by setting them to NaN
    let foundCategories = new Array(categoryCount).fill(0);
    for (let i = databaseData.length - 1; i >= 1; i--) {
        let row = databaseData[i];
        for (let j = 0; j < categoryCount; j++) {
            if (foundCategories[j] === 1) continue;

            let categoryIndex = COLUMN_PER_VALUE * j + 1;
            if (row[categoryIndex] !== 0) {
                foundCategories[j] = 1;
            }
            else {
                row[categoryIndex] = NaN;
            }

        }

        if (foundCategories.reduce((a, b) => a + b) === categoryCount) {
            break;
        }
    }


    // interpolierte werte
    let previousValues = new Array(columnCount).fill(0);
    let futureValues = new Array(columnCount).fill(0);
    let nullStreckenStart = new Array(columnCount).fill(0);

    for (let i = 1; i < databaseData.length; i++) {
        for (let j = 1; j < columnCount; j++) {
            if (databaseData[i][j] === 0) {
                if (nullStreckenStart[j] === 0) {
                    previousValues[j] = Number(databaseData[i - 1][j]);
                    nullStreckenStart[j] = i;
                }
            } else {
                if (nullStreckenStart[j] > 0) {
                    futureValues[j] = Number(databaseData[i][j]);
                    let schrittweite = (futureValues[j] - previousValues[j]) / (i - nullStreckenStart[j] + 1);
                    for (let k = nullStreckenStart[j]; k < i; k++) {
                        databaseData[k][j] = Number((previousValues[j] + schrittweite * (k - nullStreckenStart[j] + 1)).toFixed(2));
                    }
                    nullStreckenStart[j] = 0;
                }
                previousValues[j] = Number(databaseData[i][j]);
            }
        }
    }

    // Behandlung für den Fall, dass das Array mit Nullen endet
    for (let j = 1; j < columnCount; j++) {
        if (nullStreckenStart[j] > 0) {
            for (let k = nullStreckenStart[j]; k < databaseData.length; k++) {
                databaseData[k][j] = Number(previousValues[j].toFixed(2)); // Verwenden Sie den letzten Nicht-Null-Wert
            }
        }
    }
}

function daysTillToday(datumString) {
    if (typeof datumString === 'string') {
        let teile = datumString.split("-");
        let gegebenesDatum = new Date(teile[2], teile[1] - 1, teile[0]);
        let heute = new Date();
        let differenzInZeit = heute.getTime() - gegebenesDatum.getTime();
        let differenzInTagen = Math.floor(differenzInZeit / (1000 * 3600 * 24));
        return differenzInTagen + 1;
    } else {
        // Behandlung für den Fall, dass datumString kein String ist
        console.error('datumString ist kein String:', datumString);
        return 0;
    }
}


function filterData(databaseData, interval) {
    let filteredData = [databaseData[0]]; // Behalten Sie die Überschriften bei
    for (let i = databaseData.length - 1; i > 0; i -= interval) {
        filteredData.unshift(databaseData[i]);
    }
    return filteredData;
}



function showAddFirstInfoModal() {
    console.debug("showwinnng");
    console.log('showAddFirstInfoModal was called');
    document.getElementById('addFirstInfoModal').style.display = 'block';
}

function hideAddFirstInfoModal() {
    console.debug('hideAddFirstInfoModal was called');
    const modal = document.getElementById('addFirstInfoModal');
    if (modal) {
        console.log('Modal found, hiding it');
        modal.style.display = 'none';
    } else {
        console.log('Modal not found');
    }
}
